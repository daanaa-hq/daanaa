#!/usr/bin/env python3
"""
LLM-powered structured extraction, local Qwen3-30B (port 11437) only.

Two extraction domains sharing one HTTP-calling core (_call_llm):
- Scraped org website content: financial figures, founded date/service
  area/leadership (original scope).
- 990 narrative enrichment (added 2026-08-16, Phase 4 of
  docs/990-enrichment/): mission_summary, services, populations_served,
  geographies, reported_outcomes, new_or_changed_programs, other_useful_facts
  -- derived ONLY from the bounded deterministic excerpts
  scripts/ops/fetch_irs_direct_filing.py's parse_990_xml() already extracts
  (mission text, Schedule O, structured programs, grant purposes), never
  from a whole filing.

Why LLM over regex for website content: org websites are wildly inconsistent
in formatting. A financial figure might be in a table, a paragraph, an
infographic caption, or a PDF link. Regex requires enumerating every
pattern; the local model generalizes. The 990 narrative case is different --
deterministic extraction gets the RAW text (already done, see above); the
model's job there is compressing/summarizing bounded, already-sourced text
into donor-readable form and pulling out structured facts, with grounding
enforced by prompt instruction ("use only supplied text, omit rather than
guess") plus post-hoc human spot-check, not by re-verifying facts against
outside knowledge.

Structured output enforced via JSON schema (response_format) — matches the
project's existing mission-generation approach (see generate_missions.py),
which fixed the same "verbose output won't parse" failure mode documented
in TODOS.md 2026-07-10.
"""

import json
import logging
import requests

logger = logging.getLogger(__name__)

LLM_ENDPOINT = "http://localhost:11437/v1/chat/completions"
MODEL = "qwen3-30b-a3b-instruct"

FINANCIAL_EXTRACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "financial_extraction",
        "schema": {
            "type": "object",
            "properties": {
                "found_financial_data": {"type": "boolean"},
                "fiscal_year": {"type": ["integer", "null"]},
                "revenue": {"type": ["number", "null"]},
                "expenses": {"type": ["number", "null"]},
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                "source_context": {"type": "string", "description": "Brief quote of where this was found"},
            },
            "required": ["found_financial_data", "confidence"],
        },
    },
}

METADATA_EXTRACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "metadata_extraction",
        "schema": {
            "type": "object",
            "properties": {
                "founded_year": {"type": ["integer", "null"]},
                "service_area_states": {"type": "array", "items": {"type": "string"}},
                "executive_name": {"type": ["string", "null"]},
                "mission_summary": {"type": ["string", "null"], "description": "1-2 sentence mission if found"},
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            },
            "required": ["confidence"],
        },
    },
}


def _call_llm(system_prompt, user_content, schema, timeout=30, max_input_chars=8000, max_tokens=500):
    """Fail-closed: any parse or request error returns None, never raises
    into the caller's batch loop (lesson #3 — but here None IS the explicit
    'could not extract' signal, logged by the caller, not swallowed).
    max_input_chars/max_tokens are overridable (defaults match the original
    website-extraction tuning) -- 990 narrative input can be larger (a
    single Schedule O explanation ran ~5,700 chars in the Phase 1 sample)
    and its multi-array output schema needs more room than a handful of
    scalar fields."""
    try:
        resp = requests.post(
            LLM_ENDPOINT,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content[:max_input_chars]},
                ],
                "response_format": schema,
                "temperature": 0.1,  # deterministic extraction, not creative
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except requests.exceptions.RequestException as e:
        logger.warning(f"LLM extraction request failed: {e}")
        return None
    except (KeyError, IndexError, TypeError, ValueError) as e:
        # Codex Review D (2026-08-16): the original except clause only caught
        # KeyError/JSONDecodeError. resp.json() can raise ValueError on a
        # non-JSON body; an empty/absent "choices" list raises IndexError;
        # a malformed response shape (e.g. "choices": null) can raise
        # TypeError. json.JSONDecodeError is a ValueError subclass, so this
        # widened tuple still covers the original case.
        logger.warning(f"LLM extraction response malformed: {e}")
        return None


def extract_financial_data(page_text, ein, source_url):
    """Extract revenue/expenses from a scraped page's text content."""
    system_prompt = (
        "You extract financial figures from nonprofit organization webpage text. "
        "Only report figures you actually find stated in the text — never estimate "
        "or infer. If no clear organization-wide revenue/expense figure is present, "
        "set found_financial_data to false. Distinguish organization-wide totals from "
        "single-program budgets; only report the former."
    )
    result = _call_llm(system_prompt, page_text, FINANCIAL_EXTRACTION_SCHEMA)
    if result is None:
        logger.warning(f"Financial extraction failed for {ein} ({source_url})")
        return None
    if result.get("found_financial_data"):
        logger.info(f"Financial data found for {ein}: revenue={result.get('revenue')}, "
                     f"confidence={result.get('confidence')}")
    return result


def extract_metadata(page_text, ein, source_url):
    """Extract founding date, service area, leadership from an About page."""
    system_prompt = (
        "You extract organizational metadata from nonprofit 'About' page text. "
        "Only report facts explicitly stated in the text. Service area states "
        "should be USPS two-letter codes. If information isn't present, leave "
        "the field null or empty."
    )
    result = _call_llm(system_prompt, page_text, METADATA_EXTRACTION_SCHEMA)
    if result is None:
        logger.warning(f"Metadata extraction failed for {ein} ({source_url})")
        return None
    return result


# ── 990 narrative enrichment (Phase 4, docs/990-enrichment/) ────────────────
# Input is always the bounded, already-deterministically-extracted excerpt
# bundle from scripts/ops/fetch_irs_direct_filing.py's parse_990_xml() --
# mission text + Schedule O explanations + structured program descriptions +
# grant purposes -- never a whole filing. reported_outcomes is explicitly
# organization-reported, never independently verified (Stewardship P3/P5/P10:
# label AI summarization honestly, never as verification).

NARRATIVE_ENRICHMENT_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "narrative_990_enrichment",
        "schema": {
            "type": "object",
            "properties": {
                "mission_summary": {
                    "type": ["string", "null"],
                    "description": "1-2 sentence donor-readable summary of what this org does, in plain language. Must be grounded in the supplied text only.",
                },
                "services": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Concrete services/activities the org provides, as short phrases (e.g. 'job placement', 'transitional housing').",
                },
                "populations_served": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Who the org serves, only if explicitly stated (e.g. 'veterans', 'youth ages 8-18'). Do not infer from the org's name alone.",
                },
                "geographies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Places the org explicitly says it serves, only if stated in the text. Do not infer from the org's mailing address.",
                },
                "reported_outcomes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim": {"type": "string"},
                            "value": {"type": ["string", "null"]},
                            "evidence_quote": {
                                "type": "string",
                                "description": "The exact sentence or phrase from the supplied text this claim comes from, copied verbatim (not paraphrased). Required so this specific claim can be mechanically checked against the source.",
                            },
                        },
                        "required": ["claim", "evidence_quote"],
                    },
                    "description": "Organization-reported accomplishments/results with a quantity, if any (e.g. claim='meals served', value='12,000'). Never independently verified -- report only what the org itself states. Every item's evidence_quote is checked against the source text before storage; unmatched items are dropped, not stored unverified.",
                },
                "new_or_changed_programs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Programs explicitly described as new, expanded, or discontinued this year.",
                },
                "other_useful_facts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Other short, concrete, donor-relevant facts from the text that don't fit the above categories. Omit vague or promotional language.",
                },
                "grounded": {
                    "type": "boolean",
                    "description": "true if every field above is directly supported by the supplied text; false if you had to leave most fields empty because the text didn't contain enough narrative content. This is a self-assessment, not independent verification -- treat it as a diagnostic signal for reviewing thin-input cases, never as a publication gate or confidence score.",
                },
            },
            "required": [
                "mission_summary", "services", "populations_served", "geographies",
                "reported_outcomes", "new_or_changed_programs", "other_useful_facts",
                "grounded",
            ],
        },
    },
}

NARRATIVE_SYSTEM_PROMPT = (
    "You summarize a nonprofit organization's own IRS Form 990 filing text for "
    "a donor browsing a nonprofit directory. Rules, no exceptions:\n"
    "1. Use ONLY the text supplied below. Never use outside knowledge about "
    "this organization, its name, or its likely activities.\n"
    "2. Never invent, infer, or guess a fact that isn't stated. If the text "
    "doesn't say who they serve, leave populations_served empty -- do not "
    "guess from the org's name.\n"
    "3. Never turn a stated goal or intention into a claimed accomplishment. "
    "'We plan to expand services' is not a reported outcome.\n"
    "4. Never independently verify or editorialize on organization-reported "
    "figures -- report them exactly as stated, this is not a fact-check.\n"
    "5. If the supplied text is too thin or generic to summarize honestly, "
    "return short/empty fields and set grounded=false. An honest empty "
    "result is correct; a plausible-sounding invented one is not."
)


def build_narrative_input(parsed_filing: dict) -> str:
    """Assembles the bounded excerpt bundle from parse_990_xml()'s output
    into the single text block the model sees. Order: mission first (the
    org's own words on its purpose), then programs (what they actually do),
    then Schedule O (supplemental detail), then grant purposes. Each section
    omitted entirely if empty, so a thin filing produces a short, honest
    input rather than empty section headers."""
    parts = []
    mission = parsed_filing.get("mission_text")
    if mission:
        parts.append(f"MISSION (from the filing):\n{mission}")
    # Deterministic change flags (SignificantNewProgramSrvcInd/
    # SignificantChangeInd), already extracted by parse_990_xml() but not
    # previously surfaced here -- found reviewing Phase 4 results (0/16
    # samples got a non-empty new_or_changed_programs, i.e. the model was
    # inferring "did anything change" from prose alone with no direct
    # signal). Pointing the deterministic flag at the model turns
    # new_or_changed_programs from "guess from tone" into "describe what
    # changed, in readable terms, when we already know something did."
    if parsed_filing.get("significant_new_program") or parsed_filing.get("significant_change"):
        parts.append(
            "NOTE: this filing indicates a new or significantly changed program "
            "this year (per the filing's own checkbox, not inferred). If the "
            "PROGRAMS or SCHEDULE O text below describes what's new or changed, "
            "summarize it in new_or_changed_programs."
        )
    programs = parsed_filing.get("programs") or []
    if programs:
        # Codex Review D (2026-08-16): dollar amounts were included here with
        # no output field that uses them, risking the model treating expense
        # size as an implicit signal of program "prominence" or importance --
        # not something we want it inferring. Description text only. (The
        # amounts are still in parsed_filing["programs"][i]["expense_amt"]
        # for any future deterministic use -- Phase 3 doesn't currently
        # persist per-program amounts to a table, only the joined text used
        # for cause_tags; this is a known gap, not something this removal
        # makes worse.)
        prog_lines = [f"- {p['description']}" for p in programs if p.get("description")]
        if prog_lines:
            parts.append("PROGRAMS (from Part III):\n" + "\n".join(prog_lines))
    schedule_o = parsed_filing.get("schedule_o") or []
    if schedule_o:
        so_lines = [f"- {row['explanation']}" for row in schedule_o if row.get("explanation")]
        if so_lines:
            parts.append("SCHEDULE O SUPPLEMENTAL DETAIL:\n" + "\n".join(so_lines))
    grants = parsed_filing.get("grant_purposes") or []
    if grants:
        parts.append("GRANT PURPOSES:\n" + "\n".join(f"- {g}" for g in grants))
    return "\n\n".join(parts)


NARRATIVE_REQUIRED_KEYS = (
    "mission_summary", "services", "populations_served", "geographies",
    "reported_outcomes", "new_or_changed_programs", "other_useful_facts", "grounded",
)


def _normalize_for_match(text: str) -> str:
    return " ".join(text.split()).lower()


def _verify_reported_outcomes(outcomes: list, bounded_input: str, ein: str) -> list:
    """Codex Review D (2026-08-16): a self-reported 'grounded' flag from the
    same model that generated the claims isn't independent verification.
    This is the cheap, mechanical check that actually is: each outcome's
    evidence_quote must appear (whitespace/case-normalized, not exact-byte)
    in the bounded input the model was given. An outcome whose quote doesn't
    match is dropped, not stored -- an unverifiable claim about a nonprofit's
    reported impact is worse than no claim (Stewardship P3)."""
    normalized_input = _normalize_for_match(bounded_input)
    verified = []
    for item in outcomes:
        quote = item.get("evidence_quote", "")
        if quote and _normalize_for_match(quote) in normalized_input:
            verified.append(item)
        else:
            logger.warning(
                f"Dropping unverified reported_outcome for {ein}: "
                f"evidence_quote not found in source text: {quote[:80]!r}"
            )
    return verified


def _validate_shape(result: dict, ein: str) -> bool:
    """Local structural check beyond json.loads succeeding -- Codex Review D
    (2026-08-16) correctly noted valid-JSON-wrong-shape wasn't checked before
    this. Cheap, no jsonschema dependency: confirm every required key is
    present and array fields are actually lists."""
    if not isinstance(result, dict):
        return False
    for key in NARRATIVE_REQUIRED_KEYS:
        if key not in result:
            logger.warning(f"Narrative result for {ein} missing key '{key}' -- rejecting")
            return False
    array_fields = (
        "services", "populations_served", "geographies", "reported_outcomes",
        "new_or_changed_programs", "other_useful_facts",
    )
    for key in array_fields:
        if not isinstance(result[key], list):
            logger.warning(f"Narrative result for {ein} field '{key}' is not a list -- rejecting")
            return False
    return True


def extract_narrative_enrichment(parsed_filing: dict, ein: str) -> dict | None:
    """Derives donor-readable semantic fields from one org's already-parsed
    990 filing (parse_990_xml() output). Returns None on any failure --
    caller must treat that as 'no enrichment this run', never fall back to
    guessing or writing partial data."""
    bounded_input = build_narrative_input(parsed_filing)
    if not bounded_input.strip():
        logger.info(f"No narrative excerpts to summarize for {ein} -- skipping GPU call")
        return None
    result = _call_llm(
        NARRATIVE_SYSTEM_PROMPT, bounded_input, NARRATIVE_ENRICHMENT_SCHEMA,
        timeout=60, max_input_chars=16000, max_tokens=1200,
    )
    if result is None:
        logger.warning(f"Narrative enrichment failed for {ein}")
        return None
    if not _validate_shape(result, ein):
        return None
    result["reported_outcomes"] = _verify_reported_outcomes(
        result["reported_outcomes"], bounded_input, ein
    )
    return result


if __name__ == "__main__":
    # Smoke test against the live local server
    logging.basicConfig(level=logging.INFO)
    sample = (
        "Timbergrove Sports Association is a 501(c)(3) youth sports organization "
        "founded in 1998, serving families in Houston, Texas. In fiscal year 2024, "
        "we had total revenue of $412,000 and total expenses of $389,500, supporting "
        "over 2,000 young athletes across baseball, soccer, and basketball leagues."
    )
    print("Financial extraction test:")
    print(json.dumps(extract_financial_data(sample, "263248544", "https://timbergrovesports.com"), indent=2))
    print("\nMetadata extraction test:")
    print(json.dumps(extract_metadata(sample, "263248544", "https://timbergrovesports.com"), indent=2))

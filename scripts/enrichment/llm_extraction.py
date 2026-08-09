#!/usr/bin/env python3
"""
LLM-powered structured extraction from scraped org website content.

Uses local Qwen3-30B (port 11437) instead of regex/heuristics for:
- Financial figures (revenue, expenses, fiscal year) from /financials pages
- Metadata (founded date, service area, leadership) from /about pages

Why LLM over regex: org websites are wildly inconsistent in formatting.
A financial figure might be in a table, a paragraph, an infographic caption,
or a PDF link. Regex requires enumerating every pattern; the local model
generalizes.

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


def _call_llm(system_prompt, user_content, schema, timeout=30):
    """Fail-closed: any parse or request error returns None, never raises
    into the caller's batch loop (lesson #3 — but here None IS the explicit
    'could not extract' signal, logged by the caller, not swallowed)."""
    try:
        resp = requests.post(
            LLM_ENDPOINT,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content[:8000]},  # cap context
                ],
                "response_format": schema,
                "temperature": 0.1,  # deterministic extraction, not creative
                "max_tokens": 500,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except requests.exceptions.RequestException as e:
        logger.warning(f"LLM extraction request failed: {e}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
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

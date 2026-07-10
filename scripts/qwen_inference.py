#!/usr/bin/env python3
"""
Qwen-32B inference for generating cause tags and websites.

Structured-output contract (2026-07-10 Layer 1 repair): every generator asks
for a JSON object (grammar-enforced server-side when qwen_fn supports the
`schema` kwarg — see get_real_qwen_fn in enrich_batch.py), parses it, and
fails closed. Verbose prose that can't be parsed returns None; a garbage
value must never reach registry_enriched. This replaced the raw
`.strip()` handling that got Layer 1 disabled on 2026-07-08.
"""
import json
import re
from typing import Callable, Optional, Dict, Any
import time


_JSON_OBJ_RE = re.compile(r'\{.*\}', re.DOTALL)
# Bare hostname: labels of [a-z0-9-], at least one dot, alpha TLD. No paths,
# no spaces — anything else means the model didn't answer with a domain.
_DOMAIN_RE = re.compile(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,}$')

TAGS_SCHEMA = {
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5,
        }
    },
    "required": ["tags"],
}
WEBSITE_SCHEMA = {
    "type": "object",
    "properties": {"domain": {"type": "string"}},
    "required": ["domain"],
}
MISSION_SCHEMA = {
    "type": "object",
    "properties": {"mission": {"type": "string"}},
    "required": ["mission"],
}


def _parse_json_obj(text: Optional[str]) -> Optional[dict]:
    """Extract a JSON object from a model response, or None.

    Tries a strict parse first, then the outermost {...} span (handles code
    fences and stray prose around the object). Fails closed on anything else.
    """
    if not text:
        return None
    for candidate in (text, *( [m.group(0)] if (m := _JSON_OBJ_RE.search(text)) else [] )):
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except (json.JSONDecodeError, ValueError):
            continue
    return None


def _normalize_domain(raw: Optional[str]) -> Optional[str]:
    """Reduce a model-suggested domain to a bare validated hostname, or None."""
    if not raw or not isinstance(raw, str):
        return None
    d = raw.strip().lower()
    d = re.sub(r'^https?://', '', d)
    d = d.split('/', 1)[0].split('?', 1)[0]
    if d.startswith('www.'):
        d = d[4:]
    return d if _DOMAIN_RE.match(d) else None


class QwenInference:
    """Generate cause tags and websites using Qwen-32B."""

    def __init__(
        self,
        qwen_fn: Callable,
        config: Dict[str, Any],
        prompt_version: str = 'v1.0',
        timeout_seconds: int = 300
    ):
        self.qwen_fn = qwen_fn
        self.config = config
        self.prompt_version = prompt_version
        self.timeout_seconds = timeout_seconds
        self.prompts = config['prompts'].get(prompt_version, config['prompts']['v1.0'])

    def _call(self, prompt: str, max_tokens: int, schema: dict) -> Optional[str]:
        """Invoke qwen_fn, passing the JSON schema when the fn supports it.

        Legacy qwen_fns (old mocks, callers built before the structured-output
        contract) only accept (prompt, max_tokens) — fall back for those so
        the schema stays a server-side enforcement upgrade, not a hard break.
        """
        try:
            return self.qwen_fn(prompt=prompt, max_tokens=max_tokens, schema=schema)
        except TypeError:
            return self.qwen_fn(prompt=prompt, max_tokens=max_tokens)

    def generate_tags(
        self,
        org_data: Dict[str, Any],
        similar_orgs: list[Dict[str, Any]],
        max_retries: int = 1,
        grounding_context: Optional[str] = None
    ) -> Optional[str]:
        prompt = self._build_cause_tags_prompt(org_data, similar_orgs, grounding_context)
        prompt += '\n\nRespond with only a JSON object: {"tags": ["tag1", "tag2", ...]}'

        for attempt in range(max_retries):
            try:
                result = self._call(prompt, max_tokens=150, schema=TAGS_SCHEMA)
                obj = _parse_json_obj(result)
                if not obj or not isinstance(obj.get('tags'), list):
                    return None  # fail closed: verbose/unparseable output never reaches the DB
                seen = []
                for t in obj['tags']:
                    if isinstance(t, str) and t.strip() and t.strip().lower() not in seen:
                        seen.append(t.strip().lower())
                    if len(seen) == 5:
                        break
                # JSON-array string, matching the cause_tags column format
                return json.dumps(seen) if seen else None
            except TimeoutError:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    print(f"[ERROR] Qwen timeout generating tags for {org_data.get('EIN', 'unknown')}")
                    return None
            except Exception as e:
                print(f"[ERROR] Qwen error for {org_data.get('EIN', 'unknown')}: {e}")
                return None

        return None

    def generate_website(
        self,
        org_data: Dict[str, Any],
        similar_orgs: list[Dict[str, Any]],
        max_retries: int = 1
    ) -> Optional[str]:
        prompt = self._build_website_prompt(org_data, similar_orgs)
        prompt += '\n\nRespond with only a JSON object: {"domain": "example.org"}'

        for attempt in range(max_retries):
            try:
                result = self._call(prompt, max_tokens=50, schema=WEBSITE_SCHEMA)
                obj = _parse_json_obj(result)
                if not obj:
                    return None  # fail closed
                return _normalize_domain(obj.get('domain'))
            except TimeoutError:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    print(f"[ERROR] Qwen timeout generating website for {org_data.get('EIN', 'unknown')}")
                    return None
            except Exception as e:
                print(f"[ERROR] Qwen error for {org_data.get('EIN', 'unknown')}: {e}")
                return None

        return None

    def generate_mission_from_website(
        self,
        org_data: Dict[str, Any],
        website_content: str,
        max_retries: int = 1
    ) -> Optional[str]:
        """Generate a mission statement grounded in real website text.

        This is the fix for generic, template-like missions (e.g. "Provides
        educational services in City, State") — instead of guessing from
        NTEE code + city/state alone, this grounds generation in what the
        org's own website actually says, when a validated site is available.
        Callers should fall back to NTEE-based generation (not this method)
        when no validated website content exists.
        """
        prompt = self._build_mission_prompt(org_data, website_content)
        prompt += '\n\nRespond with only a JSON object: {"mission": "..."}'

        for attempt in range(max_retries):
            try:
                result = self._call(prompt, max_tokens=150, schema=MISSION_SCHEMA)
                obj = _parse_json_obj(result)
                if not obj:
                    return None  # fail closed
                mission = obj.get('mission')
                if isinstance(mission, str) and len(mission.strip()) >= 20:
                    return mission.strip()
                return None
            except TimeoutError:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    print(f"[ERROR] Qwen timeout generating mission for {org_data.get('EIN', 'unknown')}")
                    return None
            except Exception as e:
                print(f"[ERROR] Qwen error generating mission for {org_data.get('EIN', 'unknown')}: {e}")
                return None

        return None

    def _build_mission_prompt(
        self,
        org_data: Dict[str, Any],
        website_content: str
    ) -> str:
        template = self.prompts.get('mission', '')
        return template.format(
            org_name=org_data.get('name', ''),
            website_content=website_content or 'No specific content available.'
        )

    def _build_cause_tags_prompt(
        self,
        org_data: Dict[str, Any],
        similar_orgs: list[Dict[str, Any]],
        grounding_context: Optional[str] = None
    ) -> str:
        similar_tags = ', '.join([
            org.get('cause_tags', '').split(',')[0]
            for org in similar_orgs[:3]
            if org.get('cause_tags')
        ])

        ntee_label = org_data.get('ntee', '?')
        ntee_emphasis = self._get_ntee_emphasis(ntee_label)

        template = self.prompts.get('cause_tags', '')
        prompt = template.format(
            similar_tags=similar_tags or 'Community, Education',
            org_name=org_data.get('name', ''),
            mission=org_data.get('mission', ''),
            ntee=ntee_label,
            ntee_label=self._ntee_label(ntee_label),
            ntee_emphasis=ntee_emphasis
        )

        if grounding_context:
            prompt += f"\n\nAdditional context from the organization's website: {grounding_context}"

        return prompt

    def _build_website_prompt(
        self,
        org_data: Dict[str, Any],
        similar_orgs: list[Dict[str, Any]]
    ) -> str:
        similar_domains = ', '.join([
            org.get('website', '')
            for org in similar_orgs[:3]
            if org.get('website')
        ])

        # org_data['state'] may be present but None (e.g. an org row with no
        # STATE value on file) - dict.get's default only applies when the key
        # is *missing*, not when it's None, so an explicit `or` fallback is
        # required here to actually avoid passing None through.
        state = org_data.get('state') or 'CA'
        state_patterns = self._get_state_domain_patterns(state)

        template = self.prompts.get('website', '')
        return template.format(
            similar_domains=similar_domains or 'example.org, nonprofit.org',
            org_name=org_data.get('name', ''),
            city=org_data.get('city', ''),
            state=state,
            state_patterns=state_patterns
        )

    def _ntee_label(self, ntee: Optional[str]) -> str:
        ntee_labels = {
            'A': 'Arts, Culture & Humanities', 'B': 'Educational Institutions',
            'C': 'Environmental Quality', 'D': 'Animal-Related', 'E': 'Health Care',
            'F': 'Mental Health, Crisis Intervention', 'G': 'Voluntary Health Associations',
            'H': 'Medical Research', 'I': 'Crime & Law Enforcement',
            'J': 'Employment, Job Training', 'K': 'Food, Agriculture & Nutrition',
            'L': 'Housing & Shelter', 'M': 'Public Safety', 'N': 'Recreation & Sports',
            'O': 'Youth Development', 'P': 'Human Services',
            'Q': 'International, Foreign Affairs', 'R': 'Civil Rights, Social Action',
            'S': 'Community Improvement', 'T': 'Philanthropy, Voluntarism',
            'U': 'Science & Technology', 'V': 'Social Science', 'W': 'Public Benefit',
            'X': 'Religion', 'Y': 'Mutual/Membership Benefit', 'Z': 'Unknown'
        }
        return ntee_labels.get((ntee or '?')[0:1], 'Nonprofit Organization')

    def _get_ntee_emphasis(self, ntee: Optional[str]) -> str:
        emphasis_map = {
            'A': 'accessibility, audience engagement, art form',
            'B': 'grade level served, subject matter, educational approach',
            'E': 'type of care, patient demographics, specialty',
            'O': 'age group, youth development area, activity type',
            'P': 'service population, type of assistance, community focus'
        }
        return emphasis_map.get((ntee or '?')[0:1], 'community impact, service type')

    def _get_state_domain_patterns(self, state: str) -> str:
        # Defense in depth: guard against None even though _build_website_prompt
        # already normalizes state before calling this, in case a future
        # caller invokes this helper directly with a None/missing state.
        state_abbrev = (state or '').lower()[:2]
        patterns_map = {
            'ca': '.org, .ngo, nonprofit-ca.org', 'ny': '.org, nonprofit-ny.org, charitable.org',
            'tx': '.org, .net, nonprofit-tx.org', 'fl': '.org, .net, nonprofit-fl.org',
            'default': '.org, nonprofit.org, .net'
        }
        return patterns_map.get(state_abbrev, patterns_map['default'])

"""Structured-output contract for QwenInference (2026-07-10 Layer 1 repair).

Layer 1 was disabled on 2026-07-08 because Qwen2.5-32B-Instruct answers
free-form prompts with verbose prose ("Based on similar organizations, the
most likely domain would be **example.org**...") that the raw
`.strip().lower()` handling wrote downstream as garbage. The repair:

- qwen_fn gains an optional `schema` kwarg; the production fn passes it to
  llama-server as OpenAI-style `response_format: json_schema` (grammar
  enforced server-side), older/mock fns without the kwarg still work.
- Every generator parses a JSON object out of the response and FAILS CLOSED:
  verbose junk returns None, never a garbage value into registry_enriched.
- generate_tags returns a JSON-array string matching the cause_tags column
  format (lowercase, deduped, <=5), fixing the prior comma-prose mismatch.
- generate_website returns a bare validated domain or None.
"""

import json
import pytest
from scripts.qwen_inference import QwenInference


ORG = {
    'EIN': '611234567',
    'name': 'Tech for Good Foundation',
    'mission': 'Provides technology training to underserved communities',
    'ntee': 'T', 'state': 'CA', 'city': 'San Francisco',
}
SIMILAR = [{
    'EIN': '621345678', 'organization_name': 'Urban Tech Alliance',
    'mission': 'Tech education for youth', 'cause_tags': 'Technology, Education',
    'website': 'urtech.org', 'similarity_score': 0.87,
}]


def make_qwen(response: str, capture: dict | None = None):
    """A qwen_fn that supports the schema kwarg and returns a fixed response."""
    def fn(prompt: str, max_tokens: int = 200, schema: dict | None = None) -> str:
        if capture is not None:
            capture['prompt'] = prompt
            capture['schema'] = schema
        return response
    return fn


def make_legacy_qwen(response: str):
    """A qwen_fn WITHOUT the schema kwarg (old mocks / older callers)."""
    def fn(prompt: str, max_tokens: int = 200) -> str:
        return response
    return fn


class TestTags:
    def test_valid_json_returns_normalized_json_array_string(self, enrich_config):
        qwen = QwenInference(qwen_fn=make_qwen('{"tags": ["Education", " Youth ", "education"]}'), config=enrich_config)
        result = qwen.generate_tags(ORG, SIMILAR)
        assert result is not None
        parsed = json.loads(result)
        assert parsed == ["education", "youth"]  # lowercased, stripped, deduped

    def test_verbose_prose_fails_closed(self, enrich_config):
        verbose = ("Based on the mission and similar organizations, I would "
                   "suggest the following cause tags: Education, Youth "
                   "Development, and Community Building. These reflect...")
        qwen = QwenInference(qwen_fn=make_qwen(verbose), config=enrich_config)
        assert qwen.generate_tags(ORG, SIMILAR) is None

    def test_json_inside_code_fence_is_recovered(self, enrich_config):
        fenced = 'Here you go:\n```json\n{"tags": ["arts", "museums"]}\n```'
        qwen = QwenInference(qwen_fn=make_qwen(fenced), config=enrich_config)
        assert json.loads(qwen.generate_tags(ORG, SIMILAR)) == ["arts", "museums"]

    def test_caps_at_five_tags_and_drops_empties(self, enrich_config):
        resp = '{"tags": ["a", "b", "", "c", "d", "e", "f", "g"]}'
        qwen = QwenInference(qwen_fn=make_qwen(resp), config=enrich_config)
        assert len(json.loads(qwen.generate_tags(ORG, SIMILAR))) == 5

    def test_schema_is_passed_to_qwen_fn(self, enrich_config):
        cap = {}
        qwen = QwenInference(qwen_fn=make_qwen('{"tags": ["x"]}', capture=cap), config=enrich_config)
        qwen.generate_tags(ORG, SIMILAR)
        assert cap['schema'] is not None
        assert 'tags' in cap['schema'].get('properties', {})

    def test_legacy_qwen_fn_without_schema_kwarg_still_works(self, enrich_config):
        qwen = QwenInference(qwen_fn=make_legacy_qwen('{"tags": ["health"]}'), config=enrich_config)
        assert json.loads(qwen.generate_tags(ORG, SIMILAR)) == ["health"]


class TestWebsite:
    def test_valid_json_domain_is_returned_bare(self, enrich_config):
        qwen = QwenInference(qwen_fn=make_qwen('{"domain": "TechForGood.org"}'), config=enrich_config)
        assert qwen.generate_website(ORG, SIMILAR) == 'techforgood.org'

    def test_scheme_and_www_are_stripped(self, enrich_config):
        qwen = QwenInference(qwen_fn=make_qwen('{"domain": "https://www.techforgood.org/"}'), config=enrich_config)
        assert qwen.generate_website(ORG, SIMILAR) == 'techforgood.org'

    def test_verbose_prose_fails_closed(self, enrich_config):
        verbose = ("The most likely domain for this organization would be "
                   "**techforgood.org** based on the naming pattern.")
        qwen = QwenInference(qwen_fn=make_qwen(verbose), config=enrich_config)
        assert qwen.generate_website(ORG, SIMILAR) is None

    def test_non_domain_value_fails_closed(self, enrich_config):
        qwen = QwenInference(qwen_fn=make_qwen('{"domain": "I am not sure"}'), config=enrich_config)
        assert qwen.generate_website(ORG, SIMILAR) is None

    def test_null_domain_fails_closed(self, enrich_config):
        qwen = QwenInference(qwen_fn=make_qwen('{"domain": null}'), config=enrich_config)
        assert qwen.generate_website(ORG, SIMILAR) is None


class TestMission:
    def test_valid_json_mission_is_returned(self, enrich_config):
        m = "Provides hands-on technology training to underserved communities in San Francisco."
        qwen = QwenInference(qwen_fn=make_qwen(json.dumps({"mission": m})), config=enrich_config)
        assert qwen.generate_mission_from_website(ORG, "site text " * 20) == m

    def test_verbose_prose_fails_closed(self, enrich_config):
        qwen = QwenInference(qwen_fn=make_qwen("Sure! Here is a mission statement you could use: ..."), config=enrich_config)
        assert qwen.generate_mission_from_website(ORG, "site text " * 20) is None

    def test_too_short_mission_fails_closed(self, enrich_config):
        qwen = QwenInference(qwen_fn=make_qwen('{"mission": "Helps."}'), config=enrich_config)
        assert qwen.generate_mission_from_website(ORG, "site text " * 20) is None

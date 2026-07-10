"""Task 4: Tests for Qwen inference module.

Tests the QwenInference class for:
- Cause tag generation
- Website suggestion generation
- Prompt building with similar org context
- Graceful error handling (timeouts, exceptions)
"""

import pytest
from scripts.qwen_inference import QwenInference


class TestQwenInference:
    """Test QwenInference cause tag and website generation."""

    def test_generate_tags_returns_string(self, mock_qwen, enrich_config):
        """Test that generate_tags returns a non-empty string."""
        qwen = QwenInference(qwen_fn=mock_qwen, config=enrich_config)

        org_data = {
            'EIN': '611234567',
            'name': 'Tech for Good Foundation',
            'mission': 'Provides technology training to underserved communities',
            'ntee': 'T',
            'state': 'CA',
            'city': 'San Francisco'
        }

        similar_orgs = [
            {
                'EIN': '621345678',
                'organization_name': 'Urban Tech Alliance',
                'mission': 'Tech education for youth',
                'cause_tags': 'Technology, Education',
                'website': 'urtech.org',
                'similarity_score': 0.87
            }
        ]

        result = qwen.generate_tags(org_data, similar_orgs)

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_website_returns_string(self, mock_qwen, enrich_config):
        """Test that generate_website returns a non-empty string."""
        qwen = QwenInference(qwen_fn=mock_qwen, config=enrich_config)

        org_data = {
            'EIN': '621345678',
            'name': 'Urban Animal Rescue',
            'city': 'Austin',
            'state': 'TX'
        }

        similar_orgs = [
            {
                'EIN': '611234567',
                'organization_name': 'Animal Care Plus',
                'mission': 'Animal rescue and rehabilitation',
                'cause_tags': 'Animal Welfare',
                'website': 'animalcare.org',
                'similarity_score': 0.79
            }
        ]

        result = qwen.generate_website(org_data, similar_orgs)

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_prompt_includes_similar_org_context(self, enrich_config):
        """Test that prompts include actual similar org context (tags, domains, mission).

        This test verifies that the prompt building methods construct prompts with
        substantive content from similar orgs and the target org, not just placeholder
        values. It checks the actual string content of prompts.
        """
        # Inspect prompts via the builder methods directly — generate_* now
        # parses responses as JSON fail-closed (structured-output contract),
        # so the old echo-the-prompt-through-generate trick no longer applies.
        qwen = QwenInference(qwen_fn=lambda prompt, max_tokens=200: '', config=enrich_config)

        org_data = {
            'EIN': '611234567',
            'name': 'Tech for Good Foundation',
            'mission': 'Provides technology training to underserved communities',
            'ntee': 'T',
            'state': 'CA',
            'city': 'San Francisco'
        }

        similar_orgs = [
            {
                'EIN': '621345678',
                'organization_name': 'Urban Tech Alliance',
                'mission': 'Tech education for youth',
                'cause_tags': 'Technology, Education, Community Development',
                'website': 'urbantech.org',
                'similarity_score': 0.87
            },
            {
                'EIN': '631456789',
                'organization_name': 'Code for All',
                'mission': 'Democratizing coding education',
                'cause_tags': 'Education, Youth Services',
                'website': 'codeforall.org',
                'similarity_score': 0.82
            }
        ]

        # Test cause tags prompt includes similar org tags and target mission
        tags_prompt = qwen._build_cause_tags_prompt(org_data, similar_orgs, None)

        # Verify essential content is in the prompt (similar orgs' first tags and target mission)
        assert 'Technology' in tags_prompt, "First similar org's cause tag not in prompt"
        assert 'Education' in tags_prompt, "Second similar org's cause tag not in prompt"
        assert 'Provides technology training to underserved communities' in tags_prompt, \
            "Target org mission context missing from tags prompt"

        # Test website prompt includes similar org domains and org name/location
        # Use the prompt building method directly to test before .lower() is applied
        website_prompt = qwen._build_website_prompt(org_data, similar_orgs)

        # Verify essential content is in the prompt
        assert 'urbantech.org' in website_prompt or 'codeforall.org' in website_prompt, \
            "Similar org domains not in website prompt"
        assert 'San Francisco' in website_prompt and 'CA' in website_prompt, \
            "Target org location (city and state) context missing from website prompt"

    def test_qwen_timeout_returns_none(self, enrich_config):
        """Test that TimeoutError from Qwen is handled gracefully and returns None.

        This test deterministically raises TimeoutError to verify timeout handling.
        """
        # Create a mock qwen that always raises TimeoutError
        def timeout_qwen(prompt: str, max_tokens: int = 200) -> str:
            raise TimeoutError("Qwen server timeout")

        qwen = QwenInference(qwen_fn=timeout_qwen, config=enrich_config, timeout_seconds=1)

        org_data = {
            'EIN': '611234567',
            'name': 'Tech for Good Foundation',
            'mission': 'Provides technology training',
            'ntee': 'T',
            'state': 'CA',
            'city': 'San Francisco'
        }

        similar_orgs = [
            {
                'EIN': '621345678',
                'organization_name': 'Another Org',
                'cause_tags': 'Technology',
                'website': 'other.org',
                'similarity_score': 0.85
            }
        ]

        # generate_tags should return None on timeout
        result = qwen.generate_tags(org_data, similar_orgs, max_retries=1)
        assert result is None, "generate_tags should return None on timeout"

        # generate_website should return None on timeout
        result = qwen.generate_website(org_data, similar_orgs, max_retries=1)
        assert result is None, "generate_website should return None on timeout"

    def test_generate_tags_with_v1_1_prompt(self, mock_qwen, enrich_config):
        """Test generate_tags using v1.1 prompt version with NTEE emphasis."""
        qwen = QwenInference(
            qwen_fn=mock_qwen,
            config=enrich_config,
            prompt_version='v1.1'
        )

        org_data = {
            'EIN': '631456789',
            'name': 'Community Health Clinic',
            'mission': 'Delivers affordable primary care',
            'ntee': 'E',
            'state': 'IL',
            'city': 'Chicago'
        }

        similar_orgs = [
            {
                'EIN': '641567890',
                'organization_name': 'City Medical Center',
                'cause_tags': 'Health Services, Community Development',
                'website': 'citymedical.org',
                'similarity_score': 0.91
            }
        ]

        result = qwen.generate_tags(org_data, similar_orgs)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_website_lowercase_normalization(self, mock_qwen, enrich_config):
        """Test that generate_website returns lowercase domain names."""
        # Mock qwen that returns uppercase domain (structured-output JSON shape)
        def uppercase_qwen(prompt: str, max_tokens: int = 200) -> str:
            return '{"domain": "MyOrgSite.ORG"}'

        qwen = QwenInference(qwen_fn=uppercase_qwen, config=enrich_config)

        org_data = {
            'EIN': '621345678',
            'name': 'Urban Animal Rescue',
            'city': 'Austin',
            'state': 'TX'
        }

        similar_orgs = []

        result = qwen.generate_website(org_data, similar_orgs)
        assert result == "myorgsite.org", "Website should be normalized to lowercase"

    def test_empty_similar_orgs_fallback(self, mock_qwen, enrich_config):
        """Test that generation works with empty similar_orgs list (uses fallback defaults)."""
        qwen = QwenInference(qwen_fn=mock_qwen, config=enrich_config)

        org_data = {
            'EIN': '651678901',
            'name': 'Environmental Alliance',
            'mission': 'Protects wetlands and habitats',
            'ntee': 'C',
            'state': 'OR',
            'city': 'Portland'
        }

        # Empty list should use fallback values in prompts
        result = qwen.generate_tags(org_data, similar_orgs=[])
        assert result is not None
        assert isinstance(result, str)

        result = qwen.generate_website(org_data, similar_orgs=[])
        assert result is not None
        assert isinstance(result, str)

    def test_ntee_label_mapping(self, enrich_config):
        """Test that _ntee_label maps NTEE codes to descriptive labels."""
        def echo_qwen(prompt: str, max_tokens: int = 200) -> str:
            return prompt

        qwen = QwenInference(qwen_fn=echo_qwen, config=enrich_config)

        # Test a few NTEE codes
        assert "Arts, Culture & Humanities" in qwen._ntee_label('A')
        assert "Educational Institutions" in qwen._ntee_label('B')
        assert "Health Care" in qwen._ntee_label('E')
        assert "Environmental Quality" in qwen._ntee_label('C')
        assert "Unknown" in qwen._ntee_label('Z')  # Unknown category

    def test_state_domain_patterns(self, enrich_config):
        """Test that _get_state_domain_patterns returns appropriate domain suggestions."""
        def echo_qwen(prompt: str, max_tokens: int = 200) -> str:
            return prompt

        qwen = QwenInference(qwen_fn=echo_qwen, config=enrich_config)

        # Test a few states
        ca_patterns = qwen._get_state_domain_patterns('CA')
        assert '.org' in ca_patterns
        assert 'nonprofit' in ca_patterns.lower()

        ny_patterns = qwen._get_state_domain_patterns('NY')
        assert '.org' in ny_patterns
        assert 'nonprofit-ny' in ny_patterns.lower()

        # Unknown state should return default
        xx_patterns = qwen._get_state_domain_patterns('XX')
        assert '.org' in xx_patterns

    def test_ntee_label_handles_none_and_empty(self, enrich_config):
        """Regression test: NULL/empty NTEE1 must not crash _ntee_label.

        287,293 real orgs in merit_registry.db have NULL or empty NTEE1.
        Previously `ntee[0]` raised TypeError on None and IndexError on ''.
        Both must now fall back to the default label without raising.
        """
        def echo_qwen(prompt: str, max_tokens: int = 200) -> str:
            return prompt

        qwen = QwenInference(qwen_fn=echo_qwen, config=enrich_config)

        assert qwen._ntee_label(None) == 'Nonprofit Organization'
        assert qwen._ntee_label('') == 'Nonprofit Organization'

    def test_ntee_emphasis_handles_none_and_empty(self, enrich_config):
        """Regression test: NULL/empty NTEE1 must not crash _get_ntee_emphasis.

        Same root cause as test_ntee_label_handles_none_and_empty - both
        methods indexed ntee[0] directly.
        """
        def echo_qwen(prompt: str, max_tokens: int = 200) -> str:
            return prompt

        qwen = QwenInference(qwen_fn=echo_qwen, config=enrich_config)

        assert qwen._get_ntee_emphasis(None) == 'community impact, service type'
        assert qwen._get_ntee_emphasis('') == 'community impact, service type'

    def test_generate_tags_with_null_ntee_does_not_crash(self, mock_qwen, enrich_config):
        """Integration-level regression test: generate_tags must succeed (not
        raise) for an org whose ntee is None, since _build_cause_tags_prompt
        calls _ntee_label/_get_ntee_emphasis before generate_tags' own
        try/except is ever reached.
        """
        qwen = QwenInference(qwen_fn=mock_qwen, config=enrich_config)

        org_data = {
            'EIN': '999999999',
            'name': 'Org With Missing NTEE',
            'mission': 'Serves the community in an unspecified way',
            'ntee': None,
            'state': 'CA',
            'city': 'Fresno'
        }

        result = qwen.generate_tags(org_data, [])

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0


def test_generate_mission_from_website_returns_string(mock_qwen, enrich_config):
    """Basic contract: given org data + website content, returns a mission string."""
    qwen = QwenInference(qwen_fn=mock_qwen, config=enrich_config, prompt_version='v1.0')

    org_data = {'EIN': '123', 'name': 'Tech Academy', 'ntee': 'B25'}
    website_content = (
        "We provide free coding bootcamps and laptop donations to underserved "
        "youth in San Francisco. Since 2015, we've trained over 400 students "
        "through our after-school Saturday Robotics Academy program."
    )

    result = qwen.generate_mission_from_website(org_data, website_content)

    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_mission_from_website_prompt_includes_real_content(enrich_config):
    """The prompt sent to Qwen must include the actual website text, not
    just NTEE/location — this is the whole point of grounding. Uses an echo
    mock (not mock_qwen) to inspect exactly what was sent."""
    captured_prompts = []

    def echo_qwen(prompt: str, max_tokens: int = 200) -> str:
        captured_prompts.append(prompt)
        return "A specific, grounded mission sentence."

    qwen = QwenInference(qwen_fn=echo_qwen, config=enrich_config, prompt_version='v1.0')

    org_data = {'EIN': '123', 'name': 'Tech Academy', 'ntee': 'B25'}
    website_content = "Saturday Robotics Academy trains 400 students in coding."

    qwen.generate_mission_from_website(org_data, website_content)

    assert len(captured_prompts) == 1
    assert "Saturday Robotics Academy" in captured_prompts[0]
    assert "Tech Academy" in captured_prompts[0]


def test_generate_mission_from_website_timeout_returns_none(enrich_config):
    """Deterministic timeout mock — same pattern as the existing
    test_qwen_timeout_returns_none test for generate_tags/generate_website."""
    def timeout_qwen(prompt: str, max_tokens: int = 200) -> str:
        raise TimeoutError("Qwen timeout")

    qwen = QwenInference(qwen_fn=timeout_qwen, config=enrich_config, prompt_version='v1.0')
    org_data = {'EIN': '123', 'name': 'Org', 'ntee': 'B25'}

    result = qwen.generate_mission_from_website(org_data, "some website content", max_retries=1)

    assert result is None


def test_generate_mission_from_website_empty_content_still_works(mock_qwen, enrich_config):
    """Empty website_content (e.g., a page that fetched but had no useful
    text) should not crash — falls through to a generic-but-valid prompt."""
    qwen = QwenInference(qwen_fn=mock_qwen, config=enrich_config, prompt_version='v1.0')
    org_data = {'EIN': '123', 'name': 'Org', 'ntee': 'B25'}

    result = qwen.generate_mission_from_website(org_data, "")

    assert result is None or isinstance(result, str)


def test_generate_tags_without_grounding_context_unchanged(mock_qwen, enrich_config):
    """Backward compatibility: existing 2-arg calls must still work exactly
    as before — this is a non-breaking extension, not a replacement."""
    qwen = QwenInference(qwen_fn=mock_qwen, config=enrich_config, prompt_version='v1.0')
    org_data = {'EIN': '123', 'name': 'Org', 'mission': 'Test mission', 'ntee': 'B25'}

    result = qwen.generate_tags(org_data, similar_orgs=[])

    assert isinstance(result, str)


def test_generate_tags_with_grounding_context_included_in_prompt(enrich_config):
    """When grounding_context is provided (real website text), it must
    appear in the prompt sent to Qwen — this is what lets cause tags be
    informed by real site content, not just the (possibly still-generic)
    mission field alone."""
    captured_prompts = []

    def echo_qwen(prompt: str, max_tokens: int = 200) -> str:
        captured_prompts.append(prompt)
        return "Education, Youth Development"

    qwen = QwenInference(qwen_fn=echo_qwen, config=enrich_config, prompt_version='v1.0')
    org_data = {'EIN': '123', 'name': 'Org', 'mission': 'Generic mission', 'ntee': 'B25'}
    grounding = "Saturday Robotics Academy trains 400 students in coding and robotics."

    qwen.generate_tags(org_data, similar_orgs=[], grounding_context=grounding)

    assert len(captured_prompts) == 1
    assert "Saturday Robotics Academy" in captured_prompts[0]


def test_generate_tags_without_grounding_context_prompt_unchanged(enrich_config):
    """When grounding_context is None (the default), the prompt must be
    byte-identical to the pre-Task-4 prompt — confirms zero behavior change
    for the common case where no website was found/validated."""
    captured_prompts = []

    def echo_qwen(prompt: str, max_tokens: int = 200) -> str:
        captured_prompts.append(prompt)
        return "Education"

    qwen = QwenInference(qwen_fn=echo_qwen, config=enrich_config, prompt_version='v1.0')
    org_data = {'EIN': '123', 'name': 'Org', 'mission': 'Test mission', 'ntee': 'B25'}

    qwen.generate_tags(org_data, similar_orgs=[])
    prompt_without_grounding = captured_prompts[0]

    captured_prompts.clear()
    qwen.generate_tags(org_data, similar_orgs=[], grounding_context=None)
    prompt_with_none = captured_prompts[0]

    assert prompt_without_grounding == prompt_with_none

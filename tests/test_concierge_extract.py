"""Concierge post-call extraction (eng review T4, design doc 2026-07-10).

Contract: a call transcript goes in, a Quick-Start draft (or None) comes out.
Fail-closed everywhere — a junk transcript must produce NO draft, never a
garbage draft, because a human operator will trust what's on the review
screen (stewardship P3/P10). Mirrors the structured-output contract shipped
2026-07-10 in test_qwen_structured_output.py.
"""

import json
import pytest
from scripts.concierge_extract import extract_draft, write_draft, DRAFTS_DIR


TRANSCRIPT = (
    "Operator: Thanks for calling Daanaa, this call is recorded so we can set "
    "up your page. Caller: Sure. We're the Riverside Youth Robotics club. We "
    "run free after-school robotics and coding clubs for middle schoolers in "
    "Portland. Our website is riversideyouthrobotics.org and donations go "
    "through riversideyouthrobotics.org/donate. Best email is "
    "info@riversideyouthrobotics.org. We always need volunteer mentors."
)


def make_qwen(response, capture=None):
    def fn(prompt, max_tokens=400, schema=None):
        if capture is not None:
            capture['prompt'] = prompt
            capture['schema'] = schema
        return response
    return fn


GOOD_JSON = json.dumps({
    "mission": "Runs free after-school robotics and coding clubs for middle schoolers in Portland.",
    "website": "riversideyouthrobotics.org",
    "donate_url": "https://riversideyouthrobotics.org/donate",
    "contact_email": "info@riversideyouthrobotics.org",
    "contact_phone": None,
    "volunteer_note": "Seeking volunteer mentors.",
})


class TestExtractDraft:
    def test_good_transcript_yields_draft(self):
        draft = extract_draft(TRANSCRIPT, "Riverside Youth Robotics", make_qwen(GOOD_JSON))
        assert draft is not None
        assert draft['website'] == 'riversideyouthrobotics.org'
        assert draft['mission'].startswith('Runs free')

    def test_verbose_prose_fails_closed(self):
        qwen = make_qwen("Sure! Based on the call, here is what I gathered about the org...")
        assert extract_draft(TRANSCRIPT, "Riverside Youth Robotics", make_qwen("prose")) is None
        assert extract_draft(TRANSCRIPT, "Riverside Youth Robotics", qwen) is None

    def test_empty_or_tiny_transcript_fails_closed_without_calling_qwen(self):
        def exploding_qwen(prompt, max_tokens=400, schema=None):
            raise AssertionError("qwen must not be called for junk input")
        assert extract_draft("", "Org", exploding_qwen) is None
        assert extract_draft("hi", "Org", exploding_qwen) is None
        assert extract_draft(None, "Org", exploding_qwen) is None

    def test_invalid_website_is_dropped_not_fatal(self):
        resp = json.dumps({"mission": "A real mission sentence long enough to keep.",
                           "website": "not a domain", "donate_url": None,
                           "contact_email": None, "contact_phone": None,
                           "volunteer_note": None})
        draft = extract_draft(TRANSCRIPT, "Org", make_qwen(resp))
        assert draft is not None
        assert draft['website'] is None

    def test_javascript_donate_url_is_dropped(self):
        resp = json.dumps({"mission": "A real mission sentence long enough to keep.",
                           "website": None, "donate_url": "javascript:alert(1)",
                           "contact_email": None, "contact_phone": None,
                           "volunteer_note": None})
        draft = extract_draft(TRANSCRIPT, "Org", make_qwen(resp))
        assert draft is not None
        assert draft['donate_url'] is None

    def test_all_fields_null_fails_closed(self):
        resp = json.dumps({"mission": None, "website": None, "donate_url": None,
                           "contact_email": None, "contact_phone": None,
                           "volunteer_note": None})
        assert extract_draft(TRANSCRIPT, "Org", make_qwen(resp)) is None

    def test_schema_passed_to_qwen(self):
        cap = {}
        extract_draft(TRANSCRIPT, "Org", make_qwen(GOOD_JSON, capture=cap))
        assert cap['schema'] is not None and 'mission' in cap['schema']['properties']

    def test_transcript_is_truncated_in_prompt(self):
        cap = {}
        long_transcript = "word " * 20000
        extract_draft(long_transcript, "Org", make_qwen(GOOD_JSON, capture=cap))
        assert len(cap['prompt']) < 40000


class TestWriteDraft:
    def test_write_and_content(self, tmp_path, monkeypatch):
        monkeypatch.setattr('scripts.concierge_extract.DRAFTS_DIR', tmp_path)
        draft = json.loads(GOOD_JSON)
        path = write_draft("CAtest123", "123456789", draft, transcript="t" * 30)
        data = json.loads(path.read_text())
        assert data['ein'] == '123456789'
        assert data['call_sid'] == 'CAtest123'
        assert data['draft']['website'] == 'riversideyouthrobotics.org'
        assert data['status'] == 'pending_review'

    def test_call_sid_is_sanitized_for_filesystem(self, tmp_path, monkeypatch):
        monkeypatch.setattr('scripts.concierge_extract.DRAFTS_DIR', tmp_path)
        path = write_draft("../../etc/passwd", "123456789", json.loads(GOOD_JSON), transcript="t" * 30)
        assert path.parent == tmp_path  # traversal neutralized

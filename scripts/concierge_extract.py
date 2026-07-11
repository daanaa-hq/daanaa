#!/usr/bin/env python3
"""Concierge post-call extraction: call transcript -> Quick-Start draft.

Part of the onboarding pilot (design doc akbar-master-design-20260710-200430,
eng review task T4). The operator takes the call; afterwards this module turns
the transcript into a drafted profile the operator reviews and confirms — the
AI never writes to registry data directly (stewardship P10).

Fail-closed contract (same as qwen_inference.py, 2026-07-10): junk in ->
None out, never a garbage draft. The review screen shows only drafts that
parsed, validated, and contain at least one usable fact.

STT is deliberately NOT here — callers pass a transcript. Whisper wiring
lands with the recording work (eng review T3).
"""
import json
import re
from pathlib import Path
from typing import Callable, Optional

from scripts.qwen_inference import _parse_json_obj, _normalize_domain

DRAFTS_DIR = Path(__file__).resolve().parent.parent / 'data' / 'concierge_drafts'

# Transcripts can run long; cap what we send to the model. ~24K chars is
# comfortably inside the 24576-token server context alongside the prompt.
_MAX_TRANSCRIPT_CHARS = 24_000
_MIN_TRANSCRIPT_CHARS = 40  # anything shorter can't contain a real call

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$')
_PHONE_RE = re.compile(r'^[\d\s()+.-]{7,20}$')

CONCIERGE_SCHEMA = {
    "type": "object",
    "properties": {
        "mission": {"type": ["string", "null"]},
        "website": {"type": ["string", "null"]},
        "donate_url": {"type": ["string", "null"]},
        "contact_email": {"type": ["string", "null"]},
        "contact_phone": {"type": ["string", "null"]},
        "volunteer_note": {"type": ["string", "null"]},
    },
    "required": ["mission", "website", "donate_url",
                 "contact_email", "contact_phone", "volunteer_note"],
}

_PROMPT = """You are extracting facts from a phone call between a Daanaa operator and a representative of the nonprofit "{org_name}". Use ONLY what the representative actually said — never invent or embellish. If a fact was not clearly stated, use null.

TRANSCRIPT:
{transcript}

Extract:
- mission: the org's work in the rep's own words, 1-2 sentences (null if not described)
- website: their website domain (null if not mentioned)
- donate_url: where donations happen, full URL if given (null if not mentioned)
- contact_email / contact_phone: public contact they offered (null otherwise)
- volunteer_note: whether/how they want volunteers (null if not discussed)

Respond with only a JSON object: {{"mission": ..., "website": ..., "donate_url": ..., "contact_email": ..., "contact_phone": ..., "volunteer_note": ...}}"""


def _clean_donate_url(raw: Optional[str]) -> Optional[str]:
    """Keep only http(s) URLs (or bare domain+path we can https-prefix)."""
    if not raw or not isinstance(raw, str):
        return None
    u = raw.strip()
    if u.lower().startswith(('http://', 'https://')):
        scheme_ok = True
    elif re.match(r'^[a-z0-9]', u, re.IGNORECASE) and '.' in u.split('/')[0]:
        u = 'https://' + u
        scheme_ok = True
    else:
        scheme_ok = False
    if not scheme_ok:
        return None
    host = re.sub(r'^https?://', '', u).split('/', 1)[0].lower()
    return u if _normalize_domain(host) else None


def extract_draft(transcript: Optional[str], org_name: str, qwen_fn: Callable) -> Optional[dict]:
    """Transcript -> validated Quick-Start draft dict, or None (fail closed)."""
    if not transcript or not isinstance(transcript, str) \
            or len(transcript.strip()) < _MIN_TRANSCRIPT_CHARS:
        return None

    prompt = _PROMPT.format(org_name=org_name,
                            transcript=transcript[:_MAX_TRANSCRIPT_CHARS])
    try:
        try:
            result = qwen_fn(prompt=prompt, max_tokens=400, schema=CONCIERGE_SCHEMA)
        except TypeError:
            result = qwen_fn(prompt=prompt, max_tokens=400)
    except Exception:
        return None

    obj = _parse_json_obj(result)
    if not obj:
        return None

    mission = obj.get('mission')
    if not isinstance(mission, str) or len(mission.strip()) < 20:
        mission = None

    email = obj.get('contact_email')
    if not isinstance(email, str) or not _EMAIL_RE.match(email.strip()):
        email = None

    phone = obj.get('contact_phone')
    if not isinstance(phone, str) or not _PHONE_RE.match(phone.strip()):
        phone = None

    volunteer = obj.get('volunteer_note')
    if not isinstance(volunteer, str) or not volunteer.strip():
        volunteer = None

    draft = {
        'mission': mission.strip() if mission else None,
        'website': _normalize_domain(obj.get('website')),
        'donate_url': _clean_donate_url(obj.get('donate_url')),
        'contact_email': email.strip() if email else None,
        'contact_phone': phone.strip() if phone else None,
        'volunteer_note': volunteer.strip() if volunteer else None,
    }
    if not any(draft.values()):
        return None  # a draft with nothing in it helps nobody
    return draft


def write_draft(call_sid: str, ein: str, draft: dict, transcript: str = '') -> Path:
    """Persist a pending-review draft as JSON (pilot storage, eng review 3A).

    Deleted by the review screen on confirm; anything older than 90 days is
    an unconfirmed leftover the cleanup pass removes (retention rule in the
    design doc).
    """
    safe_sid = re.sub(r'[^A-Za-z0-9_-]', '', call_sid or '')[:64] or 'nocallsid'
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    path = DRAFTS_DIR / f'{safe_sid}.json'
    payload = {
        'call_sid': safe_sid,
        'ein': ''.join(c for c in (ein or '') if c.isdigit())[:10],
        'status': 'pending_review',
        'draft': draft,
        'transcript': transcript,
        'source': 'concierge_call',
    }
    path.write_text(json.dumps(payload, indent=2))
    return path

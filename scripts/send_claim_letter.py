#!/usr/bin/env python3
"""
scripts/send_claim_letter.py

Send a Daanaa claim verification letter to an org's IRS-registered mailing address.
The letter contains a QR code + 6-digit PIN so the org can verify ownership.

MVP mode (no LOB_API_KEY): logs to logs/claim_letters.log for manual printing/mailing.
Production mode (LOB_API_KEY set): sends via Lob.com API (prints + mails same day).

Called by the /api/claim/start endpoint in daanaa_api.py.
"""

import os, io, base64, json, logging, hmac as _hmac, hashlib
from datetime import datetime, timezone
from pathlib import Path

# Must match daanaa_api.py _CLAIM_SECRET derivation.
_CLAIM_SECRET = (
    os.environ.get("DAANAA_CLAIM_SECRET")
    or os.environ.get("DAANAA_ADMIN_KEY")
    or "daanaa-dev-claim-secret"
).encode()

def _make_verify_token(ein: str, pin: str) -> str:
    return _hmac.new(_CLAIM_SECRET, f"{ein}:{pin}".encode(), hashlib.sha256).hexdigest()

LOG_PATH = Path(__file__).parent.parent / "logs" / "claim_letters.log"

def _build_letter_html(org_name: str, ein: str, pin: str, verify_url: str, qr_b64: str, irs_address: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Georgia, serif; color: #1a1a2e; margin: 0; padding: 48px; max-width: 600px; }}
  .header {{ border-bottom: 2px solid #c9a84c; padding-bottom: 16px; margin-bottom: 32px; }}
  .logo {{ font-size: 28px; font-weight: bold; color: #c9a84c; letter-spacing: 0.05em; }}
  .tagline {{ font-size: 12px; color: #666; margin-top: 4px; }}
  h2 {{ font-size: 18px; margin-bottom: 8px; }}
  .org {{ font-size: 16px; color: #1a1a2e; margin-bottom: 4px; font-weight: bold; }}
  .ein {{ font-size: 13px; color: #666; margin-bottom: 24px; }}
  .instruction {{ font-size: 14px; line-height: 1.6; margin-bottom: 24px; }}
  .qr-section {{ text-align: center; margin: 32px 0; }}
  .qr-img {{ width: 180px; height: 180px; }}
  .pin-box {{ border: 2px solid #c9a84c; border-radius: 8px; padding: 16px 24px; display: inline-block; margin-top: 16px; }}
  .pin-label {{ font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }}
  .pin {{ font-size: 32px; font-weight: bold; letter-spacing: 0.3em; color: #1a1a2e; font-family: monospace; }}
  .url {{ font-size: 12px; color: #666; margin-top: 16px; word-break: break-all; }}
  .footer {{ border-top: 1px solid #eee; margin-top: 40px; padding-top: 16px; font-size: 11px; color: #999; }}
</style>
</head>
<body>
  <div class="header">
    <div class="logo">Daanaa</div>
    <div class="tagline">Nonprofit Discovery Platform · daanaa.org</div>
  </div>

  <h2>Claim your organization's page on Daanaa</h2>
  <div class="org">{org_name}</div>
  <div class="ein">EIN: {ein} · {irs_address}</div>

  <div class="instruction">
    We found your organization in the IRS public registry and created a profile on Daanaa —
    a free directory that helps donors discover nonprofits like yours.
    <br><br>
    Scan the QR code below (or visit the URL and enter your PIN) to claim this page.
    Once claimed, you can update your mission, confirm your giving link, and share your
    profile with donors.
  </div>

  <div class="qr-section">
    <img class="qr-img" src="data:image/png;base64,{qr_b64}" alt="Scan to claim your page">
    <div class="pin-box">
      <div class="pin-label">Or enter this PIN at daanaa.org/claim</div>
      <div class="pin">{pin}</div>
    </div>
    <div class="url">{verify_url}</div>
  </div>

  <div class="footer">
    This letter was sent to the address on file with the IRS for EIN {ein}.
    If this is not your organization, you can discard this letter.
    Questions? Email hello@daanaa.org · daanaa.org
  </div>
</body>
</html>"""


def send_claim_letter(ein: str, org_name: str, address: dict, pin: str) -> str | None:
    """
    Send a verification letter. Returns lob_letter_id on success, None on failure.

    address: dict with keys: street, city, state, zip
    """
    verify_token = _make_verify_token(ein, pin)
    verify_url = f"https://daanaa.org/claim/verify?ein={ein}&token={verify_token}"

    # Generate QR code
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
    except ImportError:
        qr_b64 = ""  # qrcode not installed; letter will have no QR image

    irs_address_str = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip', '')}".strip(", ")
    html = _build_letter_html(org_name, ein, pin, verify_url, qr_b64, irs_address_str)

    lob_key = os.environ.get("LOB_API_KEY", "")

    if lob_key:
        try:
            import lob
            lob.api_key = lob_key
            letter = lob.Letter.create(
                description=f"Daanaa claim — {org_name[:50]}",
                to={
                    "name": org_name[:40],
                    "address_line1": address.get("street", "")[:50],
                    "address_city":  address.get("city", ""),
                    "address_state": address.get("state", ""),
                    "address_zip":   address.get("zip", ""),
                    "address_country": "US",
                },
                from_={
                    "name": "Daanaa",
                    "address_line1": os.environ.get("DAANAA_STREET", ""),
                    "address_city":  os.environ.get("DAANAA_CITY", ""),
                    "address_state": os.environ.get("DAANAA_STATE", ""),
                    "address_zip":   os.environ.get("DAANAA_ZIP", ""),
                    "address_country": "US",
                },
                file=html,
                color=False,
                double_sided=False,
            )
            return letter.id
        except Exception as e:
            logging.warning(f"Lob API failed for EIN {ein}: {e} — falling back to log")

    # MVP fallback: log for manual printing/mailing
    LOG_PATH.parent.mkdir(exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "ein": ein,
        "org_name": org_name,
        "to_address": irs_address_str,
        "pin_hash": hashlib.sha256(pin.encode()).hexdigest()[:16],
        "verify_url": verify_url,
        "status": "log_only",
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return f"log:{ein}"  # non-None indicates "letter queued" (manually)

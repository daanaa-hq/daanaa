"""
Contact information extraction from websites and ProPublica 990 data.
Collects: email, phone, executive name, board size, street address.
"""
import re
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

# Email regex (basic)
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
# Phone regex (US format)
PHONE_REGEX = r'(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})'

def extract_contact_from_html(html: str, org_name: str = '') -> Dict[str, str]:
    """Extract email and phone from HTML content."""
    contact = {}

    # Extract email
    emails = re.findall(EMAIL_REGEX, html)
    if emails:
        # Prefer contact@ or info@ over others
        preferred = [e for e in emails if any(x in e.lower() for x in ['contact', 'info', 'hello'])]
        contact['email'] = preferred[0] if preferred else emails[0]

    # Extract phone
    phones = re.findall(PHONE_REGEX, html)
    if phones:
        first_phone = phones[0]
        contact['phone'] = f"+1-{first_phone[0]}-{first_phone[1]}-{first_phone[2]}"

    return contact


def get_propublica_990_contact(ein: str) -> Dict[str, Optional[str]]:
    """Fetch leadership info from ProPublica 990 API."""
    contact = {}

    try:
        # ProPublica 990 API endpoint
        url = f"https://projects.propublica.org/api/nonprofits/{ein}.json"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Extract executive director (if available in response)
            if 'organization' in data:
                org = data['organization']
                # ProPublica doesn't always expose leadership in API
                # This is a placeholder for when API provides it
                if 'executive_name' in org:
                    contact['executive_name'] = org['executive_name']

            logger.debug(f"ProPublica data for {ein}: {contact}")
    except Exception as e:
        logger.debug(f"ProPublica fetch failed for {ein}: {e}")

    return contact


def extract_contact_signals(
    org: Dict,
    html_content: Optional[str] = None
) -> Dict:
    """
    Extract contact signals for an organization.

    Args:
        org: Organization dict with EIN, website, street_address
        html_content: Optional pre-fetched HTML from website

    Returns:
        Dict with contact signals: email, phone, executive_name, board_size, etc.
    """
    contact = {
        'contact_verified_date': datetime.now().isoformat(),
        'contact_sources': []
    }

    # 1. From website if HTML available
    if html_content:
        try:
            web_contact = extract_contact_from_html(html_content, org.get('organization_name', ''))
            contact.update(web_contact)
            if web_contact:
                contact['contact_sources'].append('website_contact_page')
        except Exception as e:
            logger.warning(f"Contact extraction failed for {org['EIN']}: {e}")

    # 2. From ProPublica 990 API
    if org.get('EIN'):
        try:
            propub_contact = get_propublica_990_contact(org['EIN'])
            contact.update(propub_contact)
            if propub_contact:
                contact['contact_sources'].append('990_filing')
        except Exception as e:
            logger.warning(f"ProPublica lookup failed for {org['EIN']}: {e}")

    # 3. Address already in org record (from backfill)
    if org.get('street_address'):
        contact['street_address'] = org['street_address']
        contact['contact_sources'].append('irs_filing')

    return contact if contact.get('email') or contact.get('phone') else {}


def save_contact_to_s3(ein: str, contact: Dict, s3_client) -> bool:
    """Upload contact data to S3."""
    try:
        s3_client.put_object(
            Bucket='daanaa-enrichment',
            Key=f'contact/{ein}.json',
            Body=json.dumps(contact),
            ContentType='application/json',
            Metadata={'last_updated': datetime.now().isoformat()}
        )
        return True
    except Exception as e:
        logger.error(f"S3 upload failed for contact/{ein}.json: {e}")
        return False

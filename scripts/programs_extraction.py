"""
Program information extraction: descriptions, service area, accreditations.
"""
import re
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Known accreditation badges/patterns
ACCREDITATION_PATTERNS = {
    'charity_navigator': (r'charity\s*navigator|cn\.guide', '⭐ Charity Navigator'),
    'guidestar': (r'guidestar|grants\.guide', '🏆 Guidestar'),
    'givewells': (r'givewell|give\s*well', '✓ GiveWell'),
    'candid': (r'candid\.org|foundation\s*center', '📊 Candid'),
    'bcorporation': (r'b\s*corp|certified\s*b\s*corp', 'B Corp Certified'),
    'nonprofit_excellence': (r'nonprofit\s*excellence|npo\s*excellence', '🌟 Excellence'),
}


def calculate_years_active(ruling_date: Optional[str]) -> Optional[int]:
    """Calculate years active from IRS ruling date."""
    if not ruling_date:
        return None

    try:
        # ruling_date format: "2005-06-15" or similar
        ruling_year = int(ruling_date[:4])
        current_year = datetime.now().year
        years = current_year - ruling_year

        if 0 <= years <= 150:  # Sanity check
            return years
    except (ValueError, IndexError, TypeError):
        logger.warning(f"Could not parse ruling_date: {ruling_date}")

    return None


def detect_accreditations(html_content: Optional[str]) -> List[str]:
    """Detect accreditation badges in website HTML."""
    if not html_content:
        return []

    accreditations = []
    html_lower = html_content.lower()

    for badge_key, (pattern, label) in ACCREDITATION_PATTERNS.items():
        if re.search(pattern, html_lower):
            accreditations.append(label)

    return accreditations


def extract_program_signals(
    org: Dict,
    html_content: Optional[str] = None
) -> Dict:
    """
    Extract program capability signals.

    Args:
        org: Organization dict with EIN, mission, ruling_date
        html_content: Optional pre-fetched HTML

    Returns:
        Dict with program signals: descriptions, service_area, years_active, accreditations
    """
    programs = {
        'programs_verified_date': datetime.now().isoformat(),
        'program_sources': []
    }

    # 1. Years active (from ruling date - high confidence)
    if org.get('ruling_date'):
        years_active = calculate_years_active(org['ruling_date'])
        if years_active is not None:
            programs['years_active'] = years_active
            programs['program_sources'].append('irs_ruling_date')

    # 2. Accreditations from website
    if html_content:
        accreditations = detect_accreditations(html_content)
        if accreditations:
            programs['accreditations'] = accreditations
            programs['program_sources'].append('website_badges')

    # 3. Basic service area hints from mission (simple extraction)
    if org.get('mission'):
        mission = org['mission'].lower()
        # Detect common service area keywords
        if any(x in mission for x in ['houston', 'texas', 'tx', 'metro']):
            programs['service_area_hints'] = ['Houston area', 'Texas']
            programs['program_sources'].append('mission_text')

    return programs


def save_programs_to_s3(ein: str, programs: Dict, s3_client) -> bool:
    """Upload programs data to S3."""
    try:
        s3_client.put_object(
            Bucket='daanaa-enrichment',
            Key=f'programs/{ein}.json',
            Body=json.dumps(programs),
            ContentType='application/json',
            Metadata={'last_updated': datetime.now().isoformat()}
        )
        return True
    except Exception as e:
        logger.error(f"S3 upload failed for programs/{ein}.json: {e}")
        return False

"""
Map NTEE codes to cause tags.
NTEE is the authoritative source for organization classification.
This ensures cause_tags always align with actual NTEE classification.

Source: IRS NTEE classification system
"""

# NTEE1 to cause tags mapping (primary classification)
NTEE1_TO_CAUSES = {
    'A': ['arts', 'culture', 'humanities'],
    'B': ['education', 'training'],
    'C': ['environment', 'animals'],
    'D': ['animal welfare', 'animal rescue'],
    'E': ['health', 'healthcare', 'medical'],
    'F': ['mental health', 'substance abuse', 'healthcare'],
    'G': ['diseases', 'medical research', 'health'],
    'H': ['healthcare', 'hospitals', 'medical'],
    'I': ['mental health', 'crisis services'],
    'J': ['employment', 'workforce', 'job training'],
    'K': ['food', 'agriculture', 'nutrition'],
    'L': ['housing', 'shelter'],
    'M': ['public safety', 'disaster relief'],
    'N': ['recreation', 'sports', 'leisure'],
    'O': ['civic engagement', 'civic services'],
    'P': ['civil rights', 'advocacy', 'social justice'],
    'Q': ['community development', 'community services'],
    'R': ['philanthropy', 'charitable giving'],
    'S': ['international', 'foreign affairs', 'humanitarian'],
    'T': ['religion', 'faith based'],
    'U': ['science', 'research', 'technology'],
    'V': ['social services', 'public welfare'],
    'W': ['legal services', 'legal advocacy'],
    'X': ['unknown', 'other'],
    'Y': ['unknown', 'other'],
    'Z': ['unknown', 'other'],
}

def get_causes_from_ntee(ntee1: str, nteecc: str = None) -> list:
    """
    Get cause tags based on NTEE classification.

    Args:
        ntee1: First character of NTEE code (major category)
        nteecc: Full NTEE code (for refinement)

    Returns:
        List of cause tags aligned with NTEE classification
    """
    if not ntee1 or ntee1 not in NTEE1_TO_CAUSES:
        return ['other']

    causes = NTEE1_TO_CAUSES.get(ntee1, ['other']).copy()

    # Add international tag for international orgs
    if nteecc and nteecc.startswith('S'):
        if 'international' not in causes:
            causes.append('international')

    return causes


def should_override_cause_tags(current_tags: list, ntee1: str) -> bool:
    """
    Determine if cause_tags should be overridden based on NTEE mismatch.

    Returns True if current tags don't align with NTEE classification.
    """
    if not current_tags or not ntee1:
        return False

    ntee_causes = NTEE1_TO_CAUSES.get(ntee1, ['other'])

    # Check if any current tag is in the NTEE-appropriate causes
    for tag in current_tags:
        if tag.lower() in [c.lower() for c in ntee_causes]:
            return False  # At least one tag matches, don't override

    # No tags match NTEE classification, override needed
    return True


if __name__ == "__main__":
    # Test cases
    test_cases = [
        ('B', 'B19', ['health', 'healthcare']),  # This should fail the test
        ('E', 'E99', ['health']),  # This should pass
        ('S', 'S99', ['international']),  # International
    ]

    print("Testing NTEE to Cause mapping:\n")
    for ntee1, nteecc, current_tags in test_cases:
        ntee_causes = get_causes_from_ntee(ntee1, nteecc)
        should_override = should_override_cause_tags(current_tags, ntee1)
        print(f"NTEE {ntee1}/{nteecc}: {current_tags}")
        print(f"  → Should be: {ntee_causes}")
        print(f"  → Override needed: {should_override}\n")

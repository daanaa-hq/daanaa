"""
NTEE Questionnaire for v5.0 Taxonomy

7 high-risk NTEE categories require user clarification to assign to the correct archetype.
This module generates the UI questionnaire and processes responses.

High-risk categories (must ask):
- B: Civic/Mutual (44% Donation-Funded, 44% Membership)
- C: Healthcare (70% Donation-Funded, 30% Fee-for-Service)
- E: Mental Health/Behavioral (28% Donation-Funded, 52% Fee-for-Service)
- L: Animals (52% Donation-Funded, 52% Fee-for-Service)
- N: Youth (25% Donation-Funded, 58% Fee-for-Service, 17% Membership)
- S: Civic/Social (52% Donation-Funded, 48% Membership)
- U: Grantmaking (44% Endowment-Funded, 44% Donation-Funded)
"""

NTEE_QUESTIONS = {
    'B': {
        'ntee_name': 'Civic and Social Organizations',
        'question': 'Is your organization primarily funded by donations and grants, or by membership dues?',
        'options': [
            {
                'value': 'donation_funded',
                'label': 'Primarily donations and grants',
                'examples': 'Community centers, advocacy organizations, neighborhood groups',
            },
            {
                'value': 'membership',
                'label': 'Primarily membership dues',
                'examples': 'Civic leagues, professional associations, chambers of commerce',
            },
        ],
    },
    'C': {
        'ntee_name': 'Healthcare',
        'question': 'Is your healthcare organization primarily funded by donations/grants or patient fees/Medicaid reimbursement?',
        'options': [
            {
                'value': 'donation_funded',
                'label': 'Donations and grants (free clinics, health charities)',
                'examples': 'Free or low-cost clinics, community health centers, health advocacy',
            },
            {
                'value': 'fee_for_service',
                'label': 'Patient fees and Medicaid/insurance reimbursement',
                'examples': 'Medicaid clinics, urgent care centers, reimbursement-dependent providers',
            },
        ],
    },
    'E': {
        'ntee_name': 'Mental Health and Behavioral Services',
        'question': 'Is your mental health organization primarily funded by donations/grants or billing insurance/Medicaid?',
        'options': [
            {
                'value': 'donation_funded',
                'label': 'Donations and grants',
                'examples': 'Community counseling, peer support nonprofits, grant-funded clinics',
            },
            {
                'value': 'fee_for_service',
                'label': 'Insurance and Medicaid billing',
                'examples': 'Treatment centers, psychiatric hospitals, reimbursement-based clinics',
            },
        ],
    },
    'L': {
        'ntee_name': 'Animal-Related Organizations',
        'question': 'Is your animal organization primarily a sanctuary/rescue (donations) or a clinic/service (fees)?',
        'options': [
            {
                'value': 'donation_funded',
                'label': 'Sanctuary or rescue (funded by donations)',
                'examples': 'Animal sanctuaries, rescues, animal advocacy',
            },
            {
                'value': 'fee_for_service',
                'label': 'Veterinary clinic or animal services (funded by fees)',
                'examples': 'Veterinary clinics, animal hospitals, boarding services',
            },
        ],
    },
    'N': {
        'ntee_name': 'Youth Development Organizations',
        'question': 'Is your youth organization primarily community-based (donations) or activity/camp-based (program fees)?',
        'options': [
            {
                'value': 'donation_funded',
                'label': 'Community-based (donations and grants)',
                'examples': 'Mentoring programs, youth advocacy, community youth organizations',
            },
            {
                'value': 'fee_for_service',
                'label': 'Activity-based (camps, tuition, program fees)',
                'examples': 'Camps, after-school programs, tuition-based schools',
            },
        ],
    },
    'S': {
        'ntee_name': 'Civic and Social Organizations',
        'question': 'Is your organization primarily funded by donations or membership dues?',
        'options': [
            {
                'value': 'donation_funded',
                'label': 'Primarily donations',
                'examples': 'Community organizations, social nonprofits',
            },
            {
                'value': 'membership',
                'label': 'Primarily membership dues',
                'examples': 'Mutual benefit societies, civic leagues',
            },
        ],
    },
    'U': {
        'ntee_name': 'Grantmaking, Fundraising, and Related Organizations',
        'question': 'Does your grantmaking organization have a permanent endowment or are you pass-through/newly formed?',
        'options': [
            {
                'value': 'endowment',
                'label': 'Permanent endowment (family foundation, lasting endowment)',
                'examples': 'Established family foundations, permanent grantmakers',
            },
            {
                'value': 'donation_funded',
                'label': 'Pass-through or newly formed (no permanent endowment)',
                'examples': 'Pass-through foundations, donor-advised funds, newly established foundations',
            },
        ],
    },
}

def get_questionnaire_for_ntee(ntee1: str) -> dict:
    """
    Return questionnaire data for a given NTEE code, or None if not high-risk.
    """
    ntee1 = (ntee1 or 'Z').upper()
    return NTEE_QUESTIONS.get(ntee1)

def process_questionnaire_response(ntee1: str, response_value: str) -> str:
    """
    Given NTEE code and user's response, return the assigned archetype.
    Returns: archetype key ('donation_funded', 'fee_for_service', 'endowment', 'membership')
    """
    if ntee1 not in NTEE_QUESTIONS:
        return None

    q = NTEE_QUESTIONS[ntee1]
    for opt in q['options']:
        if opt['value'] == response_value:
            return opt['value']

    return None

def generate_questionnaire_html() -> str:
    """
    Generate HTML form for questionnaire (for frontend integration).
    """
    html = """
<div class="ntee-questionnaire">
  <h3>Help us understand your organization's funding model</h3>
  <p>Your organization falls into a category that can be structured different ways.
  To give you the most accurate peer comparison, tell us how you fund yourself:</p>
"""

    for ntee_code in sorted(NTEE_QUESTIONS.keys()):
        q = NTEE_QUESTIONS[ntee_code]
        html += f"""
  <div class="question" data-ntee="{ntee_code}">
    <h4>{q['ntee_name']} (NTEE {ntee_code})</h4>
    <p class="question-text">{q['question']}</p>
"""
        for opt in q['options']:
            html += f"""
    <label class="option">
      <input type="radio" name="ntee_{ntee_code}" value="{opt['value']}" />
      <strong>{opt['label']}</strong><br/>
      <span class="examples">Examples: {opt['examples']}</span>
    </label>
"""
        html += "  </div>\n"

    html += "</div>"
    return html

if __name__ == '__main__':
    # Print questionnaire data
    import json
    print(json.dumps(NTEE_QUESTIONS, indent=2))

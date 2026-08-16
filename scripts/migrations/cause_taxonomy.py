#!/usr/bin/env python3
"""
Cause Taxonomy — 15 cause categories for nonprofit classification.

Maps keywords → causes with confidence scoring.
Used by phase5_mission_backfill.py for cause tag extraction.

Categories are mutually exclusive and ordered by commonality.
Keyword matching is case-insensitive and pattern-based.

Usage:
    from cause_taxonomy import CAUSE_TAXONOMY, extract_causes
    causes, confidence = extract_causes(mission_text)
"""

import re
from typing import Tuple

# ── CAUSE TAXONOMY ────────────────────────────────────────────────────────

CAUSE_TAXONOMY = {
    "education": {
        "label": "Education & Learning",
        "keywords": [
            r"\b(elementary|middle\s*school|high\s*school|secondary\s*school|kindergarten|preschool|pre-k)\b",
            r"\b(college|university|higher\s*education|student\s*loan|financial\s*aid|scholarship)\b",
            r"\b(tutoring|homework\s*help|academic\s*support|after\s*school|after-school)\b",
            r"\b(literacy|reading|english\s*as\s*a\s*second|esl)\b",
            r"\b(stem|science|math|coding|computer\s*science|technology\s*education)\b",
            r"\b(vocational|trade\s*school|apprenticeship|workforce\s*training|job\s*training)\b",
            r"\b(teacher|principal|school|education|learning|curriculum)\b",
        ],
    },
    "health": {
        "label": "Health & Medical",
        "keywords": [
            r"\b(cancer|diabetes|heart\s*disease|chronic\s*disease|illness)\b",
            r"\b(hospital|clinic|medical|doctor|physician|nurse|healthcare)\b",
            r"\b(mental\s*health|depression|anxiety|ptsd|trauma)\b",
            r"\b(maternal\s*health|pregnancy|prenatal|infant|child\s*health)\b",
            r"\b(primary\s*care|preventive\s*care|health\s*equity|health\s*disparit|medically\s*underserved)\b",
            r"\b(substance\s*abuse|addiction|recovery|opioid|alcohol)\b",
            r"\b(disability|disabled|accessible|accessible\s*healthcare)\b",
        ],
    },
    "food": {
        "label": "Food & Nutrition",
        "keywords": [
            r"\b(food\s*bank|food\s*pantry|emergency\s*food|food\s*shelf)\b",
            r"\b(hunger|food\s*insecurity|food\s*access|alleviate\s*hunger)\b",
            r"\b(meals|meal\s*program|school\s*lunch|school\s*meal|free\s*meal)\b",
            r"\b(nutrition|nutritious|healthy\s*eating)\b",
            r"\b(agriculture|garden|farm|local\s*food|food\s*desert)\b",
            r"\b(meal|cooking|food|feast|banquet|dinner)\b",
        ],
    },
    "housing": {
        "label": "Housing & Homelessness",
        "keywords": [
            r"\b(affordable\s*housing|low\s*income\s*housing|housing\s*stability)\b",
            r"\b(homeless|unhoused|experiencing\s*homelessness|houseless)\b",
            r"\b(transitional\s*housing|rapid\s*rehousing|shelter)\b",
            r"\b(eviction\s*prevention|prevent\s*eviction|housing\s*crisis)\b",
            r"\b(housing|rent|apartment|home|living)\b",
        ],
    },
    "youth": {
        "label": "Youth & Child Development",
        "keywords": [
            r"\b(youth\s*development|positive\s*youth|at-risk\s*youth|underserved\s*youth)\b",
            r"\b(mentoring|mentor|big\s*brother|big\s*sister|role\s*model)\b",
            r"\b(summer\s*camp|summer\s*program|summer\s*learning)\b",
            r"\b(foster\s*youth|foster\s*care|aging\s*out|child\s*welfare)\b",
            r"\b(juvenile\s*justice|youth\s*detention|court\s*involved)\b",
            r"\b(childcare|child\s*care|affordable\s*childcare|daycare|preschool)\b",
            r"\b(child\s*abuse|child\s*protect|safe\s*children)\b",
            r"\b(teen|adolescent|young\s*people|youth|kid|child)\b",
        ],
    },
    "environment": {
        "label": "Environment & Conservation",
        "keywords": [
            r"\b(climate|conservation|environmental|ecosystem|habitat)\b",
            r"\b(renewable\s*energy|solar|wind|clean\s*energy|green\s*energy)\b",
            r"\b(water\s*quality|clean\s*water|pollution|waste\s*reduction|recycling)\b",
            r"\b(forest|tree|park|nature|wildlife|endangered\s*species)\b",
            r"\b(sustainability|sustainable|carbon|emissions|greenhouse)\b",
            r"\b(environmental\s*justice|climate\s*justice|toxic\s*exposure)\b",
        ],
    },
    "arts": {
        "label": "Arts & Culture",
        "keywords": [
            r"\b(art|museum|gallery|exhibition|artist)\b",
            r"\b(music|concert|orchestra|band|musician|singer|theater|theatre|play)\b",
            r"\b(dance|ballet|performance|performing\s*arts)\b",
            r"\b(literature|book|writing|author|poet|poetry|film|movie|cinema)\b",
            r"\b(cultural|culture|heritage|community\s*center|creative)\b",
            r"\b(arts\s*education|music\s*education|creative\s*education)\b",
        ],
    },
    "civil_rights": {
        "label": "Civil Rights & Social Justice",
        "keywords": [
            r"\b(racial\s*equity|racial\s*justice|anti-racism|anti\s*racism|systemic\s*racism)\b",
            r"\b(civil\s*rights|voting\s*rights|voter\s*access|voting\s*access)\b",
            r"\b(lgbtq|transgender|trans|gender\s*identity|sexual\s*orientation)\b",
            r"\b(immigrant|immigration|undocumented|daca|refugee|asylum)\b",
            r"\b(discrimination|bias|equity|equality|equal\s*opportunity)\b",
            r"\b(people\s*of\s*color|bipoc|black\s*community|latino\s*community|native\s*american)\b",
        ],
    },
    "employment": {
        "label": "Employment & Economic Development",
        "keywords": [
            r"\b(job\s*placement|job\s*training|employment\s*training|workforce\s*development)\b",
            r"\b(small\s*business|entrepreneurship|startup|micro-enterprise|microenterprise)\b",
            r"\b(financial\s*literacy|financial\s*capability|asset\s*building|financial\s*education)\b",
            r"\b(living\s*wage|poverty\s*alleviation|economic\s*empowerment|economic\s*mobility)\b",
            r"\b(employment|job|career|work|workforce|labor)\b",
        ],
    },
    "seniors": {
        "label": "Seniors & Aging",
        "keywords": [
            r"\b(elder|senior|older\s*adult|aging|age\s*friendly|caregiver)\b",
            r"\b(meals\s*on\s*wheels|senior\s*center|aging\s*in\s*place)\b",
            r"\b(retirement|pension|social\s*security|medicare|medicaid)\b",
            r"\b(dementia|alzheimer|cognitive|memory\s*loss)\b",
        ],
    },
    "animals": {
        "label": "Animal Welfare",
        "keywords": [
            r"\b(animal|pet|dog|cat|wildlife|sanctuary|rescue)\b",
            r"\b(animal\s*welfare|animal\s*protection|animal\s*cruelty|animal\s*abuse)\b",
            r"\b(shelter|adoption|spay|neuter|veterinary|vet)\b",
            r"\b(endangered\s*species|wildlife\s*protection|habitat\s*preservation)\b",
        ],
    },
    "international": {
        "label": "International & Global Affairs",
        "keywords": [
            r"\b(international|global|global\s*health|world|humanitarian|developing\s*countries)\b",
            r"\b(africa|asia|latin\s*america|caribbean|middle\s*east|south\s*asia)\b",
            r"\b(foreign\s*aid|international\s*development|global\s*development|poverty\s*reduction)\b",
            r"\b(peace|conflict\s*resolution|human\s*rights|genocide\s*prevention)\b",
        ],
    },
    "disability": {
        "label": "Disability Services",
        "keywords": [
            r"\b(disability|disabled|developmental\s*disability|intellectual\s*disability)\b",
            r"\b(deaf|blind|hearing\s*loss|vision\s*loss|accessibility|accessible)\b",
            r"\b(autism|autistic|asperger|cerebral\s*palsy|down\s*syndrome|muscular\s*dystrophy)\b",
            r"\b(rehabilitation|therapy|occupational\s*therapy|physical\s*therapy)\b",
        ],
    },
    "community": {
        "label": "Community Development",
        "keywords": [
            r"\b(community\s*development|community\s*center|neighborhood|civic\s*engagement)\b",
            r"\b(disaster\s*relief|disaster\s*recovery|emergency\s*response|natural\s*disaster)\b",
            r"\b(homeless|poverty|economic\s*disadvantage|low-income|low\s*income)\b",
            r"\b(community|neighborhood|local|region|city|town)\b",
        ],
    },
    "social_services": {
        "label": "Social Services & Family Support",
        "keywords": [
            r"\b(family\s*services|child\s*welfare|foster\s*care|adoption)\b",
            r"\b(domestic\s*violence|intimate\s*partner|abuse|domestic\s*abuse)\b",
            r"\b(social\s*services|case\s*management|counseling|therapy)\b",
            r"\b(family|parent|children|youth|vulnerable|at-risk)\b",
        ],
    },
    "research": {
        "label": "Research & Science",
        "keywords": [
            r"\b(research|scientific|science|study|experiment|clinical\s*trial)\b",
            r"\b(university|academic|institute|laboratory|lab)\b",
            r"\b(medical\s*research|health\s*research|biomedical|pharmaceutical)\b",
        ],
    },
}


def extract_causes(text: str, limit: int = 5) -> Tuple[list[str], float]:
    """
    Extract cause tags from text.

    Args:
        text: Mission/description text to analyze
        limit: Max number of cause tags to return (default 5)

    Returns:
        (cause_list, confidence_score)
        - cause_list: List of cause category labels (e.g., ["education", "youth"])
        - confidence_score: 0.0-1.0 confidence in the extraction

    Algorithm:
        1. Score each cause by keyword matches in text
        2. Rank by match count and return top N
        3. Confidence = (match_count / text_words) capped at 1.0
    """
    if not text or not isinstance(text, str):
        return [], 0.0

    text_lower = text.lower()
    text_words = len(text_lower.split())

    cause_scores: dict[str, int] = {}

    for cause_key, cause_data in CAUSE_TAXONOMY.items():
        match_count = 0
        for pattern in cause_data["keywords"]:
            matches = len(re.findall(pattern, text_lower))
            match_count += matches

        if match_count > 0:
            cause_scores[cause_key] = match_count

    # Sort by match count descending
    ranked = sorted(cause_scores.items(), key=lambda x: x[1], reverse=True)

    # Extract top N
    result = [cause_key for cause_key, _ in ranked[:limit]]

    # Confidence: how many keywords matched vs text length
    total_matches = sum(cause_scores.values())
    confidence = min(1.0, (total_matches / max(text_words, 1)) * 0.5)

    return result, confidence


if __name__ == "__main__":
    # Quick test
    test_mission = (
        "Provides tutoring and after-school programs for low-income youth in underserved "
        "communities. Focuses on STEM education and mentorship to improve academic outcomes."
    )
    causes, conf = extract_causes(test_mission)
    print(f"Test mission: {test_mission}")
    print(f"Extracted causes: {causes}")
    print(f"Confidence: {conf:.2f}")

"""
NTEE-based synonym expansion for search.

Maps nonprofit categories to common synonyms so queries like "animal rescue"
find "animal shelter" orgs, "food bank" finds "hunger relief", etc.

Used as query-time fallback when FTS + semantic + fuzzy all return zero results.
"""

NTEE_SYNONYMS = {
    # Animal-related
    "animal shelter": ["animal rescue", "pet adoption", "animal welfare", "humane society", "spca"],
    "animal rescue": ["animal shelter", "pet adoption", "animal welfare", "humane society"],
    "pet adoption": ["animal shelter", "animal rescue", "humane society"],
    "wildlife": ["animal conservation", "habitat protection", "endangered species"],

    # Hunger/food
    "food bank": ["hunger relief", "food pantry", "food assistance", "meals on wheels", "soup kitchen"],
    "hunger relief": ["food bank", "food pantry", "food assistance", "meals"],
    "soup kitchen": ["food bank", "hunger relief", "meals"],
    "meals on wheels": ["food bank", "elderly meals", "meal delivery"],

    # Housing
    "homeless shelter": ["housing assistance", "homeless services", "homelessness", "housing support"],
    "housing assistance": ["homeless shelter", "affordable housing", "housing support"],
    "affordable housing": ["housing assistance", "low-income housing"],
    "low-income housing": ["affordable housing", "housing assistance"],

    # Youth
    "youth services": ["youth development", "youth programs", "children's services", "youth mentoring"],
    "youth mentoring": ["youth programs", "mentorship", "at-risk youth"],
    "boy scouts": ["youth programs", "youth development", "scouting"],
    "girl scouts": ["youth programs", "youth development", "scouting"],

    # Education
    "literacy": ["reading programs", "adult education", "educational support"],
    "tutoring": ["academic support", "educational assistance", "youth education"],
    "scholarship": ["educational funding", "student aid", "education grants"],
    "school supplies": ["educational materials", "student support"],

    # Health
    "cancer": ["oncology", "cancer support", "cancer research"],
    "diabetes": ["endocrinology", "disease support", "health education"],
    "mental health": ["mental illness", "psychiatric care", "behavioral health", "counseling"],
    "addiction": ["substance abuse", "recovery support", "rehabilitation"],
    "rehabilitation": ["addiction recovery", "substance abuse treatment", "physical therapy"],
    "hospice": ["palliative care", "end-of-life care", "terminal care"],

    # Seniors
    "elderly services": ["senior services", "aging support", "senior centers"],
    "senior centers": ["elderly services", "aging programs", "senior activities"],
    "meals for seniors": ["meals on wheels", "elderly nutrition", "senior meals"],

    # Disability
    "disability services": ["special needs", "accessibility", "assistive technology"],
    "blind": ["vision impaired", "visual disability", "blindness support"],
    "deaf": ["deaf services", "hearing impaired", "sign language"],
    "cerebral palsy": ["developmental disability", "disability services"],

    # Family/domestic
    "domestic violence": ["abuse shelter", "domestic abuse", "family violence"],
    "abuse shelter": ["domestic violence", "domestic abuse", "family safety"],
    "child abuse": ["child protection", "child welfare", "child safety"],
    "foster care": ["child welfare", "child protection", "family services"],

    # Community
    "community center": ["community programs", "community services", "neighborhood center"],
    "neighborhood": ["community", "local services", "community development"],
    "volunteering": ["volunteer opportunities", "community service"],

    # Legal
    "legal aid": ["free legal services", "legal assistance", "pro bono"],
    "immigration": ["refugee services", "immigrant services", "asylum"],
    "civil rights": ["social justice", "equality", "anti-discrimination"],

    # Environmental
    "conservation": ["environmental protection", "habitat protection", "wildlife"],
    "park": ["outdoor recreation", "greenspace", "nature"],
    "trail": ["hiking", "recreation", "outdoor activities"],

    # Arts/culture
    "arts": ["cultural programs", "art education", "performing arts"],
    "museum": ["cultural institution", "historical", "educational"],
    "theater": ["performing arts", "drama", "arts education"],
    "music": ["performing arts", "music education", "orchestra"],

    # Sports/recreation
    "basketball": ["sports programs", "youth athletics", "recreation"],
    "soccer": ["sports programs", "youth athletics", "recreation"],
    "baseball": ["sports programs", "youth athletics", "recreation"],
    "swimming": ["aquatics", "sports programs", "recreation"],

    # Faith
    "church": ["religious organization", "worship", "faith community"],
    "synagogue": ["jewish community", "religious organization", "worship"],
    "mosque": ["muslim community", "religious organization", "worship"],
    "christian": ["religious organization", "faith community", "church"],
}


def expand_query_with_synonyms(query: str) -> list[str]:
    """
    Given a search query, return the query plus synonym expansions.

    Example:
        expand_query_with_synonyms("animal rescue")
        → ["animal rescue", "animal shelter", "pet adoption", ...]
    """
    query_lower = query.lower().strip()
    expanded = {query_lower}

    # Direct match: "animal rescue" in NTEE_SYNONYMS
    if query_lower in NTEE_SYNONYMS:
        expanded.update(NTEE_SYNONYMS[query_lower])

    # Prefix match: "animal rescue center" → try "animal rescue"
    for key in NTEE_SYNONYMS:
        if query_lower.startswith(key):
            expanded.add(key)
            expanded.update(NTEE_SYNONYMS[key])
            break
        if query_lower in key:
            expanded.add(key)
            expanded.update(NTEE_SYNONYMS[key])

    return sorted(list(expanded))


if __name__ == "__main__":
    # Test
    tests = [
        "animal rescue",
        "food bank",
        "homeless shelter",
        "youth programs",
        "mental health",
    ]
    for q in tests:
        expanded = expand_query_with_synonyms(q)
        print(f"{q:20} → {', '.join(expanded)}")

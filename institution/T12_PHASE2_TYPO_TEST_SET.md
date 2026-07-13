# T12 Phase 2: Typo Tolerance Test Set

**Purpose:** Measure recall@5 for misspelled/abbreviated nonprofit queries.
**Decision gate:** Recall > 0.90 → ship; otherwise iterate.
**Built:** 2026-07-12 (synthetic, pending real Phase 1 analytics data)

## Test queries (50 common variations)

Generated from:
- Common typos in nonprofit names (missing letters, phonetic variations)
- Abbreviations that don't match indexed names
- Query variations that should match common causes/sectors

| Query | Expected Match | Category | Notes |
|-------|--------|----------|-------|
| "food bank" | Food for the Hungry / Feeding America | Hunger | Exact nominal match |
| "fod bank" | Food for the Hungry | Hunger | Missing 'o' |
| "enviromental" | Environmental Defense Fund | Environment | Missing 'n' |
| "womens shelter" | Women's Foundation | Women | Possessive variation |
| "homeless shelter" | National Alliance to End Homelessness | Homelessness | Word order |
| "childrens hospital" | Children's Mercy | Healthcare | Possessive |
| "mental helth" | National Alliance on Mental Illness | Mental Health | Misspelled 'health' |
| "aniaml rescue" | Best Friends Animal Society | Animals | Misspelled 'animal' |
| "cancer reserch" | American Cancer Society | Cancer | Misspelled 'research' |
| "diabetes assoc" | American Diabetes Association | Diabetes | Abbreviation |
| "heart assn" | American Heart Association | Cardiovascular | Abbreviation |
| "red cross" | American Red Cross | Disaster | Nominal match |
| "salvation army" | Salvation Army | Social Services | Nominal match |
| "goodwill" | Goodwill Industries | Job Training | Nominal match |
| "planned parenthood" | Planned Parenthood | Reproductive Health | Nominal match |
| "sierra club" | Sierra Club | Conservation | Nominal match |
| "greenpeace" | Greenpeace | Environmental | Nominal match |
| "amnisty international" | Amnesty International | Human Rights | Misspelled 'amnesty' |
| "doctors without borders" | Médecins Sans Frontières | International | English nominal |
| "oxfam" | Oxfam International | International Relief | Nominal match |
| "wwf" | World Wildlife Fund | Wildlife | Abbreviation |
| "unicef" | UNICEF | International | Nominal match |
| "urban league" | National Urban League | Civil Rights | Nominal match |
| "naacp" | NAACP | Civil Rights | Abbreviation |
| "aclu" | ACLU | Civil Rights | Abbreviation |
| "habitat for humanity" | Habitat for Humanity | Housing | Nominal match |
| "habitat for humanty" | Habitat for Humanity | Housing | Misspelled 'humanity' |
| "st judes" | St. Jude Children's Research Hospital | Pediatric Cancer | Apostrophe/period variation |
| "boys and girls club" | Boys & Girls Clubs | Youth | Ampersand variation |
| "boys & girls club" | Boys & Girls Clubs | Youth | Ampersand form |
| "special olympics" | Special Olympics | Disability Sports | Nominal match |
| "ds" | Down Syndrome Association | Disability | Abbreviation |
| "autism speaks" | Autism Speaks | Autism | Nominal match |
| "cerebral palsy assoc" | United Cerebral Palsy | Disability | Abbreviated |
| "muscular distrophy" | Muscular Dystrophy Association | Disability | Misspelled 'dystrophy' |
| "leukemia lymphoma" | Leukemia and Lymphoma Society | Blood Cancer | Abbreviated |
| "nature consrvancy" | The Nature Conservancy | Conservation | Misspelled 'conservancy' |
| "national parks" | National Parks Foundation | Conservation | Partial name |
| "world animal foundation" | World Animal Foundation | Animals | Nominal match |
| "peta" | PETA | Animal Rights | Abbreviation |
| "humane society" | Humane Society | Animals | Nominal match |
| "aspca" | ASPCA | Animal Welfare | Abbreviation |
| "meals on wheels" | Meals on Wheels America | Senior Services | Nominal match |
| "meals on wheels america" | Meals on Wheels America | Senior Services | Full nominal |
| "boys town" | Boys Town | Youth | Nominal match |
| "kiva" | Kiva | Microfinance | Nominal match |
| "khan academy" | Khan Academy | Education | Nominal match |
| "khan acedemy" | Khan Academy | Education | Misspelled 'academy' |
| "city year" | City Year | Youth | Nominal match |
| "teach for america" | Teach For America | Education | Nominal match |

---

## Measurement methodology

**Recall@5:** Of 50 test queries, how many return their expected match in the top 5 results?

**Current baseline (FTS only):** To be measured
**Target (with typo tolerance):** > 0.90 (45+ of 50)

## Implementation

**Phase 2a: Trigram layer** (SQLite spellfix1)
```sql
CREATE VIRTUAL TABLE spellfix_orgs USING spellfix1(rank=10);
INSERT INTO spellfix_orgs(word) SELECT organization_name FROM registry_enriched;
```

**Phase 2b: Query logic**
```python
def search_with_typo_tolerance(query):
    # Exact FTS match first
    results = fts_search(query)
    if len(results) >= 5:
        return results[:5]
    
    # Spellfix suggestions if zero or few results
    if len(results) == 0:
        suggestions = db.execute(
            "SELECT word FROM spellfix_orgs WHERE word MATCH ? LIMIT 3",
            (query,)
        ).fetchall()
        # Retry with top suggestion
        if suggestions:
            corrected = suggestions[0][0]
            results = fts_search(corrected)
    
    return results[:5]
```

## Decision rule

- If recall@5 >= 0.90: Ship Phase 2 → proceed to Phase 3 (Synonyms)
- If recall@5 < 0.90: Iterate on spellfix rank/threshold → re-test
- If recall remains low: Consider alternative (n-gram, fuzzy matching) → document in LESSONS.md

# Enrichment Phase 2: Contact + Capability Signals

**Status**: Approved 2026-07-08  
**Stewardship**: Passes Principles 2, 3, 4, 7, 9  
**Performance**: No impact on search/browse (S3 lazy-loads on detail only)  

---

## Goals

1. Surface small orgs with limited financial data fairly
2. Give users verifiable contact info for due diligence
3. Show capability signals (programs, accreditations, years active)
4. Keep droplet lean, search fast

---

## Data to Collect

### Contact Signals (S3: `contact/{EIN}.json`)

| Field | Source | Extraction Method | Confidence |
|-------|--------|-------------------|------------|
| `email` | Website contact page | Crawl contact/about pages, regex | High |
| `phone` | Website, 990 filing | Same crawl + ProPublica API | High |
| `street_address` | 990 filing, website | Already 1.97M/1.7M (backfilled) | High |
| `executive_name` | 990 filing | ProPublica 990 API, Schedule O | Medium |
| `board_size` | 990 filing | ProPublica API count | Medium |
| `contact_verified_date` | Metadata | Date of collection | - |
| `contact_sources` | Metadata | ["website_contact_page", "990_filing", "propublica"] | - |

### Program Signals (S3: `programs/{EIN}.json`)

| Field | Source | Extraction Method | Confidence |
|-------|--------|-------------------|------------|
| `program_descriptions` | Website, 990 filing | Qwen extraction + manual review | Medium |
| `service_area` | Website, mission | Qwen extraction from website | Medium |
| `years_active` | Ruling date | `current_year - ruling_date` | High |
| `accreditations` | Website badges | Detect Charity Navigator, GiveWell, Candid.org badges | High |
| `years_active_verified_date` | Metadata | Date of collection | - |

### DB Fields to Add (Registry)

Keep minimal - just flags to indicate S3 data availability:

```sql
ALTER TABLE registry_enriched ADD COLUMN contact_available BOOLEAN DEFAULT FALSE;
ALTER TABLE registry_enriched ADD COLUMN programs_available BOOLEAN DEFAULT FALSE;
ALTER TABLE registry_enriched ADD COLUMN years_active INTEGER;
```

---

## Pipeline Changes

### Enrichment Batch Updates

Add to `scripts/enrich_batch.py`:

```python
class ContactExtraction(Task):
    """Extract contact info from website + ProPublica 990 API"""
    def run(self, org: Dict) -> Dict:
        contact = {}
        
        # 1. From website crawl (already happening for donation links)
        if org.get('website'):
            contact['email'] = extract_email_from_website(org['website'])
            contact['phone'] = extract_phone_from_website(org['website'])
        
        # 2. From ProPublica 990 API
        if org.get('EIN'):
            propub_data = get_propublica_990_data(org['EIN'])
            if propub_data:
                contact['executive_name'] = propub_data.get('executive_name')
                contact['board_size'] = len(propub_data.get('board_members', []))
        
        contact['contact_verified_date'] = datetime.now().isoformat()
        contact['contact_sources'] = [...]  # track sources
        
        return contact

class ProgramExtraction(Task):
    """Extract program descriptions + accreditations"""
    def run(self, org: Dict) -> Dict:
        programs = {}
        
        # 1. Program descriptions via Qwen
        if org.get('website'):
            programs['program_descriptions'] = qwen_extract_programs(
                org['website'], org['mission']
            )
        
        # 2. Service area from website/mission
        programs['service_area'] = qwen_extract_service_area(
            org['website'], org['mission']
        )
        
        # 3. Years active (simple calc)
        if org.get('ruling_date'):
            programs['years_active'] = (
                datetime.now().year - int(org['ruling_date'][:4])
            )
        
        # 4. Accreditations (detect badges on website)
        programs['accreditations'] = detect_accreditation_badges(org['website'])
        
        return programs
```

### S3 Upload

After enrichment completes:

```python
# Upload to S3
s3_client.put_object(
    Bucket='daanaa-enrichment',
    Key=f'contact/{org["EIN"]}.json',
    Body=json.dumps(contact_data),
    ContentType='application/json',
    Metadata={'last_updated': datetime.now().isoformat()}
)

s3_client.put_object(
    Bucket='daanaa-enrichment',
    Key=f'programs/{org["EIN"]}.json',
    Body=json.dumps(programs_data),
    ContentType='application/json'
)

# Update DB flags only
db.execute(
    'UPDATE registry_enriched SET contact_available=?, programs_available=?, years_active=? WHERE EIN=?',
    (True, True, programs['years_active'], org['EIN'])
)
```

---

## API Changes

### GET /api/organizations/{EIN} (Detail Page)

Current response is unchanged. Add **optional** S3 fetch:

```python
@app.route('/api/organizations/<ein>')
def get_organization(ein):
    org = load_org_from_db(ein)  # Fast, DB only
    
    # Conditionally load S3 enrichment (on detail view only)
    if request.args.get('include_enrichment') == '1':
        try:
            contact = s3_client.get_object(
                Bucket='daanaa-enrichment',
                Key=f'contact/{ein}.json'
            )
            org['contact'] = json.loads(contact['Body'].read())
        except:
            pass  # Silent fail if S3 missing
        
        try:
            programs = s3_client.get_object(
                Bucket='daanaa-enrichment',
                Key=f'programs/{ein}.json'
            )
            org['programs'] = json.loads(programs['Body'].read())
        except:
            pass
    
    return jsonify(org)
```

### Browse/Search APIs

**No changes** — contact_available flag stays in DB for optional filtering.

---

## Frontend Changes

### Detail Page Component

Create `OrgEnrichmentCard.tsx`:

```typescript
export default function OrgEnrichmentCard({ ein }: { ein: string }) {
  const [contact, setContact] = useState(null)
  const [programs, setPrograms] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    // Lazy load S3 data only on detail page
    fetch(`/api/organizations/${ein}?include_enrichment=1`)
      .then(r => r.json())
      .then(org => {
        setContact(org.contact)
        setPrograms(org.programs)
        setLoading(false)
      })
  }, [ein])
  
  return (
    <div className="space-y-6">
      {contact && <ContactCard data={contact} />}
      {programs && <ProgramsCard data={programs} />}
    </div>
  )
}
```

### Contact Card

Shows: email, phone, street address, executive name, board size  
Each field links to source ("From org website", "IRS 990 filing")

### Programs Card

Shows: program list, service area, years active, accreditations  
Each accreditation links to verifier (Charity Navigator, etc)

---

## Rollout Plan

### Week 1: Enrichment Collection
- Update `enrich_batch.py` with ContactExtraction + ProgramExtraction
- Create S3 bucket: `s3://daanaa-enrichment/`
- Test on 1K orgs, validate extraction quality
- Fix any failures, retry

### Week 2: API Integration
- Add `include_enrichment` param to detail endpoint
- Test S3 fetch latency (should be <200ms)
- Cache S3 responses for 1 hour in browser

### Week 3: UI Rollout
- Add OrgEnrichmentCard to detail page
- Monitor S3 costs + latency
- Gradual rollout (10% → 50% → 100%)

---

## Monitoring

### Metrics to Track

- S3 API latency (target: <200ms p95)
- Enrichment extraction success rate (target: >90%)
- Contact info accuracy (via org claims feedback)
- Cost (should stay <$50/month)

### Alerts

- S3 latency > 500ms → page slowdown
- Extraction success < 80% → quality degradation
- Cost > $100/month → scale issue

---

## Privacy & Compliance

- ✅ All data from public sources (websites, IRS 990, ProPublica)
- ✅ No private data collected
- ✅ Org claims system allows corrections
- ✅ Not sold or shared with external parties
- ✅ Sources documented for transparency

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-08 | Approve Phase 2 | Passes all stewardship criteria; no impact on search perf |
| 2026-07-08 | Use S3 for storage | Keeps droplet lean; cost <$50/month |
| 2026-07-08 | Lazy-load on detail | No slowdown on browse/search |

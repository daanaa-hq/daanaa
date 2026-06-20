# FAQ Bot Setup & Seeding

The FAQ bot (`config/n8n-workflows/faq-bot.json`) powers semantic search to answer common donor and nonprofit questions. This guide shows how to set it up.

---

## Architecture

```
Email arrives → n8n email-triage detects FAQ question keywords 
  → Routes to FAQ-bot webhook
  → FAQ-bot embeds query (mxbai-embed-large)
  → Searches FAQ database (vector similarity)
  → If confidence > 0.7: auto-reply with FAQ answer
  → If confidence < 0.7: escalate to Chatwoot for human review
```

---

## Step 1: Create FAQ Database Schema

The main Daanaa API (`daanaa_api.py`) needs a new `/api/faq/*` endpoint and database table.

### Add to `merit_registry.db`

```sql
CREATE TABLE IF NOT EXISTS faq (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category TEXT NOT NULL,           -- "donor", "nonprofit", "general"
  question TEXT NOT NULL UNIQUE,    -- "How do I donate to an organization?"
  answer TEXT NOT NULL,             -- Full answer text
  source_url TEXT,                  -- Link to more info
  embeddings BLOB,                  -- Pre-computed vector (mxbai-embed-large)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  active BOOLEAN DEFAULT 1
);

CREATE INDEX faq_category ON faq(category);
CREATE INDEX faq_active ON faq(active);
```

### Add API Endpoint to `daanaa_api.py`

```python
import numpy as np
from scipy.spatial.distance import cosine

@app.route('/api/faq/search', methods=['GET'])
def faq_search():
    """Search FAQ by semantic similarity."""
    query = request.args.get('query', '')
    limit = int(request.args.get('limit', 3))
    
    if not query:
        return jsonify({'error': 'query required'}), 400
    
    # Get query embedding
    query_embedding = embed_text(query)
    
    # Search FAQ table
    cursor = get_db().cursor()
    cursor.execute('SELECT id, question, answer, source_url, embeddings FROM faq WHERE active=1')
    faqs = cursor.fetchall()
    
    # Calculate similarity scores
    results = []
    for faq in faqs:
        faq_embedding = np.frombuffer(faq[4], dtype=np.float32)
        similarity = 1 - cosine(query_embedding, faq_embedding)
        results.append({
            'id': faq[0],
            'question': faq[1],
            'answer': faq[2],
            'source_url': faq[3],
            'similarity': float(similarity)
        })
    
    # Sort by similarity, return top N
    results = sorted(results, key=lambda x: x['similarity'], reverse=True)[:limit]
    
    return jsonify({'results': results}), 200

def embed_text(text):
    """Get mxbai-embed-large embedding."""
    response = requests.post(
        'http://localhost:11436/v1/embeddings',
        json={'input': text, 'model': 'mxbai-embed-large'}
    )
    embedding = response.json()['data'][0]['embedding']
    return np.array(embedding, dtype=np.float32)
```

---

## Step 2: Seed FAQ Data

### Initial FAQ Dataset (Start Small)

Load this into the `faq` table:

```sql
INSERT INTO faq (category, question, answer, source_url) VALUES

-- Donor FAQs
('donor', 'How do I donate to an organization?', 
 'You can donate directly to any organization by visiting their website and clicking their donate button. Daanaa helps you discover organizations but the donation always goes directly to them.', 
 'https://daanaa.org/about'),

('donor', 'Is my donation private?', 
 'Yes. Daanaa does not track or share your giving activity. Your giving is completely private. We only help you discover and learn about organizations.',
 'https://daanaa.org/privacy'),

('donor', 'How do I know if an organization is trustworthy?', 
 'All organizations on Daanaa are real 501(c)(3) nonprofits registered with the IRS. We show financial health signals and peer comparisons to help you make informed decisions.',
 'https://daanaa.org/research'),

('donor', 'Can I support multiple organizations?', 
 'Yes! You can add organizations to your Giving Wallet and manage your support preferences. Daanaa helps you diversify your impact across causes you care about.',
 'https://daanaa.org/wallet'),

('donor', 'What is a "hidden gem"?', 
 'Hidden gems are small, financially healthy organizations that do great work but have low visibility. They often use every dollar very effectively because they have tight operations.',
 'https://daanaa.org/hidden-gems'),

-- Nonprofit FAQs
('nonprofit', 'How do I claim my organization page on Daanaa?', 
 'Call us at +1-833-DAANAA-2 (voice claims) or email support@daanaa.org with your EIN and domain email. We verify ownership and give you edit access.',
 'https://daanaa.org/claim'),

('nonprofit', 'How can I improve my organization''s visibility?', 
 'Make sure your website is current, your mission statement is clear, and your donation page works. Daanaa ranks organizations by financial health, not size—small, healthy orgs get fair visibility.',
 'https://daanaa.org/support'),

('nonprofit', 'What information does Daanaa show about my organization?', 
 'Daanaa displays your mission, financial health (based on IRS 990 data), peer comparisons, donation link, and verified contact info. We do not publish private information.',
 'https://daanaa.org/about'),

('nonprofit', 'How do I log volunteer hours?', 
 'Visit daanaa.org/volunteer/log-hours to record volunteer time. This helps donors understand your community impact.',
 'https://daanaa.org/volunteer'),

-- General FAQs
('general', 'Is Daanaa free to use?', 
 'Yes. Daanaa is completely free for both donors and nonprofits. We do not charge fees or take a cut of donations.',
 'https://daanaa.org/pricing'),

('general', 'How often is Daanaa''s data updated?', 
 'Organization data is updated monthly from IRS 990 filings. Website links are verified quarterly. Financial health is re-calculated daily.',
 'https://daanaa.org/research'),

('general', 'Can I contact Daanaa directly?', 
 'Email support@daanaa.org or call +1-833-DAANAA-2. We try to respond within 24 hours.',
 'https://daanaa.org/support');
```

### Compute Embeddings

After seeding, compute embeddings for all FAQs:

```bash
#!/bin/bash
# scripts/embed_faq_vectors.py

import sqlite3
import requests
import numpy as np

conn = sqlite3.connect('/home/akbar/meritgiving/data/merit_registry.db')
cursor = conn.cursor()

# Get all active FAQs without embeddings
cursor.execute('SELECT id, question FROM faq WHERE active=1 AND embeddings IS NULL')
faqs = cursor.fetchall()

print(f"Computing embeddings for {len(faqs)} FAQ questions...")

for faq_id, question in faqs:
    # Get embedding from local mxbai-embed-large
    response = requests.post(
        'http://localhost:11436/v1/embeddings',
        json={'input': question, 'model': 'mxbai-embed-large'},
        timeout=30
    )
    
    embedding = np.array(response.json()['data'][0]['embedding'], dtype=np.float32)
    
    # Store as blob
    cursor.execute(
        'UPDATE faq SET embeddings = ? WHERE id = ?',
        (embedding.tobytes(), faq_id)
    )
    
    print(f"  ✅ FAQ {faq_id}: {question[:50]}...")

conn.commit()
conn.close()
print("Done. All FAQ embeddings computed.")
```

Run it:
```bash
cd /home/akbar/meritgiving
source venv/bin/activate
python scripts/embed_faq_vectors.py
```

---

## Step 3: Import FAQ Bot Workflow into n8n

1. Open n8n: `http://localhost:5678`
2. **Workflows** → **Import**
3. Paste contents of `config/n8n-workflows/faq-bot.json`
4. Enable the workflow
5. Test with a webhook POST:

```bash
curl -X POST http://localhost:5678/webhook/faq-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I donate?",
    "email": "test@example.com",
    "subject": "Question"
  }'
```

**Expected:** Auto-reply email arrives within 1 minute (or Chatwoot ticket for low-confidence match)

---

## Step 4: Connect Email Intent Detection → FAQ Bot

Modify the email-triage workflow to route FAQ questions to the FAQ bot webhook:

In `config/n8n-workflows/email-triage.json`, after the Intent Detector node, add a new condition:

```json
{
  "parameters": {
    "conditions": {
      "options": [
        {
          "condition": "string",
          "value1": "{{ $node[\"Intent Detector\"].json.intent }}",
          "value2": "faq"
        }
      ]
    }
  },
  "id": "10",
  "name": "If FAQ Question",
  "type": "n8n-nodes-base.if",
  "typeVersion": 1,
  "position": [650, 600]
}
```

Connect it to an HTTP Request node that POSTs to the FAQ bot webhook:

```json
{
  "parameters": {
    "method": "POST",
    "url": "http://n8n:5678/webhook/faq-query",
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "query",
          "value": "{{ $node[\"Intent Detector\"].json.subject + ' ' + $node[\"Intent Detector\"].json.body }}"
        },
        {
          "name": "email",
          "value": "{{ $node[\"Intent Detector\"].json.from }}"
        },
        {
          "name": "subject",
          "value": "{{ $node[\"Intent Detector\"].json.subject }}"
        }
      ]
    }
  },
  "id": "11",
  "name": "Route to FAQ Bot",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4
}
```

---

## Step 5: Update Intent Detector (Optional Enhancement)

Add FAQ keyword detection to the Intent Detector function node:

```javascript
// In config/n8n-workflows/email-triage.json, Intent Detector node:

let intent = 'unknown';
let priority = 'low';

const text = (subject + ' ' + body).toLowerCase();

// Check for FAQ patterns
if (text.includes('how') || text.includes('what') || text.includes('question') || text.includes('help')) {
  intent = 'faq';
  priority = 'low';
  confidence = 0.85;
}
// ... rest of intent detection
```

This routes FAQ questions automatically without manual classification.

---

## Testing the FAQ Bot

### Test Case 1: High-Confidence Match

```bash
# Send email to daanaa@daanaa.org
Subject: How do I donate?
Body: I want to give to a nonprofit but I'm not sure how.

# Expected: Auto-reply within 1 min with FAQ answer
# "You can donate directly to any organization by visiting their website..."
```

### Test Case 2: Low-Confidence Match

```bash
Subject: Question about giving
Body: I have a weird situation and I'm not sure what to do.

# Expected: No auto-reply, Chatwoot ticket created for human review
# Ticket tagged: faq_query, confidence: 0.45
```

---

## Maintenance & Tuning

### Weekly Review

1. Check Chatwoot for FAQ escalations
   ```bash
   # In Chatwoot UI: Filter by source_id='faq_escalation'
   ```

2. Identify unanswered questions
   - Are they answerable with existing FAQs?
   - Do we need a new FAQ entry?

3. Add new FAQs as patterns emerge
   ```sql
   INSERT INTO faq (category, question, answer, source_url) 
   VALUES ('donor', '[new question]', '[answer]', '[link]');
   ```

4. Re-compute embedding for new FAQ
   ```bash
   python scripts/embed_faq_vectors.py
   ```

### Monitor FAQ Bot Performance

```bash
# Query Metabase for FAQ metrics
# Card: "FAQ Bot Response Rate"
# Query FAQ queries over last 7 days, % auto-responded (confidence ≥ 0.7)
```

**Target:** >80% of FAQ questions answered with high confidence

---

## Limitations & Future Work

- **Current:** English only (Spanish support coming)
- **Current:** FAQ answers must be pre-written (no generative AI)
- **Future:** Harvest FAQ from past Chatwoot escalations (identify patterns)
- **Future:** Semantic similarity tuning (adjust confidence threshold as data grows)

---

## Rollback

If the FAQ bot is causing problems (wrong answers being sent):

```bash
# Disable FAQ bot workflow in n8n
# In n8n UI: Workflows → FAQ Bot → Deactivate

# Remove FAQ routing from email-triage
# In n8n UI: Edit email-triage → Delete "Route to FAQ Bot" node

# All FAQ questions will be treated as "unknown" → escalate to Chatwoot
```

---

## References

- `config/n8n-workflows/faq-bot.json` — Workflow definition
- `config/n8n-workflows/email-triage.json` — Main email workflow (update to route FAQs)
- `scripts/embed_faq_vectors.py` — Embedding computation script
- `docs/AUTOMATION_BUILD_SUMMARY.md` — Overall architecture

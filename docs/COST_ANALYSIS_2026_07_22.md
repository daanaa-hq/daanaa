# Cost Analysis & Subscription Stack

**Date:** 2026-07-22  
**Status:** Current costs + Future costs + Optimization strategy

---

## Current Monthly Costs (Free Platform)

### Infrastructure

| Service | Provider | Usage | Cost | Notes |
|---------|----------|-------|------|-------|
| **Droplet (Web Server)** | DigitalOcean | 2GB RAM, 2 vCPU, 50GB SSD | $18/mo | US-based (NYC region) |
| **Backup Storage (S3)** | AWS S3 | ~100GB cold storage | $2-3/mo | Mentioned in memory (git history) |
| **Static Files CDN** | Included (Droplet) | - | $0 | Served direct from droplet |
| **Database** | SQLite (file-based) | - | $0 | No separate service |
| **Inference (Local)** | Droplet GPU | Qwen2.5, mxbai-embed | $0 | Included in droplet cost |
| **SUBTOTAL: INFRASTRUCTURE** | | | **$20-21/mo** | |

---

### SaaS & Services

| Service | Provider | Usage | Cost | US-Based? | Notes |
|---------|----------|-------|------|-----------|-------|
| **Analytics** | Plausible | ~10K pageviews/mo | $0/mo | ✅ (EU/US) | Privacy-first, GDPR compliant |
| **Auth** | Firebase (Google) | ~1K users | $0/mo (free tier) | ✅ US-based | Generous free tier, pay as you grow |
| **Domain** | Namecheap / Godaddy | daanaa.org | $10-15/yr | ✅ US-based | ~$1-1.50/mo |
| **Email (SMTP)** | NOT YET USED | - | $0/mo | - | Need: SendGrid, Mailgun, or AWS SES |
| **SMS/Voice** | NOT YET USED | - | $0/mo | - | Need: Twilio for AI assistant (future) |
| **Payment Processing** | NOT YET USED | - | $0/mo | - | Need: Stripe for subscriptions (future) |
| **Monitoring/Errors** | NOT YET USED | - | $0/mo | - | Optional: Sentry, Datadog (future) |
| **SUBTOTAL: SAAS & SERVICES** | | | **$1-2/mo** | | |

---

### Development & Tools

| Service | Provider | Usage | Cost | US-Based? | Notes |
|---------|----------|-------|------|-----------|-------|
| **GitHub** | GitHub/Microsoft | 1 private repo | $0/mo | ✅ US-based | Free tier, unlimited private repos |
| **NPM** | npm Inc | Public package hosting | $0/mo | ✅ US-based | Free for public packages |
| **AI API** | Anthropic (Claude) | NOT YET USED | $0/mo | ✅ US-based | Will cost $$$$ once AI assistant launches |
| **SUBTOTAL: DEV TOOLS** | | | **$0/mo** | | |

---

## **TOTAL CURRENT MONTHLY: $21-23/mo**

### Breakdown
```
Infrastructure:  $20-21 (95%)
Services:        $1-2   (5%)
Dev Tools:       $0     (0%)
─────────────────────────
TOTAL:           $21-23/month
```

**Annual:** ~$250-280/year for FREE platform with 500+ nonprofits

---

## Future Costs (When You Scale & Add Features)

### When You Add Email Notifications

| Service | Cost | US-Based? | Volume |
|---------|------|-----------|--------|
| **Mailgun** | $35/mo | ✅ US | 50K emails/mo |
| **SendGrid** | $30/mo | ✅ US | 50K emails/mo |
| **AWS SES** | $0.10 per 1K emails | ✅ US | ~$5/mo for 50K |
| **Recommendation** | **AWS SES** | ✅ | Cheapest, US-based |

### When You Add AI Assistant (Phase 3)

**Text Chat (Web):**
| Service | Cost | US-Based? |
|---------|------|-----------|
| **Claude API (text)** | ~$0.50-2/user/month | ✅ Anthropic (US) |
| **At 100 users:** | $50-200/mo | |
| **At 500 users:** | $250-1000/mo | |

**Voice (Phone):**
| Service | Cost | US-Based? |
|---------|------|-----------|
| **Twilio (inbound)** | $1/month + $0.0075/min | ✅ Twilio (US) |
| **Speech-to-text** | $0.0003/sec (AWS Transcribe) | ✅ AWS (US) |
| **Text-to-speech** | $4/1M chars (AWS Polly) | ✅ AWS (US) |
| **At 100 active users (10min calls/mo avg):** | ~$50-75/mo | |
| **At 500 active users:** | ~$200-300/mo | |

### Estimated Costs at Scale (500 nonprofits, 100 paying)

```
Free Platform Tier (400 users):
  Droplet:                $18/mo
  S3 Backup:              $3/mo
  Email (50K/mo):         $5/mo
  Analytics:              $0/mo
  Auth (Firebase free):   $0/mo
  Domain:                 $1.50/mo
  ──────────────────────────────
  Subtotal:               $27.50/mo

Paid Platform (AI Chat, 100 users):
  Claude API (text):      $100-150/mo
  ──────────────────────────────
  Subtotal:               $100-150/mo

Voice Assistant (optional, 30 of 100):
  Twilio + AWS:           $75-100/mo
  ──────────────────────────────
  Subtotal:               $75-100/mo (shared across all)

────────────────────────────────────
TOTAL AT SCALE:           $200-280/mo (~$2,400-3,360/year)
```

**Revenue (100 paying at $29-49/mo):**
```
Plus Tier (70 users × $29):    $2,030/mo
Pro Tier (30 users × $49):     $1,470/mo
─────────────────────────────────
GROSS REVENUE:                 $3,500/mo
COSTS:                         $250-280/mo
───────────────────────────────
NET (before taxes, payroll):   $3,200-3,250/mo
MARGIN:                        92%
```

---

## Services We're Using (Audited for US-Based)

### ✅ US-Based Services (Preferred)

| Service | Provider | Status | Cost | Why |
|---------|----------|--------|------|-----|
| **Hosting** | DigitalOcean | Active | $18/mo | Excellent, NYC datacenter |
| **Analytics** | Plausible | Active | $0/mo | Privacy-first, GDPR, EU/US |
| **Auth** | Firebase/Google | Active | $0/mo | Massive scale, free tier generous |
| **AI** | Anthropic (Claude) | Planned | $0.001-0.01/token | Best quality, US-based |
| **Email** | AWS SES | Needed | $5/mo | Cheapest, reliable |
| **SMS/Voice** | Twilio | Planned | Pay-per-use | Gold standard for voice |
| **Backup Storage** | AWS S3 | Active | $2-3/mo | Reliable, cold storage |
| **Domain** | Namecheap | Active | $1.50/mo | Cheap, US-based |
| **Payment** | Stripe | Needed | 2.9% + $0.30/txn | US-based, best for nonprofits |
| **Monitoring** | Sentry | Optional | $29/mo | Error tracking, US-based |

### ⚠️ What We DON'T Need (Foreign Services)

- ❌ Google Cloud (no specific service we need)
- ❌ Azure (no specific service we need)
- ❌ Datadog (expensive, Sentry cheaper)
- ❌ PagerDuty (too early for on-call)
- ❌ CloudFlare (DigitalOcean sufficient)

---

## Cost Optimization Strategy

### **Tier 1: No-Brainer Optimizations (Do Now)**

| Optimization | Savings | Effort | Risk |
|--------------|---------|--------|------|
| Use AWS SES instead of Mailgun | $20-30/mo | 1 hr | None |
| Cache more aggressively (reduce API calls) | $0 (but faster) | 2 hrs | Low |
| Compress database (SQLite VACUUM) | $0 (but smaller backups) | 30 min | None |
| Use Plausible free tier (not upgrading) | $0/mo current | 0 hrs | None |
| Keep Firebase free tier (don't upgrade) | $0/mo current | 0 hrs | None |

**Total savings: $0-30/mo, but improvement to user experience**

---

### **Tier 2: Scale-Conscious Optimizations (When Growing)**

| Optimization | Timing | Savings | Tradeoff |
|--------------|--------|---------|----------|
| Use Claude for non-critical tasks, cheaper models (Llama) for others | Q2 2027 | 30-40% of AI costs | Quality slightly lower |
| Upgrade droplet only when hitting 80% CPU (not before) | When needed | $18/mo → $24/mo | Wait longer to upgrade |
| Use cold S3 storage for old backups | Q4 2026 | 50% of backup costs | Slower recovery |
| Batch email sends (daily digest instead of immediate) | Q4 2026 | None saved, but smoother load | Slight UX delay |

---

### **Tier 3: Major Architecture Changes (Only If Needed)**

| Change | Savings | Complexity | When |
|--------|---------|-----------|------|
| Move to serverless (AWS Lambda) | Save $18 droplet, pay per request | High | Only if traffic >1000 reqs/sec |
| Use managed PostgreSQL instead of SQLite | Add $15/mo | Medium | Only if >10GB data |
| Build custom inference layer (remove Anthropic) | Save 70% of Claude costs | Very High | Only if 1000+ paid users |

**Reality: You won't need these for years, if ever.**

---

## Current vs. Optimized (No-Brainer Changes)

### Current Setup

```
Monthly:
  DigitalOcean Droplet:     $18
  AWS S3 Backup:            $3
  Mailgun Email:            $35 (not yet used)
  Firebase:                 $0
  Plausible:                $0
  Domain:                   $1.50
  ─────────────────────────────
  TOTAL:                    $57.50/mo

But honestly: You're only using $22/mo right now
(Mailgun not needed until Q4 2026)
```

### Optimized Setup (Just Change Email)

```
Monthly:
  DigitalOcean Droplet:     $18
  AWS S3 Backup:            $3
  AWS SES Email:            $5 (when needed)
  Firebase:                 $0
  Plausible:                $0
  Domain:                   $1.50
  ─────────────────────────────
  TOTAL:                    $27.50/mo

Savings vs Mailgun:         $30/mo ($360/year)
```

---

## Service Stack Recommendation

### **NOW (Free Platform)**

**Essentials:**
- ✅ DigitalOcean Droplet 2GB ($18/mo)
- ✅ AWS S3 for backups ($3/mo)
- ✅ Firebase Auth (free tier, $0/mo)
- ✅ Plausible Analytics (free tier, $0/mo)
- ✅ Domain ($1.50/mo)

**Total: $22.50/mo**

---

### **Q4 2026 (Add Email + Paid Features)**

**Add:**
- ✅ AWS SES for emails ($5/mo)
- ✅ Stripe for payments (2.9% + $0.30/txn, only on revenue)

**Upgrade (maybe):**
- ℹ️ Firebase (if >10K users) → $25/mo
- ℹ️ Sentry error tracking (optional) → $29/mo

**Total: $60-62/mo base + % of revenue on payments**

---

### **Q1 2027 (Add AI Assistant)**

**Add:**
- ✅ Claude API for text/voice ($100-200/mo depending on usage)
- ✅ Twilio for voice ($1/mo + per-minute)
- ✅ AWS Transcribe/Polly for speech ($20-40/mo estimated)

**Total: $180-260/mo + Claude API**

---

## US-Based Services Summary

| Service | Provider | Cost | Status |
|---------|----------|------|--------|
| **Compute** | DigitalOcean (NYC) | $18/mo | ✅ Active |
| **Storage** | AWS S3 | $3/mo | ✅ Active |
| **Auth** | Firebase (Google) | $0/mo | ✅ Active |
| **Analytics** | Plausible | $0/mo | ✅ Active |
| **Email** | AWS SES | $5/mo | ⏳ Soon |
| **Payments** | Stripe | 2.9% + $0.30 | ⏳ When paid |
| **Voice** | Twilio (SF HQ) | Pay-per-use | ⏳ Q1 2027 |
| **AI** | Anthropic (SF) | $0.001-0.01/token | ⏳ Q1 2027 |
| **Speech** | AWS Transcribe/Polly | $0.0003/sec | ⏳ Q1 2027 |
| **Error Tracking** | Sentry | $29/mo (optional) | ⏳ Later |
| **Monitoring** | CloudWatch (AWS free tier) | $0/mo | ✅ Available |
| **Backup Monitoring** | AWS CloudWatch | $0/mo | ✅ Built-in |

**All US-based. Zero foreign services. ✅**

---

## Cost Reduction Playbook

### **Immediately (Do This Week)**

```
1. Switch email from Mailgun to AWS SES
   → Save $30/mo starting Q4
   → Change: 1 environment variable

2. Enable SQLite VACUUM on backup
   → Reduce S3 size by 20-30%
   → Save $0.50-1/mo (small, but compound)

3. Keep Firebase free tier forever
   → It auto-scales, free up to 100K connections
   → You won't hit it for years
```

**Savings: $30-31/mo (starting Q4)**

---

### **When Revenue Starts (Q2 2027)**

```
1. Use Stripe's nonprofit discount (2.2% instead of 2.9%)
   → Save 0.7% of revenue
   → At $3,500/mo revenue: Save $24/mo

2. Use AWS Lambda for any async jobs
   → Instead of cron on droplet
   → Saves: Nothing immediately, but future-proofs

3. Enable SQLite WAL mode offloading
   → Moves WAL writes to S3
   → Saves: Droplet disk IO
```

**Savings: $24/mo on payments**

---

### **If You Hit Scale (500+ users)**

```
1. Negotiate Anthropic pricing at volume
   → At $10K+/mo spend: Get 20-30% discount
   → Ask for startup program (free credits)

2. Use open-source LLM (Llama 2) for non-critical tasks
   → Keep Claude for core features
   → Saves: 60-70% of non-critical AI costs

3. Upgrade to Droplet 4GB only when hitting 75% CPU
   → Don't upgrade early
   → Save: ~$25/mo per month delayed
```

---

## Bottom Line

### **Today**
```
Cost:     $22.50/mo
Revenue:  $0
Margin:   N/A (free platform)
```

### **After Free Platform Launch (3 months)**
```
Cost:     $22.50/mo
Revenue:  $0 (still free)
Margin:   N/A (free platform)
Runway:   Infinite (costs are trivial)
```

### **When AI Assistant Ships (6 months)**
```
Cost:     $27.50/mo + AI costs
Revenue:  $3,500/mo (100 paying users)
Margin:   ~90%
Runway:   Indefinite (profitable)
```

### **At Scale (12 months)**
```
Cost:     $250-280/mo + AI costs
Revenue:  $10,000-15,000/mo (300 paying)
Margin:   ~95%
Runway:   Years (highly profitable)
```

---

## What NOT to Do

❌ **Don't use:**
- Datadog (too expensive, use Sentry or CloudWatch)
- Google Cloud (DigitalOcean is simpler)
- PagerDuty (too early)
- CloudFlare (DigitalOcean CDN sufficient)
- Segment (you don't need analytics routing yet)

❌ **Don't upgrade:**
- Firebase beyond free tier (not needed until 100K+ users)
- Plausible beyond free tier (current traffic is tiny)
- Droplet until CPU >75% (premature optimization)

---

## The Path Forward

| Phase | Cost | Revenue | Action |
|-------|------|---------|--------|
| **Now (Free)** | $22/mo | $0 | Launch & grow users |
| **Q4 2026 (Paid)** | $62/mo | $500-1000/mo | Add email, payments |
| **Q1 2027 (AI)** | $280/mo + AI | $3,500/mo | Launch voice assistant |
| **EOY 2027 (Scale)** | $400-500/mo + AI | $15,000+/mo | Profitable SaaS |

---

**Recommendation: You're in great shape cost-wise. Focus on growth, not optimization. Costs won't be a problem until revenue is.**

Any questions on specific services or cost drivers?

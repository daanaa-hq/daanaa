# AI Platform Assistant — Proposal & Architecture

**Date:** 2026-07-22  
**Concept:** Scoped AI agent that DOES things on the platform, not a general chatbot  
**Status:** Concept (pre-build)

---

## The Insight

**Problem You're Solving:**
- Users want an AI assistant, but you can't support a general-purpose AI they use for anything
- Creating an open chatbot = infinite support surface
- But restricting it to "only answer questions" = not as useful as it could be

**Solution:**
- Build an **autonomous action agent** for the platform only
- Users can ask it to DO things (create events, approve hours, find orgs)
- Not a general AI — explicitly scoped to Daanaa operations
- Multi-modal: text chat + voice (phone number)
- Clear boundary: "I help you on Daanaa, not with other questions"

**Why This Works:**
1. ✅ **Scope is clear** — "I'm a Daanaa assistant, not a general AI"
2. ✅ **Liability is bounded** — Only platform actions possible
3. ✅ **Value is tangible** — Users can accomplish real work via voice/text
4. ✅ **Support is manageable** — Only help with platform bugs, not AI reasoning
5. ✅ **Differentiation is strong** — No other nonprofit platform has this

---

## What It Looks Like

### Voice Example (Phone Call)

```
User: Calls +1-844-DAANAA-1

AI: "Hi! I'm Daanaa Assistant. I help nonprofits and donors use the 
    platform via voice or text. What can I help you with today?"

User: "I need to create a volunteer event for Saturday at 2pm"

AI: "I can help! Tell me:
     - Event title?
     - Location?
     - How many hours is it?
     - What should volunteers do?"

User: "Beach cleanup, Ocean Beach, 3 hours, remove trash and clean up"

AI: "Got it. Creating a volunteer event:
     Title: Beach Cleanup
     Date: Saturday, 2:00 PM
     Location: Ocean Beach
     Hours: 3
     Task: Remove trash and clean up
     
     Ready to create? (Say yes or no)"

User: "Yes"

AI: "Done! Event created. Here's your QR code link: [URL]
     You can share this with volunteers, or I can text it to you."

User: "Text it"

AI: "Sent! You can now find it in your Daanaa dashboard too."
```

### Text Example (Web Chat)

```
User: "How many volunteer hours are pending approval?"

AI: "You have 12 hours pending from 3 volunteers:
    - Sarah: 4 hours (logged Sunday)
    - Marcus: 5 hours (logged Tuesday)
    - Elena: 3 hours (logged Wednesday)
    
    Would you like me to approve any of these?"

User: "Approve Sarah and Marcus"

AI: "Approving 9 hours for Sarah and Marcus... Done! 
     They'll see their hours counted in the public impact now.
     Elena's 3 hours still waiting for your review."
```

### Donor Example (Voice)

```
User: Calls +1-844-DAANAA-1

AI: "Hi! I'm Daanaa Assistant. I help you find organizations and 
    manage your giving. What are you interested in?"

User: "Show me environmental nonprofits near me that need donations"

AI: "I found 14 environmental nonprofits in your area. Top matches:
    1. Bay Area Coastal Alliance - restoring wetlands (88 Financial Health)
    2. Urban Gardeners Collective - community food security (82)
    3. Green City Coalition - air quality monitoring (79)
    
    Want details on any of these? Or should I add them to your wallet?"

User: "Add all three to my wallet"

AI: "Done! All three added. You can compare them in your Daanaa wallet,
     or head to any one to donate. Need anything else?"
```

---

## Capability Matrix

### What the AI CAN Do (Scoped)

**Nonprofits:**
- ✅ "How many approvals are pending?"
- ✅ "Create a volunteer event"
- ✅ "Approve these volunteer hours"
- ✅ "What's my profile completeness?"
- ✅ "Update my mission statement to..."
- ✅ "Export my report"
- ✅ "Show me recent feedback"
- ✅ "Send the QR code to my phone"

**Donors:**
- ✅ "Find environmental nonprofits in my area"
- ✅ "Show me high-health nonprofits"
- ✅ "Add these 5 to my wallet"
- ✅ "Compare these two organizations"
- ✅ "What's their donation link?"
- ✅ "Send me this organization's details"

**Everyone:**
- ✅ "How do I approve volunteer hours?"
- ✅ "What does financial health mean?"
- ✅ "How do I create an event?"
- ✅ "Show me my dashboard"

### What the AI CANNOT Do (Clear Boundary)

- ❌ General questions ("What's the capital of France?")
- ❌ Medical/legal advice
- ❌ Financial advice beyond the platform
- ❌ Access other users' data (privacy wall)
- ❌ Modify other organizations' profiles
- ❌ Delete data
- ❌ Make donations (hand-off only)

**Exact Response:**
> "I'm specifically built to help with the Daanaa platform. I can't answer 
> general questions or give advice outside of Daanaa. Is there something 
> I can help you with on the platform?"

---

## Architecture

### Tech Stack

```
User (Phone or Web)
        ↓
  Twilio (voice) / Web Chat (text)
        ↓
   Authentication (phone # or OAuth)
        ↓
   Claude API (function calling)
        ↓
   Platform Agent (router)
        ↓
   Safe Action Executor (guardrails)
        ↓
   Daanaa API (read/write actions)
        ↓
   Audit Trail (all AI actions logged)
```

### Key Components

**1. Voice Interface (Twilio)**
- Dedicated phone number: +1-844-DAANAA-1
- IVR: "Say what you need, or press 1 for more options"
- Speech-to-text (Twilio built-in)
- Text-to-speech for responses
- Session management (user verification on first call)

**2. Natural Language Agent (Claude API)**
- Function calling: Understand user intent
- Route to correct action (read data, write data, search, etc.)
- Clarifying questions if ambiguous
- Confirmation before destructive actions

**3. Permission Layer**
- Verify user owns/can access the resource
- Nonprofit can only approve their own hours
- Donor can only modify their own wallet
- Admin actions require explicit auth

**4. Safety Guardrails**
- Rate limiting: 10 requests/min per user
- Scope limiting: Only platform actions
- Action limitations: Require confirmation for writes
- Audit trail: Every AI action logged
- Fallback: Hand off to human support if needed

**5. Audit Trail**
```
{
  timestamp: 2026-07-22T14:30:00Z,
  user_id: 123456,
  user_type: "nonprofit",
  ai_request: "Approve volunteer hours for Sarah",
  ai_interpreted: {action: "approve_hours", volunteer: "Sarah", hours: 4},
  action_taken: "hours_approved",
  result: "success",
  side_effects: ["impact_logged", "email_sent"]
}
```

---

## Implementation Phases

### Phase 1: Text-Based Nonprofit Assistant (2-3 weeks)

**What ships:**
- Web chat widget on nonprofit dashboard
- Nonprofit can ask: "How many approvals pending?"
- Simple Q&A about platform features
- Link to FAQ if question too complex

**Tech:**
- React component for chat UI
- Claude API with function calling
- Read-only access to nonprofit data

**Launch criteria:**
- ✅ Can answer common questions
- ✅ Doesn't make mistakes
- ✅ Graceful fallback to human support

---

### Phase 2: Nonprofit Action Agent (3-4 weeks)

**What ships:**
- "Create an event" voice command (via chat first, then voice)
- "Approve hours" via text
- "Export report" automation
- Confirmation required for all writes

**Tech:**
- Function calling to existing API endpoints
- Permission layer (user can only act on their org)
- Confirmation UI ("Click OK to approve 5 hours")

---

### Phase 3: Voice Interface (4-5 weeks)

**What ships:**
- Twilio phone number (+1-844-DAANAA-1)
- Speech-to-text → Claude → Text-to-speech
- Full nonprofit workflow (create event, check approvals, etc.)
- Session management (repeat callers recognized)

**Tech:**
- Twilio integration
- WebRTC for voice handling
- Caching for returning users ("Remember my timezone")

---

### Phase 4: Donor Assistant (2-3 weeks)

**What ships:**
- "Find environmental nonprofits in my area"
- "Add to wallet" voice
- "Compare these orgs"
- "What's their mission?"

---

### Phase 5: Advanced Features (After Launch)

- Voice mailbox (leave message → AI calls back with answer)
- SMS option (text +1-844-DAANAA-2 for commands)
- Proactive notifications ("You have 5 approvals waiting")
- Learning (remember preferences, previous questions)

---

## Risk Mitigation

### "People Use It as Their Personal AI"

**Prevention:**
```
User: "What's a good diet?"
AI: "I'm the Daanaa Platform Assistant. I help with nonprofit management 
    and finding organizations to support. I can't help with general questions.
    
    Is there something I can help with on Daanaa?"
```

**Hard boundary:** Every response includes scope reminder if off-topic.

### "It Hallucinates Platform Features"

**Prevention:**
- Claude function calling only calls known endpoints
- If action not in capability matrix → "I don't have that feature yet"
- No speculation ("I think you can...") — only confirmed features

### "It Makes Mistakes & We Get Support Tickets"

**Prevention:**
- All writes require confirmation ("Click OK to approve")
- Audit trail of all AI actions
- Easy rollback (user can undo via dashboard)
- Clear disclaimer: "I'm still learning"

### "Liability: User Thinks It's Official Advice"

**Prevention:**
```
Example: User asks "What's a good nonprofit to give to?"
AI: "I can show you Daanaa's search tools to find nonprofits by 
    mission, location, or financial health. But I can't recommend 
    specific organizations — that's your decision."
```

Clear: Daanaa provides tools, AI helps navigate, user decides.

---

## Success Metrics

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Incident Rate** | <1% of AI actions need rollback | Reliability |
| **Scope Compliance** | 100% off-topic responses handled correctly | Boundary holding |
| **User Satisfaction** | 4.2+ stars on "Was this helpful?" | Utility |
| **Adoption** | 20%+ of nonprofits use voice/chat monthly | Traction |
| **Support Load** | +0% (no net increase in support tickets) | Cost neutral |

---

## Comparison: What This ISN'T

| This Isn't | This IS |
|-----------|---------|
| General chatbot (ChatGPT-like) | Platform-specific agent (Daanaa operations only) |
| Responsible for user questions | Responsible for platform bugs only |
| Open-ended AI | Scoped action executor |
| "Ask me anything" | "Ask me about Daanaa" |
| Liability nightmare | Bounded, auditable, reversible |

---

## Stewardship Alignment

| Principle | How It Applies |
|-----------|----------------|
| #2 Privacy | Phone # verified, no tracking, session-local only |
| #3 Trust signals | "I'm an AI assistant" disclosed clearly |
| #5 No weaponizing | Strictly nonprofit-facing, not pushing users |
| #6 Quick corrections | Audit trail lets users undo AI actions |
| #9 Explainable | Every action logged, every decision traceable |
| #10 AI tool not replacement | Explicit: "I help you use Daanaa, you decide" |

---

## The Ask

Before we build, clarify scope:

1. **Voice Priority?** Start with text chat, add voice after? Or prioritize phone?
2. **First Users?** Build for nonprofits first (high value, clear actions) or donors?
3. **Budget?** Twilio + Claude API costs ~$200-500/month depending on scale
4. **Timeline?** Phase 1 (text chat) is 2-3 weeks. Okay?
5. **Tone?** Friendly/casual? Professional? Emoji-heavy?

---

## Why This Works for Daanaa

1. **Accessibility** — Voice is more accessible than UI (great for older nonprofits)
2. **Differentiation** — No other nonprofit platform has autonomous voice agent
3. **Retention** — "I did X with Daanaa assistant" is stickier than browsing
4. **Scale** — One agent handles 1000s of users, 1 team to maintain
5. **Stewardship** — Bounded, auditable, reversible = trustworthy

---

**Next Step:** Would you like to start with Phase 1 (text chat), or research full voice setup first?

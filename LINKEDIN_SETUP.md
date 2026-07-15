# LinkedIn API Setup — Autonomous Posting

## One-Time Setup (30 minutes)

### Step 1: Register Daanaa App on LinkedIn

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Click "Create app"
3. Fill in:
   - App name: `Daanaa Social Manager`
   - LinkedIn page: Daanaa company page
   - App logo: Daanaa icon
   - Legal agreement: Accept
4. Click "Create app"

### Step 2: Get Credentials

In your new app:
1. Go to "Auth" tab
2. Copy: **Client ID**
3. Copy: **Client Secret**
4. Under "Authorized redirect URLs", add: `http://localhost:8000/oauth/linkedin/callback`

### Step 3: Get Access Token

Run this once to authenticate:

```bash
source ~/meritgiving/venv/bin/activate
python3 scripts/linkedin_auth.py \
  --client-id <YOUR_CLIENT_ID> \
  --client-secret <YOUR_CLIENT_SECRET>
```

This will:
1. Open a browser to LinkedIn's auth page
2. Ask you to authorize Daanaa
3. Return an **access token** and **refresh token**
4. Save them to `.env` automatically

### Step 4: Verify Setup

```bash
python3 scripts/linkedin_poster.py --verify
```

Should output: `✓ LinkedIn connection verified`

---

## Auto-Posting Workflow

Once credentials are set:

```
Weekly Theme Approved ──→ Carousel Built ──→ Post to LinkedIn
Comment Generated ────→ High Confidence ──→ Auto-Post (85%+)
```

### What Happens Automatically

1. **Every Monday**: AI curates theme → You approve → Carousel posts to LinkedIn
2. **Throughout week**: High-confidence comments auto-post
3. **Real-time**: Engagement metrics synced back to dashboard

### What Requires Your Decision

- ✓ Theme approval (before carousel creation)
- ✓ Comment review (before posting)
- ✓ Optional: edit + manually post in LinkedIn (if you want tweaks)

---

## Environment Variables Required

```bash
export LINKEDIN_CLIENT_ID="your-client-id"
export LINKEDIN_CLIENT_SECRET="your-client-secret"
export LINKEDIN_ACCESS_TOKEN="auto-refreshed"
export LINKEDIN_REFRESH_TOKEN="auto-refreshed"
export LINKEDIN_ORG_URN="urn:li:organization:YOUR-ORG-ID"
```

Get your org ID:
```bash
curl -H "Authorization: Bearer $LINKEDIN_ACCESS_TOKEN" \
  https://api.linkedin.com/v2/me | jq '.id'
```

---

## Troubleshooting

**"401 Unauthorized"** → Token expired → Auto-refreshes, try again in 30 sec

**"403 Forbidden"** → Org not authorized → Check app permissions + redirect URLs

**"Rate limited"** → LinkedIn limits posts per app → Queue and retry (handled automatically)

---

## Next: Test Live

Once verified:

```bash
# Test posting a carousel
python3 scripts/linkedin_poster.py --test-carousel

# Test posting a comment  
python3 scripts/linkedin_poster.py --test-comment
```

Both will post to LinkedIn with `[TEST]` prefix — you can delete them.

---

## Deployment

LinkedIn auto-posting is **live** as soon as credentials are set. No restarts needed.

To disable: Unset `LINKEDIN_ACCESS_TOKEN` environment variable.

To revert a post: Delete manually in LinkedIn (API doesn't support deletion for security).

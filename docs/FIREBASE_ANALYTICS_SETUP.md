# Firebase Analytics Setup for Phase 3 Measurement

**Frontend code ready:** ✅ (commit 24f6077aeb1)  
**What's needed:** Your login to Firebase Console to enable Analytics

---

## Step 1: Enable Google Analytics in Firebase Project

1. Go to **Google Cloud Console** → https://console.cloud.google.com/
2. Select your Firebase project (from VITE_FIREBASE_PROJECT_ID in `.env`)
3. Left sidebar → **Analytics** (or search for "Analytics")
4. Click **Get Started** → **Create Analytics Account**
   - Organization: Leave as suggested
   - Account name: `Daanaa` (or any name)
   - Data sharing: Default is fine (uncheck if privacy-sensitive)
   - Click **Create**

5. Firebase will create a **Google Analytics property** and link it to your Firebase project
   - This takes ~1-2 minutes
   - You'll see a **Measurement ID** (format: `G-XXXXXXXXXX`)

---

## Step 2: Verify Firebase Console Shows Events

1. After Analytics is enabled, go back to **Firebase Console** → https://console.firebase.google.com/
2. Select your project
3. Left sidebar → **Analytics** → **Realtime**
4. (This will be empty until you deploy + visit the site, but confirms setup is wired)

---

## Step 3: Deploy Frontend to Droplet

Once Analytics is enabled in Firebase, deploy the new frontend code:

```bash
cd ~/meritgiving/frontend && npm run build
rsync -az --delete dist/ root@162.243.97.179:/opt/daanaa/frontend/dist/ \
  -e "ssh -i ~/.ssh/daanaa_do"
ssh -i ~/.ssh/daanaa_do root@162.243.97.179 'systemctl restart daanaa'
```

Verify:
```bash
curl -s https://daanaa.org/ | grep -i firebase | head -2
# Should see Firebase SDK loading
```

---

## Step 4: Test Event Tracking

Visit https://daanaa.org and:

1. **Find an org** (e.g., https://daanaa.org/org/264837170)
2. Scroll down to see **At a Glance** section
3. Open **Browser DevTools** → **Console** tab
4. Look for Firebase initialization messages
5. Go to **Network** tab → Filter `firebaselogging.googleapis.com` or `analytics.google.com`
6. You should see event POST requests

---

## Step 5: Verify Events in Firebase Analytics Dashboard

1. **Firebase Console** → **Analytics** → **Realtime**
2. You should see live events streaming in within 30 seconds of visiting
3. Events will show as:
   - `atagla nce_visible` (when you scroll to At a Glance)
   - `org_detail_bookmark` (when you click bookmark heart)
   - `search_filter_context` (when applicable)

---

## Events Dashboard (Where to View Data)

### Real-time Events
**Firebase Console** → **Analytics** → **Realtime**
- Shows live events as they happen
- Good for sanity-checking during setup

### Custom Events Report
**Firebase Console** → **Analytics** → **Reports** → **Custom Events**
- Shows aggregated event counts over time
- Segment by `org_size` (Micro/Professional/Established)
- Segment by `section` (at_a_glance, etc.)

### Key Metric: Small Org CTR
To measure if Phase 3 helps small orgs, you'll need:
- Count of `org_detail_bookmark` events where `org_size = 'Micro'`
- Compare Week 1 (Aug 10-16) vs. baseline (Aug 2-8)
- Target: +30% improvement = Phase 3 Wins

---

## Baseline Metrics (Aug 2-8)

Before we start measurement, you'll need to capture pre-Phase-3 data:

1. Go to **Firebase Analytics** → **Custom Events**
2. Filter by `org_detail_bookmark` event
3. Date range: **Aug 2-8, 2026**
4. Screenshot or note:
   - Total event count (all org sizes)
   - If possible, filter by `org_size = 'Micro'` and count separately

Save these numbers as **baseline**. We'll compare Week 1 (Aug 10-16) against this.

---

## Troubleshooting

### Events not appearing in Firebase?

**Check 1: Frontend deployed?**
```bash
curl -s https://daanaa.org/ | grep "firebase"
```
Should show Firebase SDK loading. If not, redeploy frontend.

**Check 2: Analytics enabled in Firebase?**
- Go to **Firebase Console** → **Project Settings** → **General** tab
- Scroll down to see if Google Analytics is linked (will show "Google Analytics account: [Name]")

**Check 3: Analytics account created?**
- Go to https://analytics.google.com/
- Login as the same Google account
- You should see your Firebase project listed with a **Measurement ID** (G-XXXXXXXXXX)

**Check 4: Browser DevTools**
- **Console:** Look for Firebase warnings or errors
- **Network:** Search for `firebaselogging.googleapis.com` — should see event POSTs

---

## Privacy & Data

Firebase Analytics automatically:
- ✅ Anonymizes IP addresses
- ✅ Does NOT track PII (we only send org-level properties)
- ✅ Aggregates events server-side (not stored per-user)
- ✅ Complies with Stewardship P2 (privacy-first)

See PRIVACY-INVARIANTS.md for details.

---

## Next Steps

1. ✅ Frontend code ready (commit 24f6077aeb1)
2. ⏳ **YOUR TURN:** Enable Analytics in Firebase Console (5 min)
3. ⏳ **YOUR TURN:** Deploy frontend to droplet (5 min)
4. ✅ Verify events firing (browser DevTools check, 5 min)
5. ✅ Capture baseline metrics (Aug 2-8 data, 5 min)
6. ✅ Start measurement (Gate A.1 daily pulse checks, Aug 10-16)

---

## Questions?

- **Firebase setup stuck?** Check your Google Cloud project; make sure billing is enabled
- **Events not tracking?** Enable Realtime Events dashboard; should see data flow in ~30s
- **Privacy concern?** Firebase analytics are aggregated; see PRIVACY-INVARIANTS.md

**Tell me when you've enabled Analytics in Firebase Console — I'll guide you through deployment.**

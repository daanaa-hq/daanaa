# QA Testing Hub - Access Guide

**Status:** ✅ Ready for Testing (July 22, 2026)

---

## 🎯 Quick Access

### Option 1: Local Server (Recommended)
The QA hub is set up on your local development server with all documents and forms ready.

**Location:** `/home/akbar/meritgiving/qa_server/`

**Files included:**
- `index.html` - Main QA hub with navigation
- `tests/` - All test documents
  - `QA_CREDENTIALS.txt`
  - `QA_TEST_CHECKLIST.txt`
  - `QA_MANUAL_TESTS.md`
  - `QA_TEST_2026_07_22.sh`
- `reports/` - Report submission
  - `submit.html` - Online form
  - `QA_REPORT_TEMPLATE.txt` - Text template

---

## 📋 How QA Team Gets Access

### For Local/Internal QA:
1. Download from: `/home/akbar/meritgiving/qa_server/`
2. Or clone/share the repo
3. Open `qa_server/index.html` in browser

### For Remote/External QA:
**Share via:**

**Option A: Direct File Download**
```bash
# Share via secure link or email:
# http://your-server:8000/qa_server/
# (requires python -m http.server running)

python3 -m http.server 8000 --directory /home/akbar/meritgiving/qa_server/
```
Then give QA team: `http://your-ip:8000/`

**Option B: Zip Archive**
```bash
cd /home/akbar/meritgiving
zip -r qa_testing_hub.zip qa_server/
# Send qa_testing_hub.zip to QA team
# They unzip and open index.html locally
```

**Option C: Document Sharing**
Print/email individual files:
- `QA_CREDENTIALS.txt` (quick reference)
- `QA_TEST_CHECKLIST.txt` (printable form)
- `QA_MANUAL_TESTS.md` (detailed guide)

---

## ✅ What QA Team Needs

### Essential:
1. **Login Credentials**
   - Email: `test@testnonprofit.org`
   - Password: `TestNonprofit2024!`
   - Website: `https://daanaa.org`

2. **Test Documents** (pick one approach):
   - Quick: `QA_CREDENTIALS.txt` (5-10 min)
   - Standard: `QA_TEST_CHECKLIST.txt` (50 min)
   - Detailed: `QA_MANUAL_TESTS.md` (2-3 hours)
   - Automated: `QA_TEST_2026_07_22.sh` (technical)

3. **Report Submission**
   - Fill `QA_REPORT_TEMPLATE.txt`
   - Or use `reports/submit.html` web form
   - Email to: `qa@daanaa.org`

---

## 🚀 Setup Instructions for QA Team

### Quick Setup (5 minutes)

**Step 1: Get the files**
```bash
# Option A: Download zip
unzip qa_testing_hub.zip
cd qa_server

# Option B: Clone repo
git clone <repo-url>
cd meritgiving/qa_server
```

**Step 2: Open the hub**
```bash
# Open in browser
open index.html  # macOS
start index.html # Windows
xdg-open index.html # Linux
```

**Step 3: Download test docs**
- Click links to download individual documents
- Print `QA_TEST_CHECKLIST.txt` for offline testing

**Step 4: Start testing**
- Use credentials: `test@testnonprofit.org` / `TestNonprofit2024!`
- Visit: `https://daanaa.org`
- Follow test scenarios from your chosen document

**Step 5: Submit results**
- Fill out `QA_REPORT_TEMPLATE.txt`
- Or submit via online form: `reports/submit.html`
- Email to: `qa@daanaa.org`

---

## 📊 Test Coverage

**19 Total Tests** organized in 4 categories:

| Category | Tests | Time |
|----------|-------|------|
| Donor Discovery | 5 | 15 min |
| Nonprofit Staff | 6 | 20 min |
| UX & Performance | 5 | 10 min |
| Trust & Security | 3 | 5 min |

---

## 🎯 Success Criteria

- ✅ **100% Pass** = Ready for production
- ✅ **90%+ Pass** = Minor issues only
- ⚠️ **80-89% Pass** = Needs fixes
- ❌ **<80% Pass** = Blocking issues

---

## 📞 Support

**QA Team Questions:**
- `QA_MANUAL_TESTS.md` - detailed guide
- `QA_CREDENTIALS.txt` - quick reference

**Technical Issues:**
- Contact: `dev@daanaa.org`
- Include: browser, OS, screenshot, steps to reproduce

---

## 📁 File Structure

```
qa_server/
├── index.html                    # Main hub (start here)
├── tests/
│   ├── QA_CREDENTIALS.txt       # 1-page quick ref
│   ├── QA_TEST_CHECKLIST.txt    # 2-page printable form
│   ├── QA_MANUAL_TESTS.md       # 8-page detailed guide
│   └── QA_TEST_2026_07_22.sh    # Automated tests
└── reports/
    ├── submit.html              # Online report form
    └── QA_REPORT_TEMPLATE.txt   # Text report template
```

---

## ✨ Features

✅ **Offline Access** - All files work without internet  
✅ **Printable** - Formats optimized for printing  
✅ **Mobile-Friendly** - Works on phones/tablets  
✅ **No Jargon** - Plain language for non-technical QA  
✅ **Self-Contained** - Everything in one directory  

---

**Created:** July 22, 2026  
**Status:** Production Ready  
**Pass Rate Target:** 100% (21/21 tests)

#!/usr/bin/env python3
import requests, json, sys

BASE = "http://127.0.0.1:8081"
ERRORS = []
WARNINGS = []

def check(name, url, expect_html=False):
    try:
        headers = {"Accept": "text/html"} if expect_html else {}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            ERRORS.append(f"{name}: HTTP {r.status_code}")
            return None
        return r
    except Exception as e:
        ERRORS.append(f"{name}: {e}")
        return None

# 1. Health
r = check("Health", f"{BASE}/health")
if r:
    data = r.json()
    print(f"✅ Orgs: {data.get('orgs')} | Categories: {data.get('categories')} | Impact: {data.get('MERIT_scored')}")
    if data.get('orgs', 0) < 40000:
        WARNINGS.append(f"Low org count: {data.get('orgs')}")

# 2. Homepage HTML
r = check("Homepage", f"{BASE}/", expect_html=True)
if r:
    html = r.text
    if "Every nonprofit" not in html:
        ERRORS.append("Homepage missing hero text")
    if "MERIT" not in html:
        ERRORS.append("Homepage missing brand")
    if len(html) < 1000:
        WARNINGS.append("Homepage HTML seems short")
    else:
        print("✅ Homepage renders")

# 3. Search
r = check("Search API", f"{BASE}/search?q=houston")
if r:
    data = r.json()
    print(f"✅ Search returned {data.get('count')} results")
    if data.get('count', 0) == 0:
        WARNINGS.append("Search returned 0 results for 'houston'")

# 4. Search HTML
r = check("Search HTML", f"{BASE}/search?q=houston", expect_html=True)
if r and "Search Results" not in r.text:
    ERRORS.append("Search HTML missing title")

# 5. Categories API
r = check("Categories API", f"{BASE}/categories")
if r:
    data = r.json()
    print(f"✅ Categories: {data.get('count')} groups")

# 6. Categories HTML
r = check("Categories HTML", f"{BASE}/categories", expect_html=True)
if r and "Browse by Category" not in r.text:
    ERRORS.append("Categories HTML missing title")

# 7. Category X
r = check("Category X", f"{BASE}/category/X")
if r:
    data = r.json()
    print(f"✅ Category X: {data.get('count')} orgs")
    if data.get('count', 0) == 0:
        WARNINGS.append("Category X is empty")

# 8. Category X HTML
r = check("Category X HTML", f"{BASE}/category/X", expect_html=True)
if r and "Religion" not in r.text:
    WARNINGS.append("Category X HTML missing 'Religion' name")

# 9. Org Detail API
r = check("Org API", f"{BASE}/org/741157373")
if r:
    data = r.json()
    profile = data.get('profile', {})
    print(f"✅ Org detail: {profile.get('name')}")
    if not profile.get('name'):
        ERRORS.append("Org detail missing name")

# 10. Org Detail HTML
r = check("Org HTML", f"{BASE}/org/741157373", expect_html=True)
if r:
    html = r.text
    if "MERIT Score" not in html:
        ERRORS.append("Org HTML missing MERIT Score")
    if "score-ring" not in html:
        WARNINGS.append("Org HTML missing score ring visualization")
    else:
        print("✅ Org profile renders with MERIT score")

# 11. Test a few more orgs for ProPublica enrichment
test_eins = ["931149996", "10143485", "270843775"]
for ein in test_eins:
    r = check(f"Org {ein}", f"{BASE}/org/{ein}")
    if r:
        data = r.json()
        pp = data.get('propublica')
        if pp and pp.get('organization'):
            print(f"✅ Org {ein}: ProPublica enriched")
        else:
            WARNINGS.append(f"Org {ein}: No ProPublica data")

# 12. Test random orgs for 404s
import random
eins = list(requests.get(f"{BASE}/health").json().keys()) if False else []
# Just test a known bad EIN
r = requests.get(f"{BASE}/org/999999999", timeout=5)
if r.status_code == 404:
    print("✅ 404 handling works")
else:
    WARNINGS.append(f"Bad EIN returned {r.status_code} instead of 404")

print("\n" + "="*50)
if ERRORS:
    print(f"❌ ERRORS ({len(ERRORS)}):")
    for e in ERRORS:
        print(f"   - {e}")
else:
    print("✅ NO CRITICAL ERRORS")

if WARNINGS:
    print(f"⚠️  WARNINGS ({len(WARNINGS)}):")
    for w in WARNINGS:
        print(f"   - {w}")
else:
    print("✅ NO WARNINGS")

print("="*50)
if ERRORS:
    print("🔴 NOT READY FOR BOARD")
    sys.exit(1)
elif WARNINGS:
    print("🟡 READY WITH CAVEATS")
else:
    print("🟢 FULLY READY FOR BOARD")

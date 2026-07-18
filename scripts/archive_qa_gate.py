#!/usr/bin/env python3
"""
Archive QA Gate — Verify promoted orgs meet quality standards before live visibility.
Checks: name coherence, mission quality, website validity, and Stewardship principle compliance.

Run after promotion, before database sync:
  python3 archive_qa_gate.py --verify-batch <json_file>
"""

import json
import sys
import re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent

class QAGate:
    """Quality assurance validator for promoted orgs."""

    def __init__(self):
        self.results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'issues': defaultdict(list),
            'redflags': []
        }

    def check_name(self, org):
        """Verify organization name is coherent and not obviously corrupted."""
        name = org.get('organization_name', '')
        if not name or len(name) < 3:
            self.results['issues']['empty_name'].append(org.get('EIN'))
            return False

        # Check for obviously corrupted patterns
        bad_patterns = [
            r'^[\s\-_]+$',  # Only whitespace/punctuation
            r'[0-9]{10,}',  # Excessive digits (likely OCR errors)
            r'[^\w\s\-\'\(\)]',  # Weird unicode/symbols
        ]

        for pattern in bad_patterns:
            if re.search(pattern, name):
                self.results['issues']['corrupted_name'].append(name[:50])
                return False

        return True

    def check_mission(self, org):
        """Verify mission statement exists and is reasonable."""
        mission = org.get('mission', '')
        source = org.get('mission_source', '')

        if not mission:
            self.results['issues']['missing_mission'].append(org.get('EIN'))
            return False

        if len(mission) < 10:
            self.results['issues']['mission_too_short'].append(mission)
            return False

        if len(mission) > 5000:
            self.results['issues']['mission_too_long'].append(org.get('EIN'))
            return False

        # AI-generated missions should be labeled
        if source == 'ai_generated' and not org.get('mission_confidence'):
            self.results['issues']['unlabeled_ai_mission'].append(org.get('EIN'))

        return True

    def check_website(self, org):
        """Verify website recovery has high match quality."""
        website = org.get('website')
        website_status = org.get('website_status')
        match_quality = org.get('website_match_quality', 0)

        if not website:
            # Website can be absent for small orgs with no web presence — not a fail
            return True

        # If website is present, it should have good metadata
        if match_quality < 0.5:
            self.results['issues']['low_website_match'].append(
                f"{org.get('EIN')}: match={match_quality}"
            )
            return False

        if website_status not in ['active', 'archived', 'unknown']:
            self.results['issues']['invalid_website_status'].append(website_status)
            return False

        return True

    def check_donation_link(self, org):
        """Verify donation links are verified if present."""
        donate_url = org.get('donate_url')
        donate_confidence = org.get('donate_confidence', 0)

        if not donate_url:
            return True  # Optional field

        # If donation link present, confidence should be reasonable
        if donate_confidence < 50:
            self.results['issues']['low_donate_confidence'].append(
                f"{org.get('EIN')}: confidence={donate_confidence}"
            )
            return False

        # Verify URL format
        if not donate_url.startswith(('http://', 'https://')):
            self.results['issues']['invalid_donate_url'].append(donate_url[:50])
            return False

        return True

    def check_stewardship_principles(self, org):
        """Verify org meets Stewardship Principles."""
        # P3: Trust signals must be evidence-based
        if not org.get('organization_name'):
            self.results['redflags'].append(
                f"P3: {org.get('EIN')} missing name (not evidence-based)"
            )
            return False

        # P4: Small orgs treated fairly
        revenue = org.get('total_revenue', 0)
        has_mission = bool(org.get('mission'))
        has_website = bool(org.get('website'))

        if revenue < 50000 and not has_mission:
            # Small orgs with no mission description — risky
            self.results['issues']['small_org_no_mission'].append(org.get('EIN'))

        # P9: Decisions should be explainable
        website_source = org.get('website_source')
        if not website_source and org.get('website'):
            self.results['issues']['undocumented_website_source'].append(org.get('EIN'))
            return False

        return True

    def validate(self, org):
        """Run all checks on a single org."""
        self.results['total'] += 1

        checks = [
            ('name', self.check_name),
            ('mission', self.check_mission),
            ('website', self.check_website),
            ('donation_link', self.check_donation_link),
            ('stewardship', self.check_stewardship_principles),
        ]

        all_passed = True
        for check_name, check_func in checks:
            try:
                if not check_func(org):
                    all_passed = False
            except Exception as e:
                self.results['issues'][f'error_{check_name}'].append(
                    f"{org.get('EIN')}: {str(e)}"
                )
                all_passed = False

        if all_passed:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1

        return all_passed

    def report(self):
        """Generate QA report."""
        print("\n" + "=" * 70)
        print("🔐 ARCHIVE QA GATE — Promoted Orgs Quality Verification")
        print("=" * 70)
        print()

        print(f"Total checked: {self.results['total']:,}")
        print(f"Passed: {self.results['passed']:,} ({100*self.results['passed']/max(1, self.results['total']):.1f}%)")
        print(f"Failed: {self.results['failed']:,}")
        print()

        if self.results['issues']:
            print("⚠️  ISSUES FOUND")
            for issue_type, orgs in sorted(self.results['issues'].items()):
                print(f"  • {issue_type}: {len(orgs)}")
                for org in orgs[:3]:  # Show first 3
                    print(f"    - {org}")
                if len(orgs) > 3:
                    print(f"    ... and {len(orgs)-3} more")
            print()

        if self.results['redflags']:
            print("🚩 STEWARDSHIP RED FLAGS")
            for flag in self.results['redflags'][:5]:
                print(f"  • {flag}")
            print()

        print("=" * 70)

def verify_batch(json_file):
    """Verify a batch of promoted orgs from JSON."""
    try:
        with open(json_file) as f:
            orgs = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {json_file}: {e}")
        return False

    gate = QAGate()
    for org in orgs:
        gate.validate(org)

    gate.report()

    # Return success if pass rate is high enough
    pass_rate = gate.results['passed'] / max(1, gate.results['total'])
    success = pass_rate >= 0.95 and len(gate.results['redflags']) == 0

    if success:
        print("✅ GATE PASSED — Orgs approved for promotion")
    else:
        print("❌ GATE FAILED — Review issues before promoting")

    return success

if __name__ == '__main__':
    if '--verify-batch' in sys.argv:
        idx = sys.argv.index('--verify-batch')
        if idx + 1 < len(sys.argv):
            json_file = sys.argv[idx + 1]
            success = verify_batch(json_file)
            sys.exit(0 if success else 1)
        else:
            print("Usage: archive_qa_gate.py --verify-batch <json_file>")
            sys.exit(1)
    else:
        print("Usage: archive_qa_gate.py --verify-batch <json_file>")
        sys.exit(1)

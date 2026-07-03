"""
Daanaa LinkedIn Poster
-----------------------
Logs into LinkedIn as the Daanaa company page and posts a carousel PDF.

First run (session setup):
  python3 linkedin_poster.py --setup

Subsequent runs:
  python3 linkedin_poster.py --pdf output/daanaa_hidden_gems_20260702_1536.pdf \
      --caption "The nonprofits nobody talks about..."

Or run the full pipeline (generate + post) via post_carousel.py.

Credentials are read from env vars — never hardcoded:
  LINKEDIN_EMAIL
  LINKEDIN_PASSWORD
  LINKEDIN_COMPANY_ID   (the numeric ID from your company page URL)

Session is saved to scripts/linkedin/.session/ so you only log in once.
"""

import argparse
import os
import sys
import time
from pathlib import Path

SESSION_DIR = Path(__file__).parent / ".session"
PLAYWRIGHT_PYTHON = "/home/akbar/merit-pdf-env/bin/python3"


def _get_playwright():
    """Import playwright from the merit-pdf-env."""
    penv = "/home/akbar/merit-pdf-env/lib/python3.12/site-packages"
    if penv not in sys.path:
        sys.path.insert(0, penv)
    from playwright.sync_api import sync_playwright
    return sync_playwright


def setup_session():
    """Open a visible browser for manual login, then save the session."""
    SESSION_DIR.mkdir(exist_ok=True)
    sync_playwright = _get_playwright()

    print("\nOpening LinkedIn for manual login...")
    print("Log in with your personal account (the one that manages the Daanaa page).")
    print("After you're fully logged in and see your LinkedIn feed, press ENTER here.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--no-sandbox"])
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto("https://www.linkedin.com/login")
        input("  [Press ENTER once you are logged in and see your feed] ")
        ctx.storage_state(path=str(SESSION_DIR / "state.json"))
        browser.close()

    print(f"\n  Session saved to {SESSION_DIR / 'state.json'}")
    print("  You won't need to log in again until the session expires (~30 days).\n")


def post_carousel(pdf_path: str, caption: str, company_id: str):
    """Post a carousel PDF to the Daanaa LinkedIn company page."""
    state_file = SESSION_DIR / "state.json"
    if not state_file.exists():
        print("No session found. Run with --setup first.")
        sys.exit(1)

    pdf = Path(pdf_path)
    if not pdf.exists():
        print(f"PDF not found: {pdf_path}")
        sys.exit(1)

    sync_playwright = _get_playwright()

    print(f"\n  Posting carousel: {pdf.name}")
    print(f"  To company page: {company_id}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        ctx = browser.new_context(
            storage_state=str(state_file),
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()

        # Navigate to company page feed
        company_url = f"https://www.linkedin.com/company/{company_id}/admin/posts-activity/"
        print(f"  Navigating to {company_url}")
        page.goto(company_url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # Click "Start a post" / "Create a post"
        print("  Finding post button...")
        post_btn = page.locator(
            "button:has-text('Start a post'), "
            "button:has-text('Create a post'), "
            "[data-control-name='share.sharebox_create_post']"
        ).first
        post_btn.wait_for(timeout=10000)
        post_btn.click()
        time.sleep(1.5)

        # Type the caption
        print("  Entering caption...")
        text_area = page.locator(
            ".ql-editor, [data-placeholder*='talk about'], [aria-label*='Text editor']"
        ).first
        text_area.wait_for(timeout=8000)
        text_area.click()
        text_area.type(caption, delay=20)
        time.sleep(1)

        # Click the "Document" / "Add a document" button
        print("  Uploading document...")
        # Try the media toolbar first
        doc_btn = page.locator(
            "button[aria-label*='ocument'], "
            "button[aria-label*='PDF'], "
            "label[aria-label*='ocument'], "
            "button:has-text('Add a document')"
        ).first
        doc_btn.wait_for(timeout=8000)
        doc_btn.click()
        time.sleep(1)

        # File chooser
        with page.expect_file_chooser() as fc_info:
            # Some LinkedIn versions open a file input directly
            file_input = page.locator("input[type='file']").first
            if file_input.is_visible():
                file_input.set_input_files(str(pdf.resolve()))
            else:
                page.locator("button:has-text('Choose file'), label:has-text('Choose file')").first.click()
        file_chooser = fc_info.value
        file_chooser.set_files(str(pdf.resolve()))
        print("  File selected, waiting for upload...")
        time.sleep(8)  # LinkedIn upload takes a few seconds

        # Add document title if prompted
        title_field = page.locator("input[placeholder*='title'], input[aria-label*='title']").first
        if title_field.is_visible(timeout=2000):
            title_field.fill("Daanaa Nonprofit Insights")
            time.sleep(0.5)
            # Click Done/Next
            page.locator("button:has-text('Done'), button:has-text('Next')").first.click()
            time.sleep(1.5)

        # Post
        print("  Publishing...")
        post_submit = page.locator(
            "button:has-text('Post'), button[aria-label*='Post now']"
        ).last
        post_submit.wait_for(timeout=10000)
        post_submit.click()
        time.sleep(4)

        # Confirm
        if "feed" in page.url or page.locator("text=Your post is being processed").is_visible(timeout=5000):
            print("\n  Posted successfully.")
        else:
            screenshot = SESSION_DIR / "post_result.png"
            page.screenshot(path=str(screenshot))
            print(f"\n  Uncertain outcome. Screenshot saved: {screenshot}")

        browser.close()


def post_text(text: str, company_id: str):
    """Post a plain text update to the Daanaa LinkedIn company page."""
    state_file = SESSION_DIR / "state.json"
    if not state_file.exists():
        print("No session found. Run with --setup first.")
        sys.exit(1)

    sync_playwright = _get_playwright()
    print(f"\n  Posting text update to company page: {company_id}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        ctx = browser.new_context(
            storage_state=str(state_file),
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()

        company_url = f"https://www.linkedin.com/company/{company_id}/admin/posts-activity/"
        page.goto(company_url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        post_btn = page.locator(
            "button:has-text('Start a post'), "
            "button:has-text('Create a post'), "
            "[data-control-name='share.sharebox_create_post']"
        ).first
        post_btn.wait_for(timeout=10000)
        post_btn.click()
        time.sleep(1.5)

        text_area = page.locator(
            ".ql-editor, [data-placeholder*='talk about'], [aria-label*='Text editor']"
        ).first
        text_area.wait_for(timeout=8000)
        text_area.click()
        text_area.type(text, delay=15)
        time.sleep(1)

        post_submit = page.locator(
            "button:has-text('Post'), button[aria-label*='Post now']"
        ).last
        post_submit.wait_for(timeout=10000)
        post_submit.click()
        time.sleep(4)

        if "feed" in page.url or page.locator("text=Your post is being processed").is_visible(timeout=5000):
            print("\n  Posted successfully.")
        else:
            screenshot = SESSION_DIR / "text_post_result.png"
            page.screenshot(path=str(screenshot))
            print(f"\n  Uncertain outcome. Screenshot saved: {screenshot}")

        browser.close()


def main():
    parser = argparse.ArgumentParser(description="Daanaa LinkedIn Poster")
    parser.add_argument("--setup", action="store_true",
                        help="Run interactive login and save session")
    parser.add_argument("--pdf", help="Path to carousel PDF to post")
    parser.add_argument("--caption", help="Post caption text")
    parser.add_argument("--company-id", default=os.getenv("LINKEDIN_COMPANY_ID", "133385169"),
                        help="LinkedIn numeric company ID (default: from env LINKEDIN_COMPANY_ID)")
    args = parser.parse_args()

    if args.setup:
        setup_session()
    elif args.pdf:
        caption = args.caption or (
            "Every year, billions flow to nonprofits — but most donors can only name a handful.\n\n"
            "Not because the others aren't doing important work.\n"
            "Because visibility has always favored name recognition over impact.\n\n"
            "We built Daanaa to change that. 1.7M IRS-recognized nonprofits, free to explore.\n\n"
            "daanaa.org\n\n"
            "#nonprofits #philanthropy #civictech #giving"
        )
        post_carousel(args.pdf, caption, args.company_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

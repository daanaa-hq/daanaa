"""
Daanaa LinkedIn Full Pipeline
------------------------------
One command: generate carousel PDF with LLM → post to LinkedIn company page.

Usage:
  python3 post_carousel.py --type hidden_gems
  python3 post_carousel.py --type sector_insight --context "Food banks in Texas"
  python3 post_carousel.py --type how_it_works --dry-run   # generate only, no post
  python3 post_carousel.py --type hidden_gems --no-llm      # placeholder layout test

Env vars:
  LINKEDIN_COMPANY_ID  (default: 133385169 — Daanaa page)
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT = BASE / "output"
sys.path.insert(0, str(BASE))

import carousel_generator as gen
import linkedin_poster as poster

CAPTIONS = {
    "hidden_gems": (
        "Most donors give to organizations they already know.\n\n"
        "But what about the 33,900 small nonprofits with strong financials and "
        "zero name recognition?\n\n"
        "We found them. Swipe to meet a few. 👇\n\n"
        "daanaa.org — free, no account required\n\n"
        "#nonprofits #philanthropy #hiddenGems #civictech"
    ),
    "how_it_works": (
        "How do you decide which nonprofit to support?\n\n"
        "Most people rely on name recognition or a friend's recommendation. "
        "We think you deserve more context than that.\n\n"
        "Here's how Daanaa works — and why we built it the way we did. 👇\n\n"
        "daanaa.org\n\n"
        "#nonprofits #philanthropy #transparency #civictech"
    ),
    "sector_insight": (
        "Public IRS data tells a different story than most people expect.\n\n"
        "We pulled the numbers. Swipe for what we found. 👇\n\n"
        "daanaa.org — 1.7M nonprofits, free to explore\n\n"
        "#nonprofits #data #philanthropy #IRS990 #civictech"
    ),
    "myth_bust": (
        "The overhead ratio myth is costing nonprofits funding they deserve.\n\n"
        "And it's not the only one. Swipe through the ones we hear most. 👇\n\n"
        "daanaa.org\n\n"
        "#nonprofits #philanthropy #giving #civictech"
    ),
    "feature_launch": (
        "New on Daanaa — and it's free. 👇\n\n"
        "daanaa.org\n\n"
        "#nonprofits #product #civictech #philanthropy"
    ),
}

PLACEHOLDER = {
    "cover_headline": "The nonprofits nobody talks about",
    "cover_sub": "But probably should.",
    "slides": [
        {"label": "The Problem", "headline": "Most giving flows to familiar names",
         "body": "Name recognition drives donations more than impact. Organizations doing the quietest work often have the smallest digital footprint.",
         "accent_stat": "97%", "accent_label": "of U.S. nonprofits have no national brand recognition"},
        {"label": "The Data", "headline": "1.7 million organizations, most invisible",
         "body": "The IRS recognizes 1.7 million 501(c)(3) organizations. The average donor can name fewer than five.",
         "accent_stat": "33,900+", "accent_label": "hidden gems identified by Daanaa"},
        {"label": "What We Found", "headline": "Small does not mean struggling",
         "body": "Many of the healthiest nonprofits by peer financial context score are under $500K in revenue. Lean budgets, strong reserves, direct mission delivery.",
         "accent_stat": "", "accent_label": ""},
        {"label": "An Example", "headline": "A food pantry with no website",
         "body": "One organization in Houston serves 400 families per month, has two years of operating reserves, and has never appeared in a news article. They are on Daanaa.",
         "accent_stat": "", "accent_label": ""},
        {"label": "The Fix", "headline": "Public data, made searchable",
         "body": "Daanaa pulls IRS Form 990 data, benchmarks each org against its peers, and surfaces the ones doing strong work with limited visibility.",
         "accent_stat": "", "accent_label": ""},
        {"label": "Your Move", "headline": "Search before you give this year",
         "body": "You might find an organization three miles away doing exactly the work you care about. Free, no account required.",
         "accent_stat": "", "accent_label": ""},
    ],
    "cta_headline": "The best find is one you discover yourself.",
    "cta_body": "Free. No account needed.\ndaanaa.org",
}


def run(carousel_type: str = "hidden_gems", context: str = "", company_id: str = "133385169") -> tuple[Path, str]:
    """Callable API for scheduler and other scripts. Returns (pdf_path, caption)."""
    fonts = gen.load_fonts()
    content = gen.generate_content(carousel_type, context)
    pages = gen.render_carousel(content, fonts)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    pdf = OUTPUT / f"daanaa_{carousel_type}_{ts}.pdf"
    gen.save_pdf(pages, pdf)
    caption = CAPTIONS.get(carousel_type, CAPTIONS["hidden_gems"])
    poster.post_carousel(str(pdf), caption, company_id)
    return pdf, caption


def find_latest_pdf(carousel_type: str) -> Path | None:
    pdfs = sorted(OUTPUT.glob(f"daanaa_{carousel_type}_*.pdf"), reverse=True)
    return pdfs[0] if pdfs else None


def main():
    parser = argparse.ArgumentParser(description="Daanaa LinkedIn Full Pipeline")
    parser.add_argument("--type", default="hidden_gems",
                        choices=list(gen.PROMPTS.keys()))
    parser.add_argument("--context", default="", help="Extra context for the LLM")
    parser.add_argument("--caption", default="", help="Override the post caption")
    parser.add_argument("--company-id", default="133385169")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate PDF only, do not post")
    parser.add_argument("--use-existing", action="store_true",
                        help="Skip generation, use the most recent PDF of this type")
    parser.add_argument("--no-llm", action="store_true",
                        help="Use placeholder content (layout test)")
    args = parser.parse_args()

    print(f"\nDaanaa LinkedIn Pipeline")
    print(f"  Type: {args.type} | Post: {'no (dry run)' if args.dry_run else 'yes'}\n")

    # Step 1: Generate
    if args.use_existing:
        pdf = find_latest_pdf(args.type)
        if not pdf:
            print(f"No existing PDF found for type '{args.type}'.")
            sys.exit(1)
        print(f"  Using existing: {pdf.name}")
    else:
        fonts = gen.load_fonts()
        content = PLACEHOLDER if args.no_llm else gen.generate_content(args.type, args.context)
        pages = gen.render_carousel(content, fonts)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        pdf = OUTPUT / f"daanaa_{args.type}_{ts}.pdf"
        gen.save_pdf(pages, pdf)

    print(f"  PDF: {pdf}")

    if args.dry_run:
        print("\n  Dry run complete. Upload manually or re-run without --dry-run.\n")
        return

    # Step 2: Post
    caption = args.caption or CAPTIONS.get(args.type, CAPTIONS["hidden_gems"])
    poster.post_carousel(str(pdf), caption, args.company_id)
    print(f"\n  Done. {pdf.name} posted to LinkedIn.\n")


if __name__ == "__main__":
    main()

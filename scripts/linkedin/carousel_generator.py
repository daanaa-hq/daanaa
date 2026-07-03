"""
Daanaa LinkedIn Carousel Generator
-----------------------------------
Generates branded PDF carousels for LinkedIn.
Each run: LLM writes the slide content, Pillow renders it, output is a PDF.

Usage:
  python3 carousel_generator.py --type hidden_gems
  python3 carousel_generator.py --type sector_insight --sector "Food & Hunger"
  python3 carousel_generator.py --type how_it_works
  python3 carousel_generator.py --type feature_launch --feature "Volunteer matching"

Types: hidden_gems | sector_insight | how_it_works | feature_launch | myth_bust
"""

import argparse
import json
import os
import re
import textwrap
import urllib.request
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent
FONTS = BASE / "assets" / "fonts"
ASSETS = BASE / "assets"
OUTPUT = BASE / "output"
OUTPUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Brand palette
# ---------------------------------------------------------------------------
DEEP_NAVY   = (10, 22, 40)       # #0A1628
DARK_SURF   = (17, 29, 46)       # #111D2E
SOFT_GOLD   = (201, 169, 110)    # #C9A96E
BRIGHT_GOLD = (212, 184, 122)    # #D4B87A
WARM_CREAM  = (245, 240, 235)    # #F5F0EB
MUTED_CREAM = (168, 159, 148)    # #A89F94
COOL_GREY   = (55, 65, 81)       # #374151

# ---------------------------------------------------------------------------
# Slide canvas: 1080 × 1350 (4:5 portrait — optimal for LinkedIn)
# ---------------------------------------------------------------------------
W, H = 1080, 1350

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)

def load_fonts():
    return {
        "display_xl":  _font("CormorantGaramond-Italic.ttf", 108),
        "display_lg":  _font("CormorantGaramond-Italic.ttf", 80),
        "display_md":  _font("CormorantGaramond-Italic.ttf", 60),
        "display_sm":  _font("CormorantGaramond-Italic.ttf", 44),
        "body_lg":     _font("DMSans-Regular.ttf", 38),
        "body_md":     _font("DMSans-Regular.ttf", 30),
        "body_sm":     _font("DMSans-Regular.ttf", 24),
        "label":       _font("DMSans-SemiBold.ttf", 22),
        "label_sm":    _font("DMSans-SemiBold.ttf", 18),
    }

# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_w: int,
              draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines, line = [], []
    for w in words:
        test = " ".join(line + [w])
        if draw.textlength(test, font=font) <= max_w:
            line.append(w)
        else:
            if line:
                lines.append(" ".join(line))
            line = [w]
    if line:
        lines.append(" ".join(line))
    return lines

def draw_text_block(draw, text, font, color, x, y, max_w, line_gap=8):
    lines = wrap_text(text, font, max_w, draw)
    cy = y
    for ln in lines:
        draw.text((x, cy), ln, font=font, fill=color)
        bbox = draw.textbbox((0, 0), ln, font=font)
        cy += (bbox[3] - bbox[1]) + line_gap
    return cy  # bottom y after last line

def gold_rule(draw, x, y, w=80, h=3):
    draw.rectangle([x, y, x + w, y + h], fill=SOFT_GOLD)

def slide_counter(draw, fonts, current, total):
    label = f"{current} / {total}"
    draw.text((W - 60, H - 50), label, font=fonts["label_sm"],
              fill=MUTED_CREAM, anchor="rm")

def logo_stamp(img, size=56):
    logo_path = ASSETS / "logo.png"
    if not logo_path.exists():
        return
    logo = Image.open(logo_path).convert("RGBA")
    logo.thumbnail((size, size), Image.LANCZOS)
    img.paste(logo, (48, H - size - 44), logo)

def gradient_bg(size=(W, H), top=DEEP_NAVY, bottom=DARK_SURF):
    img = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(img)
    for y in range(size[1]):
        t = y / size[1]
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))
    return img

# ---------------------------------------------------------------------------
# Slide renderers
# ---------------------------------------------------------------------------
def slide_cover(fonts, headline: str, sub: str, slide_n: int, total: int) -> Image.Image:
    img = gradient_bg()
    draw = ImageDraw.Draw(img)

    # Top label
    draw.text((56, 68), "DAANAA", font=fonts["label"], fill=SOFT_GOLD)

    # Decorative rule
    gold_rule(draw, 56, 108)

    # Headline — large italic display
    y = 200
    y = draw_text_block(draw, headline, fonts["display_xl"], WARM_CREAM,
                        56, y, W - 112, line_gap=12)

    # Sub
    y += 32
    gold_rule(draw, 56, y)
    y += 24
    draw_text_block(draw, sub, fonts["body_lg"], MUTED_CREAM, 56, y, W - 112)

    # Swipe cue
    draw.text((W // 2, H - 80), "Swipe to explore →", font=fonts["label_sm"],
              fill=SOFT_GOLD, anchor="mm")

    logo_stamp(img)
    slide_counter(draw, fonts, slide_n, total)
    return img


def slide_content(fonts, label: str, headline: str, body: str,
                  slide_n: int, total: int,
                  accent_stat: str = "", accent_label: str = "") -> Image.Image:
    img = gradient_bg()
    draw = ImageDraw.Draw(img)

    # Slide label
    draw.text((56, 68), label.upper(), font=fonts["label"], fill=SOFT_GOLD)
    gold_rule(draw, 56, 102)

    # Headline
    y = 148
    y = draw_text_block(draw, headline, fonts["display_md"], WARM_CREAM,
                        56, y, W - 112, line_gap=10)

    # Optional big stat
    if accent_stat:
        y += 40
        draw.text((56, y), accent_stat, font=fonts["display_lg"], fill=BRIGHT_GOLD)
        bbox = draw.textbbox((0, 0), accent_stat, font=fonts["display_lg"])
        y += (bbox[3] - bbox[1]) + 8
        if accent_label:
            draw.text((56, y), accent_label, font=fonts["body_sm"], fill=MUTED_CREAM)
            y += 36

    # Body
    y += 32
    draw_text_block(draw, body, fonts["body_md"], MUTED_CREAM, 56, y, W - 112)

    logo_stamp(img)
    slide_counter(draw, fonts, slide_n, total)
    return img


def slide_cta(fonts, headline: str, body: str,
              slide_n: int, total: int) -> Image.Image:
    img = gradient_bg(top=DARK_SURF, bottom=DEEP_NAVY)
    draw = ImageDraw.Draw(img)

    # Centre everything vertically
    draw.text((W // 2, 280), headline, font=fonts["display_md"],
              fill=WARM_CREAM, anchor="mm")

    gold_rule(draw, W // 2 - 60, 360, w=120)

    y = 420
    for line in body.split("\n"):
        draw.text((W // 2, y), line.strip(), font=fonts["body_md"],
                  fill=MUTED_CREAM, anchor="mm")
        y += 52

    # CTA box
    box_y = H - 340
    draw.rounded_rectangle([120, box_y, W - 120, box_y + 100],
                            radius=50, fill=SOFT_GOLD)
    draw.text((W // 2, box_y + 50), "daanaa.org", font=fonts["display_sm"],
              fill=DEEP_NAVY, anchor="mm")

    # Follow line
    draw.text((W // 2, H - 190), "Follow Daanaa for weekly nonprofit insights",
              font=fonts["label_sm"], fill=MUTED_CREAM, anchor="mm")

    logo_stamp(img)
    slide_counter(draw, fonts, slide_n, total)
    return img

# ---------------------------------------------------------------------------
# LLM content generation (Ollama — qwen2.5:7b is fast, qwen3:30b is richer)
# ---------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"

# Model routing: rich carousel copy uses 30b; short text posts use 7b
MODELS = {
    "carousel": "qwen3:30b",   # richer, slower — for 8-slide carousels
    "text":     "qwen2.5:7b",  # fast — for single text posts and captions
}

# Content cache — avoid re-generating identical carousel types on the same day
_CACHE_DIR = BASE / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)

def _cache_key(carousel_type: str, context: str) -> str:
    import hashlib, datetime
    day = datetime.date.today().isoformat()
    return hashlib.md5(f"{carousel_type}:{context}:{day}".encode()).hexdigest()[:12]

def _load_cache(key: str) -> dict | None:
    p = _CACHE_DIR / f"{key}.json"
    if p.exists():
        import json as _json
        print("  Using cached content (same type+context today).")
        return _json.loads(p.read_text())
    return None

def _save_cache(key: str, content: dict):
    import json as _json
    (_CACHE_DIR / f"{key}.json").write_text(_json.dumps(content, indent=2))

PROMPTS = {
    "hidden_gems": lambda ctx: f"""You are writing copy for a LinkedIn carousel for Daanaa, a nonprofit discovery platform.
Topic: Hidden Gems — small nonprofits under $500K revenue with strong peer financial health.
Context: {ctx}

Write a JSON object with exactly these keys:
- cover_headline: punchy 5-8 word headline (italic, display font)
- cover_sub: 1 sentence subtitle
- slides: array of exactly 6 objects, each with:
  - label: 2-3 word section label (e.g. "The Problem", "What We Found")
  - headline: 6-10 word slide headline
  - body: 2-3 sentences of substantive copy
  - accent_stat: (optional) a single compelling number or ""
  - accent_label: (optional) label for the stat or ""
- cta_headline: 6-8 word closing line
- cta_body: 2 lines separated by \\n, each under 8 words

Tone: warm, specific, no jargon, no hype. Talk about real organizations doing real work.
Return ONLY valid JSON, no markdown fences.""",

    "how_it_works": lambda ctx: f"""You are writing copy for a LinkedIn carousel for Daanaa, a nonprofit discovery platform.
Topic: How Daanaa Works — step by step explanation of the platform.
Context: {ctx}

Write a JSON object with exactly these keys:
- cover_headline: punchy 5-8 word headline
- cover_sub: 1 sentence subtitle
- slides: array of exactly 6 objects, each with:
  - label: step label (e.g. "Step 1", "Step 2") or section name
  - headline: 6-10 word slide headline
  - body: 2-3 sentences of copy
  - accent_stat: (optional) compelling number or ""
  - accent_label: (optional) label or ""
- cta_headline: 6-8 word closing line
- cta_body: 2 lines separated by \\n, each under 8 words

Tone: clear, direct, non-technical. Donor and volunteer audience.
Return ONLY valid JSON, no markdown fences.""",

    "sector_insight": lambda ctx: f"""You are writing copy for a LinkedIn carousel for Daanaa, a nonprofit discovery platform.
Topic: Sector Insight — financial health data across a nonprofit sector.
Context: {ctx}

Write a JSON object with exactly these keys:
- cover_headline: punchy 5-8 word headline referencing the sector
- cover_sub: 1 sentence subtitle
- slides: array of exactly 6 objects, each with:
  - label: section label
  - headline: 6-10 word slide headline
  - body: 2-3 sentences of substantive copy using the data context
  - accent_stat: (optional) key number from context or ""
  - accent_label: (optional) label or ""
- cta_headline: 6-8 word closing line
- cta_body: 2 lines separated by \\n, each under 8 words

Tone: informative, context-giving, never alarmist. Data is from public IRS filings.
Return ONLY valid JSON, no markdown fences.""",

    "myth_bust": lambda ctx: f"""You are writing copy for a LinkedIn carousel for Daanaa, a nonprofit discovery platform.
Topic: Myth-busting common misconceptions about nonprofits and charitable giving.
Context: {ctx}

Write a JSON object with exactly these keys:
- cover_headline: punchy 5-8 word myth-bust hook
- cover_sub: 1 sentence subtitle
- slides: array of exactly 6 objects, each with:
  - label: "Myth" or "Reality" alternating, or section label
  - headline: 6-10 word slide headline
  - body: 2-3 sentences of substantive copy
  - accent_stat: (optional) compelling number or ""
  - accent_label: (optional) label or ""
- cta_headline: 6-8 word closing line
- cta_body: 2 lines separated by \\n, each under 8 words

Tone: warm, informative, never preachy. Empower donors with real context.
Return ONLY valid JSON, no markdown fences.""",

    "feature_launch": lambda ctx: f"""You are writing copy for a LinkedIn carousel for Daanaa, a nonprofit discovery platform.
Topic: Feature Launch announcement.
Context: {ctx}

Write a JSON object with exactly these keys:
- cover_headline: punchy 5-8 word headline announcing the feature
- cover_sub: 1 sentence subtitle
- slides: array of exactly 6 objects, each with:
  - label: section label
  - headline: 6-10 word slide headline
  - body: 2-3 sentences of copy explaining the feature and its value
  - accent_stat: (optional) number or ""
  - accent_label: (optional) label or ""
- cta_headline: 6-8 word closing line
- cta_body: 2 lines separated by \\n, each under 8 words

Tone: excited but grounded, no hype. Show the real value for donors/orgs.
Return ONLY valid JSON, no markdown fences.""",
}

DEFAULT_CONTEXTS = {
    "hidden_gems": (
        "Daanaa has identified 33,900+ small nonprofits (under $500K revenue) "
        "with strong peer financial health scores. These organizations are often "
        "invisible online despite doing real community work. Examples: food pantries, "
        "tutoring programs, animal rescues, local arts orgs."
    ),
    "how_it_works": (
        "Daanaa indexes 1.7 million IRS-recognized nonprofits. Each org gets a "
        "peer financial context score (0-100) benchmarked against similar orgs in "
        "the same NTEE category and revenue band. Data from IRS Form 990 filings. "
        "Free to use, no account required, no paid placement."
    ),
    "sector_insight": (
        "General nonprofit sector: approximately 40% of nonprofits show fewer than "
        "3 months of operating reserves. Small orgs (under $500K) are more likely "
        "to have lean reserves — not because they are struggling, but because they "
        "invest directly in programs. Data from public IRS 990 filings."
    ),
    "myth_bust": (
        "Common myths: overhead ratio determines org quality; bigger nonprofits are "
        "better; national orgs are more effective than local ones; you need to give "
        "large amounts to make a difference; all 501c3s are the same."
    ),
    "feature_launch": (
        "New feature on Daanaa: Hidden Gems directory — a curated weekly rotation "
        "of small, financially healthy nonprofits with limited online presence. "
        "Rotates every Monday. Filterable by cause, location, and org type."
    ),
}


def generate_content(carousel_type: str, extra_context: str = "", use_cache: bool = True) -> dict:
    ctx = DEFAULT_CONTEXTS.get(carousel_type, "") + (" " + extra_context if extra_context else "")

    if use_cache:
        key = _cache_key(carousel_type, ctx)
        cached = _load_cache(key)
        if cached:
            return cached

    prompt_fn = PROMPTS.get(carousel_type, PROMPTS["hidden_gems"])
    prompt = prompt_fn(ctx)

    # Route to right model: carousels need quality; text posts need speed
    model = MODELS["carousel"]
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 2048},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    print(f"  Generating content with {model}...")
    with urllib.request.urlopen(req, timeout=180) as resp:
        raw = json.loads(resp.read())["response"]

    # Extract JSON from response (model may add prose around it)
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        raise ValueError(f"LLM did not return valid JSON:\n{raw[:500]}")
    result = json.loads(match.group())

    if use_cache:
        _save_cache(key, result)
    return result


# ---------------------------------------------------------------------------
# Render full carousel → list of PIL images
# ---------------------------------------------------------------------------
def render_carousel(content: dict, fonts: dict) -> list[Image.Image]:
    slides_data = content.get("slides", [])
    total = len(slides_data) + 2  # cover + content slides + cta

    pages = []

    # Slide 1: Cover
    pages.append(slide_cover(
        fonts,
        content.get("cover_headline", "Discovering the nonprofits you never knew existed"),
        content.get("cover_sub", "A look at what public data reveals."),
        1, total
    ))

    # Content slides
    for i, s in enumerate(slides_data, start=2):
        pages.append(slide_content(
            fonts,
            label=s.get("label", ""),
            headline=s.get("headline", ""),
            body=s.get("body", ""),
            slide_n=i,
            total=total,
            accent_stat=s.get("accent_stat", ""),
            accent_label=s.get("accent_label", ""),
        ))

    # CTA slide
    pages.append(slide_cta(
        fonts,
        content.get("cta_headline", "Start exploring today."),
        content.get("cta_body", "Free. No account needed.\nJust real nonprofit data."),
        total, total
    ))

    return pages


# ---------------------------------------------------------------------------
# Save as PDF
# ---------------------------------------------------------------------------
def save_pdf(pages: list[Image.Image], path: Path):
    # Pillow's PDF writer needs images with JPEG codec available.
    # Save each slide as a JPEG then rebuild the PDF to avoid codec issues.
    import io
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.utils import ImageReader

    c = rl_canvas.Canvas(str(path), pagesize=(W, H))
    for page in pages:
        buf = io.BytesIO()
        page.convert("RGB").save(buf, format="JPEG", quality=92)
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=W, height=H)
        c.showPage()
    c.save()
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Daanaa LinkedIn Carousel Generator")
    parser.add_argument("--type", default="hidden_gems",
                        choices=list(PROMPTS.keys()),
                        help="Carousel type")
    parser.add_argument("--context", default="",
                        help="Extra context to pass to the LLM")
    parser.add_argument("--sector", default="",
                        help="Sector name (for sector_insight type)")
    parser.add_argument("--feature", default="",
                        help="Feature name (for feature_launch type)")
    parser.add_argument("--no-llm", action="store_true",
                        help="Skip LLM, use placeholder content for layout testing")
    args = parser.parse_args()

    extra = " ".join(filter(None, [args.context, args.sector, args.feature]))

    print(f"\nDaanaa Carousel Generator")
    print(f"  Type:    {args.type}")
    print(f"  Context: {extra or '(default)'}")

    fonts = load_fonts()

    if args.no_llm:
        content = {
            "cover_headline": "The nonprofits nobody talks about",
            "cover_sub": "But probably should.",
            "slides": [
                {"label": "The Problem", "headline": "Most giving flows to familiar names",
                 "body": "Name recognition drives donations more than impact. The organizations doing the quietest work often have the smallest digital footprint.",
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
    else:
        content = generate_content(args.type, extra)

    print("  Rendering slides...")
    pages = render_carousel(content, fonts)

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out_path = OUTPUT / f"daanaa_{args.type}_{ts}.pdf"
    save_pdf(pages, out_path)

    print(f"\n  Done. Upload to LinkedIn as a Document post.")
    print(f"  File: {out_path}\n")


if __name__ == "__main__":
    main()

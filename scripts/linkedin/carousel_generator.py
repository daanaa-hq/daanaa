"""
Daanaa LinkedIn Carousel Generator — SIGNATURE DESIGN
-------------------------------------------------------
Generates premium, impactful branded carousels optimized for LinkedIn engagement.

Signature design principles:
- Dramatic data visualization (big numbers, visual bars)
- Premium typography with intentional hierarchy
- Strategic white space (luxury feel, not clutter)
- Distinctive visual elements (Daanaa mark pattern)
- Mission-aligned color use (gold for trust, navy for authority)

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
        "display_huge": _font("CormorantGaramond-Italic.ttf", 190),
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
def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text (LLM sometimes outputs <i>, <b>, etc)."""
    return re.sub(r'<[^>]+>', '', text).strip()

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

def signature_accent(draw, x, y, size=40, variant="circle"):
    """Draw signature Daanaa visual accent (circle or square pattern)."""
    if variant == "circle":
        draw.ellipse([x, y, x + size, y + size], fill=SOFT_GOLD, outline=BRIGHT_GOLD, width=2)
    elif variant == "square":
        draw.rectangle([x, y, x + size, y + size], fill=SOFT_GOLD, outline=BRIGHT_GOLD, width=2)

def draw_link_line(draw, fonts, text, y):
    """Engagement line pointing readers at the platform. Gold, centered."""
    draw.text((56, y), text, font=fonts["label"], fill=BRIGHT_GOLD)

def parse_stat_visual(stat: str):
    """Infer a data visual from the stat text.

    '48%'   -> ('bar', 48, 100)
    '1 in 3' -> ('dots', 1, 3)
    '6 mo'  -> ('segments', 6, 12)
    """
    stat = stat.strip().lower()
    m = re.match(r'^(\d+)\s*%$', stat)
    if m:
        return ("bar", int(m.group(1)), 100)
    m = re.match(r'^(\d+)\s+in\s+(\d+)$', stat)
    if m:
        return ("dots", int(m.group(1)), int(m.group(2)))
    m = re.match(r'^(\d+)\s*mo', stat)
    if m:
        return ("segments", int(m.group(1)), 12)
    return None

VISUAL_H = 110  # vertical space a stat visual occupies

def draw_stat_visual(draw, visual, x, y, max_w):
    """Render the visual proof of the stat. Returns bottom y."""
    kind, value, total = visual

    if kind == "bar":
        bar_h = 44
        # Track
        draw.rounded_rectangle([x, y, x + max_w, y + bar_h], radius=8, fill=COOL_GREY)
        # Fill
        fill_w = max(int(max_w * value / total), 12)
        draw.rounded_rectangle([x, y, x + fill_w, y + bar_h], radius=8, fill=SOFT_GOLD)
        return y + bar_h + 24

    if kind == "dots":
        # Big circles: value filled, rest outlined
        d = 84
        gap = 36
        cx = x
        for i in range(total):
            if i < value:
                draw.ellipse([cx, y, cx + d, y + d], fill=SOFT_GOLD)
            else:
                draw.ellipse([cx, y, cx + d, y + d], outline=COOL_GREY, width=4)
            cx += d + gap
        return y + d + 24

    if kind == "segments":
        # Month blocks: value filled of total
        seg_w = (max_w - (total - 1) * 10) // total
        seg_h = 44
        cx = x
        for i in range(total):
            color = SOFT_GOLD if i < value else COOL_GREY
            draw.rounded_rectangle([cx, y, cx + seg_w, y + seg_h], radius=6, fill=color)
            cx += seg_w + 10
        return y + seg_h + 24

    return y

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

def footer_url(draw, fonts):
    """Add daanaa.org footer to bottom of slide."""
    draw.text((W // 2, H - 20), "www.daanaa.org",
              font=fonts["label_sm"],
              fill=SOFT_GOLD, anchor="mb")

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

    # Top label + signature accent
    draw.text((56, 68), "DAANAA", font=fonts["label"], fill=SOFT_GOLD)
    signature_accent(draw, 900, 68, size=30, variant="circle")

    # Decorative rule
    gold_rule(draw, 56, 108)

    # Headline — large italic display with premium spacing
    headline = strip_html_tags(headline)
    sub = strip_html_tags(sub)
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
    footer_url(draw, fonts)
    slide_counter(draw, fonts, slide_n, total)
    return img


def slide_content(fonts, label: str, headline: str, body: str,
                  slide_n: int, total: int,
                  accent_stat: str = "", accent_label: str = "",
                  source: str = "", link: str = "") -> Image.Image:
    img = gradient_bg()
    draw = ImageDraw.Draw(img)

    # Signature accent top-right
    signature_accent(draw, 900, 68, size=28, variant="circle")

    # Slide label + decorative rule
    draw.text((56, 68), label.upper(), font=fonts["label"], fill=SOFT_GOLD)
    gold_rule(draw, 56, 102)

    # Headline
    headline = strip_html_tags(headline)
    body = strip_html_tags(body)
    y = 150
    y = draw_text_block(draw, headline, fonts["display_md"], WARM_CREAM,
                        56, y, W - 112, line_gap=10)
    header_bottom = y

    # Dry-run measure the stat/body/source block so we can vertically
    # center it between the headline and the link line (kills dead space)
    visual = parse_stat_visual(strip_html_tags(accent_stat)) if accent_stat else None

    def _block_height():
        h = 0
        if accent_stat:
            f = fonts["display_huge"] if len(strip_html_tags(accent_stat)) <= 5 else fonts["display_xl"]
            bb = draw.textbbox((56, 0), strip_html_tags(accent_stat), font=f)
            h += bb[3] + 28 + 3 + 28  # stat + gap + rule + gap
            if accent_label:
                lines = wrap_text(strip_html_tags(accent_label), fonts["body_lg"], W - 112, draw)
                bb = draw.textbbox((0, 0), "Ag", font=fonts["body_lg"])
                h += len(lines) * ((bb[3] - bb[1]) + 8)
            if visual:
                h += 36 + VISUAL_H
        h += 44
        lines = wrap_text(body, fonts["body_lg"], W - 112, draw)
        bb = draw.textbbox((0, 0), "Ag", font=fonts["body_lg"])
        h += len(lines) * ((bb[3] - bb[1]) + 12)
        if source:
            h += 36 + 30
        return h

    avail_bottom = H - 210  # above the link line
    block_h = _block_height()
    slack = avail_bottom - header_bottom - block_h
    y = header_bottom + max(40, slack // 2)

    # THE NUMBER — dominant, measured placement (no overlap)
    if accent_stat:
        accent_stat = strip_html_tags(accent_stat)
        # Scale down if the stat is long ("6 months" vs "48%")
        stat_font = fonts["display_huge"] if len(accent_stat) <= 5 else fonts["display_xl"]
        draw.text((56, y), accent_stat, font=stat_font, fill=BRIGHT_GOLD)
        # Measure the ACTUAL rendered extent at this position
        stat_bbox = draw.textbbox((56, y), accent_stat, font=stat_font)
        y = stat_bbox[3] + 28

        # Gold rule anchors number to its meaning
        gold_rule(draw, 56, y, w=120)
        y += 28

        if accent_label:
            accent_label = strip_html_tags(accent_label)
            y = draw_text_block(draw, accent_label, fonts["body_lg"], WARM_CREAM,
                                56, y, W - 112, line_gap=8)

        # Visual proof of the number (bar / dots / segments)
        if visual:
            y += 36
            y = draw_stat_visual(draw, visual, 56, y, W - 112)

    # Body — larger type, fills the slide
    y += 44
    y = draw_text_block(draw, body, fonts["body_lg"], MUTED_CREAM,
                        56, y, W - 112, line_gap=12)

    # Source — its own quiet line, never merged into the body
    if source:
        source = strip_html_tags(source)
        y += 36
        draw.text((56, y), f"Source: {source}", font=fonts["body_sm"], fill=MUTED_CREAM)

    # Engagement line — every slide points at the platform
    if link:
        draw.text((56, H - 150), f"See the data  →  {link}",
                  font=fonts["label"], fill=BRIGHT_GOLD)

    logo_stamp(img)
    footer_url(draw, fonts)
    slide_counter(draw, fonts, slide_n, total)
    return img


def slide_cta(fonts, headline: str, body: str,
              slide_n: int, total: int) -> Image.Image:
    img = gradient_bg(top=DARK_SURF, bottom=DEEP_NAVY)
    draw = ImageDraw.Draw(img)

    # Signature accent top-right
    signature_accent(draw, 900, 68, size=28, variant="square")

    # Centre everything vertically
    headline = strip_html_tags(headline)
    body = strip_html_tags(body)
    draw.text((W // 2, 200), headline, font=fonts["display_md"],
              fill=WARM_CREAM, anchor="mm")

    # Enhanced rule
    gold_rule(draw, W // 2 - 80, 280, w=160)

    y = 350
    for line in body.split("\n"):
        draw.text((W // 2, y), line.strip(), font=fonts["body_md"],
                  fill=WARM_CREAM, anchor="mm")
        y += 60

    # Premium CTA button with visual presence
    box_y = H - 360
    draw.rounded_rectangle([80, box_y, W - 80, box_y + 120],
                            radius=60, fill=SOFT_GOLD, outline=BRIGHT_GOLD, width=3)
    draw.text((W // 2, box_y + 60), "daanaa.org", font=fonts["display_sm"],
              fill=DEEP_NAVY, anchor="mm")

    # Subtle follow line
    draw.text((W // 2, H - 160), "Follow Daanaa for nonprofit insights",
              font=fonts["label_sm"], fill=MUTED_CREAM, anchor="mm")

    logo_stamp(img)
    slide_counter(draw, fonts, slide_n, total)
    return img

# ---------------------------------------------------------------------------
# LLM content generation — routed through GPU server (port 11437, Vulkan)
# ---------------------------------------------------------------------------
import sys as _sys
_sys.path.insert(0, str(BASE))
import llm_client as _llm

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

    print(f"  Generating carousel content via GPU server...")
    raw = _llm.generate(prompt, max_tokens=2048, temperature=0.7)

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

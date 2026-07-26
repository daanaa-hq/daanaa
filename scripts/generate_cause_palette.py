#!/usr/bin/env python3
"""
Generate the theme-aware cause palette used by cause chips and category pages.

Why generated rather than hand-picked
-------------------------------------
The previous palette assigned a Tailwind colour per NTEE major group: 26
categories x 2 themes x 3 roles = 156 hand-picked values. Nobody maintains 156
values by hand, which is why it drifted into a state that was wrong in BOTH
themes: chips measured 17:1 against the dark page (glowing blobs) and 1.0:1
against the light page (invisible).

Here each family owns ONE hue angle, and surface/border/text are derived from it
by a per-theme recipe. That is 9 hues + 2 recipes instead of 156 values, and
changing a recipe number moves every family together.

Grouping
--------
The nine families are the official NCCS major-group families, not an invention
of ours. Using the standard taxonomy keeps the grouping explainable from public
data (Stewardship P3, P9). Z (unclassified) gets a neutral grey rather than a
hue, since inventing a colour for "we do not know" would imply a category that
does not exist.

Colour is never the only signal: every chip also carries its label, so this
satisfies WCAG 1.4.1 independently of hue.

Usage:
  python3 scripts/generate_cause_palette.py --check   # verify contrast only
  python3 scripts/generate_cause_palette.py           # write tokens + mapping
"""
import argparse
import colorsys
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKENS = ROOT / "frontend" / "public" / "tokens.css"

BEGIN = "/* BEGIN generated cause palette"
END = "/* END generated cause palette */"

# key, human label, NTEE major-group codes, hue angle
FAMILIES = [
    ("arts",        "Arts, Culture & Humanities",      "A",        330),
    ("education",   "Education",                       "BUV",      220),
    ("environment", "Environment & Animals",           "CD",       140),
    ("health",      "Health",                          "EFGH",     190),
    ("human",       "Human Services",                  "IJKLMNOP",  25),
    ("global",      "International & Foreign Affairs", "Q",        265),
    ("public",      "Public & Societal Benefit",       "RSTW",      45),
    ("religion",    "Religion-Related",                "X",        290),
    ("mutual",      "Mutual & Membership Benefit",     "Y",        170),
]

# One recipe per theme: (saturation %, lightness %) for each role.
# Dark is the site default (:root); light is the [data-theme="light"] override.
RECIPE = {
    "dark":  {"surface": (35, 17), "border": (30, 30), "text": (60, 76)},
    "light": {"surface": (45, 90), "border": (40, 82), "text": (55, 28)},
}
PAGE = {"dark": (10, 22, 40), "light": (248, 247, 245)}
NEUTRAL = {  # Z / unclassified: grey, no hue
    "dark":  {"surface": "#1B2233", "border": "#2C3547", "text": "#AEB6C4"},
    "light": {"surface": "#EDEDEB", "border": "#DCDCD8", "text": "#4A4A46"},
}


def hsl(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return (round(r * 255), round(g * 255), round(b * 255))


def hexof(rgb):
    return "#%02X%02X%02X" % rgb


def _lin(v):
    v /= 255
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def luminance(c):
    r, g, b = map(_lin, c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    l1, l2 = luminance(a), luminance(b)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def check():
    """Text on chip must meet WCAG AA (4.5). Chip must be visible against the
    page without glaring: 1.05 to 3.0."""
    failures = []
    for key, label, codes, hue in FAMILIES:
        for theme in ("dark", "light"):
            r = RECIPE[theme]
            surface = hsl(hue, *r["surface"])
            text = hsl(hue, *r["text"])
            ct = contrast(text, surface)
            cs = contrast(surface, PAGE[theme])
            if ct < 4.5:
                failures.append(f"{key}/{theme}: text on chip {ct:.2f}:1 < 4.5")
            if not (1.05 <= cs <= 3.0):
                failures.append(f"{key}/{theme}: chip vs page {cs:.2f}:1 outside 1.05-3.0")
    return failures


def css_block():
    out = [BEGIN, "   Do not edit by hand. Regenerate:",
           "     python3 scripts/generate_cause_palette.py",
           "",
           "   One hue per NCCS family; surface/border/text derived by a per-theme",
           "   recipe. Dark is the default (:root); light overrides it. */", ""]

    def emit(theme, selector):
        r = RECIPE[theme]
        lines = [f"{selector} {{"]
        for key, label, codes, hue in FAMILIES:
            lines.append(f"  /* {label} ({codes}) */")
            for role in ("surface", "border", "text"):
                lines.append(f"  --cause-{key}-{role}: {hexof(hsl(hue, *r[role]))};")
        lines.append("  /* Unclassified (Z) - neutral, no hue */")
        for role in ("surface", "border", "text"):
            lines.append(f"  --cause-unknown-{role}: {NEUTRAL[theme][role]};")
        lines.append("}")
        return lines

    out += emit("dark", ":root")
    out.append("")
    out += emit("light", ':root[data-theme="light"]')
    out.append("")
    out.append(END)
    return "\n".join(out)


def code_to_family():
    m = {}
    for key, _label, codes, _hue in FAMILIES:
        for c in codes:
            m[c] = key
    m["Z"] = "unknown"
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify contrast, write nothing")
    ap.add_argument("--print-map", action="store_true", help="emit code->family JSON")
    args = ap.parse_args()

    failures = check()
    if failures:
        print("CONTRAST FAILURES:")
        for f in failures:
            print("  -", f)
        return 1

    covered = code_to_family()
    missing = [chr(c) for c in range(65, 91) if chr(c) not in covered]
    if missing:
        print("NTEE codes with no family:", ", ".join(missing))
        return 1

    if args.print_map:
        print(json.dumps(covered, indent=2, sort_keys=True))
        return 0

    if args.check:
        print(f"OK: {len(FAMILIES)} families, 26 NTEE codes covered, "
              f"all contrast checks pass in both themes")
        return 0

    text = TOKENS.read_text()
    block = css_block()
    if BEGIN in text:
        head, rest = text.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        text = head + block + tail
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    TOKENS.write_text(text)
    print(f"Wrote {len(FAMILIES)} families (+neutral) to {TOKENS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

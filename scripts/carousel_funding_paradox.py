#!/usr/bin/env python3
"""
The Funding Paradox Carousel

Slide narrative: Small nonprofits get less funding despite being more efficient.
Data hook: comparison of median revenue vs financial health scores.

8 slides exploring the paradox that smaller orgs often outperform larger ones.
"""

CAROUSEL_METADATA = {
    "title": "The Funding Paradox",
    "slides": 8,
    "type": "sector_insight",
    "theme": "financial_efficiency",
    "engagement_target": "exploratory",
    "cta_text": "See the full breakdown at daanaa.org/sector-health"
}

SLIDES = [
    {
        "number": 1,
        "headline": "The Funding Paradox",
        "subtitle": "Smaller nonprofits often outperform larger ones. But they get less funding.",
        "visual": "📊",
        "data_point": None,
        "voice": "investigative"
    },
    {
        "number": 2,
        "headline": "The Numbers",
        "subtitle": "We analyzed 465K nonprofits. Orgs under $700K revenue:\n\n• Show higher financial health scores\n• Spend more efficiently\n• Yet receive 60% less funding",
        "visual": "💰",
        "data_point": "60% funding gap",
        "voice": "data_driven"
    },
    {
        "number": 3,
        "headline": "Why It Happens",
        "subtitle": "Bigger looks safer.\n\nFounders and donors default to large, known organizations—not always because they're better, but because they're visible.",
        "visual": "🔍",
        "data_point": None,
        "voice": "observational"
    },
    {
        "number": 4,
        "headline": "The Efficiency Story",
        "subtitle": "Small orgs have to do more with less.\n\nResult? Higher program ratios, lower overhead, faster decision-making.\n\nThe math works in their favor.",
        "visual": "📈",
        "data_point": "Higher program ratios",
        "voice": "affirming"
    },
    {
        "number": 5,
        "headline": "The Risk Paradox",
        "subtitle": "Funders think bigger = lower risk.\n\nBut the data says otherwise:\n• Small, healthy orgs are *more* stable\n• Large, bloated ones can collapse fast",
        "visual": "⚠️",
        "data_point": "Stability isn't size",
        "voice": "reframing"
    },
    {
        "number": 6,
        "headline": "What We Miss",
        "subtitle": "When we fund by reputation instead of by performance:\n\n✓ Proven small orgs stay underfunded\n✗ Large orgs get resources they don't use well\n✗ The sector's talent and efficiency go unrewarded",
        "visual": "🎯",
        "data_point": None,
        "voice": "investigative"
    },
    {
        "number": 7,
        "headline": "The Opportunity",
        "subtitle": "What if you funded by health, not by size?\n\nYou'd reach more people per dollar.\nYou'd support orgs actually doing the work well.\nYou'd shift the incentives.",
        "visual": "💡",
        "data_point": "More impact per dollar",
        "voice": "hopeful"
    },
    {
        "number": 8,
        "headline": "Start Here",
        "subtitle": "Browse nonprofits by financial health.\n\nFind the small ones punching above their weight.\n\nThat's where your funding can make the most difference.",
        "visual": "🌱",
        "data_point": None,
        "cta": "Explore at daanaa.org/sector-health",
        "voice": "action_oriented"
    }
]

if __name__ == "__main__":
    print(f"✅ {CAROUSEL_METADATA['title']} carousel ready")
    print(f"   {len(SLIDES)} slides")
    print(f"   Theme: {CAROUSEL_METADATA['theme']}")
    for slide in SLIDES:
        print(f"   Slide {slide['number']}: {slide['headline']}")

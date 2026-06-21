#!/usr/bin/env python3
"""
Daily analytics insights from Plausible.
Fetches stats, analyzes key metrics, emails actionable insights.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

PLAUSIBLE_API_KEY = os.environ.get("PLAUSIBLE_API_KEY", "")
PLAUSIBLE_SITE_ID = "daanaa.org"
PLAUSIBLE_API = "https://plausible.io/api/v1"

def fetch_plausible_stats(metric: str, period: str = "7d") -> dict:
    """Fetch metrics from Plausible API."""
    if not PLAUSIBLE_API_KEY:
        return {}

    url = f"{PLAUSIBLE_API}/stats/aggregate"
    headers = {"Authorization": f"Bearer {PLAUSIBLE_API_KEY}"}
    params = {
        "site_id": PLAUSIBLE_SITE_ID,
        "period": period,
        "metrics": metric,
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            return r.json().get("results", {})
    except Exception as e:
        print(f"Error fetching {metric}: {e}")

    return {}

def fetch_top_pages(period: str = "7d", limit: int = 10) -> list:
    """Fetch top pages by visitors."""
    if not PLAUSIBLE_API_KEY:
        return []

    url = f"{PLAUSIBLE_API}/stats/breakdown"
    headers = {"Authorization": f"Bearer {PLAUSIBLE_API_KEY}"}
    params = {
        "site_id": PLAUSIBLE_SITE_ID,
        "period": period,
        "property": "event:page",
        "limit": limit,
        "metrics": "visitors,bounce_rate,time_on_page",
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            return r.json().get("results", [])
    except Exception as e:
        print(f"Error fetching top pages: {e}")

    return []

def analyze_metrics() -> dict:
    """Analyze key metrics and generate insights."""
    insights = {
        "timestamp": datetime.now().isoformat(),
        "period": "7d",
        "metrics": {},
        "alerts": [],
        "recommendations": [],
    }

    # Fetch overall stats
    visitors = fetch_plausible_stats("visitors")
    pageviews = fetch_plausible_stats("pageviews")
    bounce_rate = fetch_plausible_stats("bounce_rate")

    insights["metrics"]["visitors"] = visitors
    insights["metrics"]["pageviews"] = pageviews
    insights["metrics"]["bounce_rate"] = bounce_rate

    # Fetch top pages
    top_pages = fetch_top_pages()
    insights["metrics"]["top_pages"] = top_pages

    # Flag high bounce rates
    if bounce_rate and bounce_rate.get("value", 0) > 50:
        insights["alerts"].append(f"⚠️ High bounce rate: {bounce_rate['value']:.1f}%")

    # Identify drop-off pages
    for page in top_pages[:5]:
        if page.get("bounce_rate", 0) > 60:
            insights["alerts"].append(f"Drop-off: {page['page']} ({page['bounce_rate']:.0f}% bounce)")

    # Recommendations based on traffic
    if visitors and visitors.get("value", 0) > 100:
        insights["recommendations"].append("✓ Strong traffic. Focus on conversion optimization.")
    else:
        insights["recommendations"].append("📈 Low traffic. Increase outreach or improve SEO.")

    # Check for key pages
    key_pages = {"/directory": "Directory", "/org/": "Org Detail", "/wallet": "Wallet"}
    for path, name in key_pages.items():
        found = any(p["page"].startswith(path) for p in top_pages)
        if not found:
            insights["alerts"].append(f"Missing in top 10: {name} ({path})")

    return insights

def save_insights(insights: dict) -> str:
    """Save insights to file."""
    log_dir = Path(__file__).parent.parent / "logs" / "analytics"
    log_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    filepath = log_dir / f"insights_{date_str}.json"

    with open(filepath, "w") as f:
        json.dump(insights, f, indent=2)

    return str(filepath)

def format_email_body(insights: dict) -> str:
    """Format insights as email body."""
    bounce = insights['metrics'].get('bounce_rate', {}).get('value', 'N/A')
    bounce_str = f"{float(bounce):.1f}%" if bounce != 'N/A' else 'N/A'

    body = f"""Daanaa Analytics Insights — {insights['timestamp'][:10]}

📊 Key Metrics (7-day):
  • Visitors: {insights['metrics'].get('visitors', {}).get('value', 'N/A')}
  • Pageviews: {insights['metrics'].get('pageviews', {}).get('value', 'N/A')}
  • Bounce Rate: {bounce_str}

🔥 Top Pages:
"""

    for page in insights['metrics'].get('top_pages', [])[:5]:
        body += f"  • {page['page']}: {page['visitors']} visitors ({page['bounce_rate']:.0f}% bounce)\n"

    if insights['alerts']:
        body += "\n⚠️ Alerts:\n"
        for alert in insights['alerts']:
            body += f"  {alert}\n"

    if insights['recommendations']:
        body += "\n💡 Recommendations:\n"
        for rec in insights['recommendations']:
            body += f"  {rec}\n"

    return body

def main():
    print("Fetching analytics insights...")

    insights = analyze_metrics()
    filepath = save_insights(insights)
    print(f"✓ Saved to {filepath}")

    email_body = format_email_body(insights)
    print("\nEmail preview:")
    print(email_body)

    # TODO: Send email via email_service.py if configured
    # email_service.send_analytics_digest(email_body)

if __name__ == "__main__":
    main()

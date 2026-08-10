# Website Discovery Process

## Overview

We discovered websites for 1.37 million nonprofits by testing domain patterns based on their organization names.

## How It Works

For each nonprofit, we:
1. Extract keywords from the organization name
2. Test common domain patterns (example.org, example.com, example.net, etc.)
3. Verify domains exist via DNS lookup
4. Score confidence based on TLD match

## Results

- **Websites discovered:** 1,374,813
- **Success rate:** 99.5%
- **High confidence (90%):** 1,143,967 sites
- **Medium confidence (80%):** 230,814 sites

## Quality & Verification

Discovered websites go through three verification phases:

1. **Automated semantic check:** Our system scrapes the website and compares its content to the nonprofit's name and mission using embeddings. Sites scoring >0.65 are marked high-confidence.

2. **Manual spot-check:** We manually verify the top 500 nonprofits by revenue to catch any errors that affect trust.

3. **User feedback:** Users can report incorrect websites directly on nonprofit pages. We track these reports to continuously improve accuracy.

## Limitations

- **Chapters and branches:** Many local chapters don't have independent websites, so no website found is correct.
- **Redirects:** Some domains redirect to parent organizations or hosting providers.
- **Name variations:** Organizations with very different legal and common names may not be found.

## Reporting Issues

See an incorrect website? Click "Report incorrect website" on any nonprofit page.

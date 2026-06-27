Inspect this entire project and determine where nonprofit data is stored.

Do NOT deploy anything.
Do NOT modify production code.
Do NOT change application behavior.

Goal:
Build a visibility/export system for Daanaa using the existing local data files.

Tasks:

1. Find all nonprofit data sources in this project.
   Search CSV, JSON, SQLite, SQL dumps, seed files, ETL scripts, imports, and data folders.

2. Determine which files contain:
   - EIN
   - organization name
   - city
   - state
   - IRS category

3. Generate:
   data/orgs.csv

Columns:
ein,name,city,state,category_letter,category_name,profile_url

where:
profile_url=https://daanaa.org/org/{ein}

4. Generate:
   dist/sitemap-index.xml
   dist/sitemaps/*
   dist/llms.txt
   dist/open-data.html

5. Create scripts so everything can be regenerated later.

Requirements:
- No deployment
- No production code changes
- Document all discovered data sources
- Produce README-visibility.md
- Prefer local files over website scraping

When finished, provide:
- data source locations
- record counts
- files created
- commands needed to regenerate

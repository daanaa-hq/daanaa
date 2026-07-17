# Donor Journey

```mermaid
sequenceDiagram
  participant D as Donor
  participant F as Frontend
  participant S as Search API
  participant P as Public profile
  participant O as Org-owned site

  D->>F: Search by cause, city, name
  F->>S: Query browse/search
  S-->>F: Results with context
  D->>F: Open nonprofit profile
  F->>S: Fetch organization detail
  S-->>F: Profile, context, donate/website info
  D->>O: Follow external hand-off
```


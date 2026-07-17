# Failure Impact Map

```mermaid
flowchart TB
  A[Ingest failure] --> A1[Stale nonprofit data]
  B[Search index failure] --> B1[Broken discovery]
  C[Claim verification failure] --> C1[Blocked nonprofit ownership]
  D[Security header drift] --> D1[Privacy / XSS risk]
  E[Language drift] --> E1[Trust and governance confusion]
```


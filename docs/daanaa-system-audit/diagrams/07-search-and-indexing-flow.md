# Search and Indexing Flow

```mermaid
flowchart TB
  Q[User query] --> FE[Frontend]
  FE --> API[Search endpoint]
  API --> FTS[FTS5 keyword search]
  API --> SEM[Semantic lookup]
  FTS --> R[Results]
  SEM --> R
  R --> FE
```


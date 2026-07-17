# Nonprofit Journey

```mermaid
sequenceDiagram
  participant N as Nonprofit
  participant F as Frontend
  participant A as Full API
  participant M as Admin review
  participant E as Email

  N->>F: Find own profile
  N->>F: Start claim
  F->>A: POST /api/claim/start
  A-->>E: Send org/admin notifications
  A-->>N: Pending claim status
  M->>A: Verify / review claim
  A-->>F: Publish claimed/active state
```


# MERIT Frontend — API Specification

This document defines every API endpoint the React frontend calls. Your Python/Flask backend must implement these.

---

## Base URL

All endpoints are prefixed with `/api`. Set `VITE_API_URL` env var to match.

```
Development:  http://localhost:5000/api
Production:   /api  (served from same domain)
```

---

## GET /api/stats

Returns platform-wide statistics for the homepage trust bar.

### Response

```json
{
  "total_organizations": 45873,
  "total_categories": 27,
  "states_covered": 53
}
```

| Field | Type | Description |
|-------|------|-------------|
| `total_organizations` | int | Count of all verified 501(c)(3) orgs |
| `total_categories` | int | Number of NTEE categories |
| `states_covered` | int | Number of states/territories with orgs |

---

## GET /api/categories

Returns all nonprofit categories for the category grid.

### Response

```json
[
  {
    "id": "education",
    "name": "Education",
    "icon": "graduation-cap",
    "org_count": 2847
  },
  {
    "id": "health",
    "name": "Health & Research",
    "icon": "heart-pulse",
    "org_count": 3124
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | URL-safe category slug |
| `name` | string | Human-readable name |
| `icon` | string | Icon identifier (frontend has mappings) |
| `org_count` | int | Number of orgs in this category |

**Supported icon values:** `graduation-cap`, `heart-pulse`, `hands-helping`, `palette`, `leaf`, `users`, `paw`, `globe`, `church`, `scale`

---

## GET /api/organizations

List organizations with filtering, sorting, and pagination.

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `search` | string | No | Search by name, city, or EIN |
| `category` | string | No | Filter by category ID |
| `sort` | string | No | `merit_score` (default), `name`, `revenue` |
| `page` | int | No | Page number (default: 1) |
| `per_page` | int | No | Items per page (default: 9) |

### Response

```json
{
  "organizations": [
    {
      "id": "1",
      "name": "United Way Worldwide",
      "ein": "13-1635294",
      "city": "Alexandria",
      "state": "VA",
      "category": "human-services",
      "subcategory": "Human Services",
      "merit_score": 94,
      "revenue": 4800000000,
      "assets": 4200000000,
      "employees": 3200,
      "founded": 1887,
      "mission": "To improve lives by mobilizing the caring power of communities...",
      "programs": ["Education", "Financial Stability", "Health"],
      "leadership": [
        { "name": "Angela F. Williams", "title": "President & CEO", "initials": "AW" }
      ],
      "board_size": 18,
      "revenue_trend": [
        { "year": 2020, "amount": 4100000000 },
        { "year": 2021, "amount": 4500000000 },
        { "year": 2022, "amount": 4700000000 },
        { "year": 2023, "amount": 4800000000 },
        { "year": 2024, "amount": 4900000000 }
      ],
      "program_efficiency": 91,
      "fundraising_ratio": 8,
      "operating_reserve": 11.2,
      "transparency_score": 96
    }
  ],
  "total": 45873,
  "page": 1,
  "per_page": 9,
  "total_pages": 5098
}
```

### Organization Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `name` | string | Organization name |
| `ein` | string | IRS Employer Identification Number |
| `city` | string | City |
| `state` | string | State code (2-letter) |
| `category` | string | Category ID slug |
| `subcategory` | string | Human-readable subcategory |
| `merit_score` | int | 0-100 composite score |
| `revenue` | int | Annual revenue in USD |
| `assets` | int | Total assets in USD |
| `employees` | int | Number of employees |
| `founded` | int | Year founded |
| `mission` | string | Mission statement |
| `programs` | string[] | List of program areas |
| `leadership` | object[] | Key personnel |
| `board_size` | int | Number of board members |
| `revenue_trend` | object[] | 5-year revenue history |
| `program_efficiency` | int | Program spending % |
| `fundraising_ratio` | int | Fundraising cost % |
| `operating_reserve` | float | Months of operating reserve |
| `transparency_score` | int | 0-100 transparency rating |

---

## GET /api/organizations/:id

Get a single organization by ID.

### Response

Same organization object as above. Returns 404 if not found.

```json
{
  "id": "1",
  "name": "United Way Worldwide",
  ...
}
```

---

## Error Responses

All errors should return JSON with a message:

```json
{
  "error": "Organization not found"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request (invalid parameters) |
| 404 | Resource not found |
| 500 | Server error |

---

## Data Types Reference

### Revenue Trend Item

```json
{
  "year": 2024,
  "amount": 4900000000
}
```

### Leadership Entry

```json
{
  "name": "Angela F. Williams",
  "title": "President & CEO",
  "initials": "AW"
}
```

The `initials` field should be 1-2 uppercase letters derived from the person's name.

# AINative Studio API Catalog for AI Agents

## Overview
AINative Studio API catalog: **1,968 endpoints** across **49 categories** for AI-native apps.

## Quick Start for Agents

### 1. Browse by Category

| Category | Focus | Key Endpoints |
|----------|-------|--------------|
| Database & Storage | ZeroDB, File Mgmt | 457 eps |
| AI & Agents | Swarms, Memory | 365 eps |
| User & Admin | Auth, Operations | 464 eps |
| Analytics | Metrics, Tracking | 110 eps |
| Dev Tools | Code Analysis | Multiple |

### 2. Finding Endpoints

**By Task:**
- Auth → `authentication.md`
- Agents → `agents.md`
- Data Storage → `zerodb.md`
- Analytics → `analytics.md`

### 3. Using the Catalog

**Workflow:**
1. Identify category
2. Open `.ainative/api-catalog/{category}.md`
3. Browse endpoints
4. Use request/response schemas

## Catalog Structure

```
.ainative/api-catalog/
├── INDEX.md
├── authentication.md
├── zerodb.md
├── agents.md
└── ... (49 categories)
```

## Syncing Catalog

```bash
/api-catalog-sync
# OR
python3 scripts/catalog_apis.py
```

## Integration Examples

### User Registration
```python
POST /v1/public/auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

### Vector Search
```python
POST /v1/projects/{project_id}/vectors/search
{
  "vector": [0.1, 0.2, 0.3],
  "limit": 10
}
```

## Best Practices
1. Check authentication first
2. Use INDEX.md
3. Reference exact endpoints
4. Handle errors
5. Sync regularly

## Troubleshooting
- Use `/api-catalog-sync`
- Check live API docs
- Search with `grep`

## Quick Reference

| Category | Endpoints | Primary Use |
|----------|-----------|-------------|
| ZeroDB | 457 | Database, Vectors |
| Admin | 438 | Operations |
| Public | 337 | Features |
| Agents | 265 | Swarms |
| Analytics | 110 | Monitoring |

**Total: 1,968 endpoints**
*Sync with `/api-catalog-sync`*
# Railway Deployment Guide

## Service Architecture

### Key Services
1. **kong-gateway** - API Gateway
2. **core** - Python backend (auth, users, billing)
3. **AINative-Community** - Strapi CMS
4. **ainative-postgres** - PostgreSQL DB

### Critical: Deploy Correctly
**ALWAYS deploy backend code to `core` service, NOT kong-gateway!**

## Deployment Commands

### 1. List Services
```bash
railway status --json | jq -r '.services.edges[].node.name'
```

### 2. Identify Backend Service
**"AINative-Core-Production"** is the main Python backend.

**WARNING:** Avoid "core" without prefix!

### 3. Deploy to Core Backend
```bash
# Recommended
railway up --detach --service "AINative-Core-Production"

# Alternative
railway link --service "AINative-Core-Production"
railway up --detach
```

### 4. Check Deployment Status
```bash
railway status --json | jq -r '.services.edges[] | select(.node.name == "core") | .node.serviceInstances.edges[0].node.latestDeployment'
```

## Common Mistakes

❌ **DON'T:** Deploy without service specification
```bash
railway up  # Incorrect!
```

✅ **DO:** Specify service explicitly
```bash
railway up --service core
```

## Verifying Deployment

### 1. Health Check
```bash
curl https://api.ainative.studio/health | jq
```

### 2. Functionality Test
```bash
curl -X POST "https://api.ainative.studio/v1/public/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}'
```

## Troubleshooting

### Service Not Found
**Solution:** List services, use exact name
```bash
railway status --json | jq -r '.services.edges[].node.name'
railway up --service core
```

## Best Practices

1. **Verify service name**
   ```bash
   railway status --json | jq -r '.services.edges[] | select(.node.name == "core")'
   ```

2. **Use explicit service flags**
   ```bash
   railway up --detach --service core
   ```

## Quick Reference

```bash
# Deploy backend
railway up --detach --service "AINative-Core-Production"

# Check services
railway status --json | jq -r '.services.edges[].node | {name, status: .serviceInstances.edges[0].node.latestDeployment.status}'
```

**Remember:** `AINative-Core-Production` handles:
- Authentication
- User management
- Billing
- API keys
- ZeroDB integration

**Kong Gateway** routes requests to services.

**Last Updated:** 2025-12-31
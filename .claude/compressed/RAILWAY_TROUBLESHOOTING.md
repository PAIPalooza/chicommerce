# Railway Configuration & Troubleshooting Guide

## CRITICAL KONG/RAILWAY DEPLOYMENT GUIDELINES

### Network Architecture Constraints
- Kong CANNOT access Railway private network DNS
- ALWAYS use public backend URL: `ainative-browser-builder.up.railway.app:443`
- Internal hostnames will ALWAYS fail

### Service Configuration

#### Backend Service
- **Public URL**: `ainative-browser-builder.up.railway.app`
  - HTTP: `:8080`
  - HTTPS: `:443`
- **Database**: 
  - PgBouncer (port 6432)
  - 20 connection pool (10 base + 10 overflow)

#### Kong Gateway
- **Public URLs**: 
  - `kong-gateway-production-8c94.up.railway.app:8000`
  - `api.ainative.studio:8000`
- **Config File**: `/kong/config/kong.yml`

## Troubleshooting Scenarios

### Scenario 1: 502/503 Errors
1. Check backend health:
   ```bash
   curl -s https://ainative-browser-builder.up.railway.app/health
   ```
2. Verify deployment status:
   ```bash
   railway status --service "AINative- Core -Production"
   railway logs --service "AINative- Core -Production" | tail -100
   ```

### Scenario 2: 404 Errors
1. Verify Kong deployment:
   ```bash
   railway status --service kong-gateway
   railway logs --service kong-gateway | grep -i "declarative"
   ```

### Scenario 3: DNS Resolution Failures
**Solution**: 
```yaml
url: https://ainative-browser-builder.up.railway.app
protocol: https
host: ainative-browser-builder.up.railway.app
port: 443
```

### Scenario 4: Circular Proxy
- NEVER use Kong's URL (`api.ainative.studio`) as upstream
- ALWAYS use backend public URL

### Scenario 5: Database Connection Pool
- Current pool size: 150 connections
- Configured in `src/backend/app/db/session.py`

### Scenario 6: Kong Admin API Limitations
- ❌ Backend CANNOT access Kong Admin API
- ✅ Kong gateway (port 8000) works perfectly

## Deployment Verification

**Verification Steps**:
```bash
# Check Kong headers
curl -I https://api.ainative.studio/health | grep -i kong

# Verify backend health
curl -s https://ainative-browser-builder.up.railway.app/health

# Test API validation
curl -s https://api.ainative.studio/v1/public/auth/login -X POST
```

## Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| DNS resolution failed | Can't resolve internal hostname | Use public URL |
| Upstream connect error | Backend not responding | Check deployment |
| No Route matched | Kong routes misconfigured | Verify kong.yml |
| Invalid upstream response | Circular proxy | Check URLs |
| QueuePool limit reached | DB pool exhausted | Already fixed at 150 |

## CRITICAL: DO NOT MODIFY
- `/kong/config/kong.yml` upstream URL
- `/src/backend/app/db/session.py` pool size
- Railway service names
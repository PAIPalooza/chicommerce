# AgentFlow Railway Deployment Rules

## Critical Configuration

### Environment Variables

```bash
AGENTFLOW_AUTO_LOGIN=false                    # CRITICAL: Must be false in production
AGENTFLOW_API_URL=https://api.ainative.studio # Required for authentication
AGENTFLOW_DATABASE_URL=postgresql://...       # Railway PostgreSQL
```

### Service Info
- **Name**: `AgentFlow`
- **URL**: https://agentflow.ainative.studio
- **Repo**: AINative-Studio/AgentFlow
- **Auto-Deploy**: Yes (main branch)

## Deployment Commands

### Deploy Options
```bash
# Option 1: GitHub Push
git push origin main

# Option 2: Force Redeploy
git commit --allow-empty -m "Force AgentFlow redeploy"
git push origin main

# Option 3: Railway CLI
railway up --detach --service "AgentFlow"
```

### Set Environment Variables
```bash
# Disable AUTO_LOGIN
railway variables --service "AgentFlow" --set "AGENTFLOW_AUTO_LOGIN=false"

# Set API URL
railway variables --service "AgentFlow" --set "AGENTFLOW_API_URL=https://api.ainative.studio"
```

## Verification Checklist

### 1. Deployment Status
```bash
railway status --json | grep -A 10 '"name": "AgentFlow"'
```
Expected: `"status": "SUCCESS"`

### 2. Verify AUTO_LOGIN Disabled
```bash
curl https://agentflow.ainative.studio/api/v1/auto_login
```
Expected: `{"detail":{"message":"Auto login is disabled","auto_login":false}}`

### 3. Health Check
```bash
curl https://agentflow.ainative.studio/health
```
Expected: `{"status":"ok"}`

## Authentication Implementation

```python
async def authenticate_user(username: str, password: str, db: AsyncSession) -> User | None:
    ainative_api_url = os.getenv("AGENTFLOW_API_URL", "https://api.ainative.studio")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ainative_api_url}/v1/public/auth/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10.0
        )
        if response.status_code == 200:
            # Auto-create local user
            ...
```

## ZERO TOLERANCE Rules
1. NEVER set `AGENTFLOW_AUTO_LOGIN=true` in production
2. ALWAYS verify authentication after deployment
3. ALWAYS use `/v1/public/auth/login` endpoint
4. ALWAYS use form-urlencoded content-type

## Production URLs
- **Frontend**: https://agentflow.ainative.studio
- **API**: https://agentflow.ainative.studio/api/v1
- **Docs**: https://agentflow.ainative.studio/docs

## Railway IDs
- **Project ID**: `47539617-ae34-4a52-a010-a88d875f347e`
- **Service ID**: `00744e52-e9eb-4246-8e95-693cae458b06`
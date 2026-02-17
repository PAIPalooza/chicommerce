# Database Query Best Practices - Prevent Connection Pool Exhaustion

## Problem
- Querying Railway DB can cause `psycopg2.OperationalError: too many clients`
- Occurs when multiple dev servers hold open connections
- Connection pool limit: 300 total connections

## Best Practices

### 1. Check Connection Pool Status
```bash
python3 << 'EOF'
import psycopg2

DATABASE_URL = "postgresql://postgres:password@host:port/railway"

try:
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = 'railway'")
    active = cur.fetchone()[0]

    cur.execute("SHOW max_connections")
    max_conn = cur.fetchone()[0]

    print(f"Active connections: {active}/{max_conn}")

    if active > int(max_conn) * 0.9:
        print("WARNING: Connection pool near capacity")

    cur.close()
    conn.close()

except Exception as e:
    print(f"Cannot connect: {e}")
    print("SOLUTION:\n1. Kill dev servers\n2. Wait 30 seconds\n3. Retry")
EOF
```

### 2. Use Context Managers
```python
try:
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    results = cur.fetchall()
finally:
    if cur: cur.close()
    if conn: conn.close()
```

### 3. Short-Lived Connections
```python
def get_user_count():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        cur.close()
        return count
    finally:
        if conn: conn.close()
```

### 4. Kill Dev Servers
```bash
pkill -9 -f "npm run dev"
pkill -9 -f "npm run develop"
sleep 10
python3 scripts/query_script.py
```

### 5. Use Railway CLI (Recommended)
```bash
railway login
railway link
railway run psql -c "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '30 days'"
```

## Emergency: Connection Pool Full

### Option 1: Kill Local Servers
```bash
pkill -9 -f "npm run dev"
pkill -9 node
sleep 30
```

### Option 2: Check Active Connections
```bash
railway run psql -c "
SELECT pid, usename, application_name, client_addr, state, query_start
FROM pg_stat_activity
WHERE datname = 'railway'
ORDER BY query_start DESC
LIMIT 20"
```

### Option 3: Terminate Idle Connections
```bash
railway run psql -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'railway'
  AND state = 'idle'
  AND query_start < NOW() - INTERVAL '10 minutes'"
```

## Pre-Query Checklist
- [ ] Stop dev servers
- [ ] Check connection pool
- [ ] Use try/finally
- [ ] Use short-lived connections
- [ ] Prefer Railway CLI

## Golden Rule
> ALWAYS close database connections immediately.
> NEVER leave connections open during queries.
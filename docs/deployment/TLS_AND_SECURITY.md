# TLS and Security Configuration Deployment Guide

## Overview

This document provides comprehensive guidance for deploying ChiCommerce with TLS/HTTPS enforcement and API key authentication for admin routes. The implementation follows OWASP security best practices and includes multiple layers of security.

## Table of Contents

1. [Security Features](#security-features)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [TLS/HTTPS Setup](#tlshttps-setup)
5. [API Key Management](#api-key-management)
6. [Security Headers](#security-headers)
7. [Deployment Scenarios](#deployment-scenarios)
8. [Testing and Verification](#testing-and-verification)
9. [Troubleshooting](#troubleshooting)
10. [Security Best Practices](#security-best-practices)

## Security Features

### Implemented Security Measures

1. **TLS/HTTPS Enforcement**
   - Automatic HTTP to HTTPS redirection
   - Configurable redirect behavior
   - Support for reverse proxy deployments

2. **Security Headers**
   - HSTS (HTTP Strict Transport Security)
   - Content Security Policy (CSP)
   - X-Content-Type-Options (MIME sniffing prevention)
   - X-Frame-Options (clickjacking protection)
   - X-XSS-Protection
   - Referrer-Policy
   - Permissions-Policy

3. **API Key Authentication**
   - Secure API key generation
   - Header-based authentication (X-API-Key)
   - Protection of all admin endpoints (CREATE, UPDATE, DELETE)
   - Public read access for customer-facing endpoints

## Prerequisites

Before deploying with TLS enabled, ensure you have:

1. **SSL/TLS Certificate**
   - Valid SSL certificate for your domain
   - Certificate chain (intermediate certificates)
   - Private key
   - Or use Let's Encrypt for free certificates

2. **Reverse Proxy** (Recommended)
   - Nginx or Apache for TLS termination
   - ALB/ELB on AWS
   - Cloud Load Balancer on GCP
   - Azure Application Gateway

3. **Environment Access**
   - Ability to set environment variables
   - Access to modify web server configuration
   - Ability to restart services

## Environment Configuration

### Required Environment Variables

Add the following to your `.env` file:

```bash
# Security Settings
TLS_ENABLED=true
HTTPS_REDIRECT_ENABLED=true
SECURITY_HEADERS_ENABLED=true

# HSTS Configuration
HSTS_MAX_AGE=31536000          # 1 year in seconds
HSTS_INCLUDE_SUBDOMAINS=true   # Apply to all subdomains
HSTS_PRELOAD=false             # Set to true only after HSTS preload submission

# Admin API Key (REQUIRED - generate a secure key)
ADMIN_API_KEY=your-secure-admin-api-key-here

# Application Settings
SECRET_KEY=your-application-secret-key
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
```

### Generating Secure API Keys

Use the built-in key generator:

```python
from app.core.security import generate_api_key

# Generate a new API key
api_key = generate_api_key()
print(f"New API Key: {api_key}")
```

Or use command line:

```bash
# Using Python
python3 -c "from app.core.security import generate_api_key; print(generate_api_key())"

# Using OpenSSL
openssl rand -base64 32
```

### Development vs Production Settings

#### Development (.env.development)
```bash
TLS_ENABLED=false              # Allow HTTP in development
HTTPS_REDIRECT_ENABLED=false   # No redirect in development
SECURITY_HEADERS_ENABLED=true  # Still test headers
HSTS_MAX_AGE=0                 # No HSTS in development
```

#### Production (.env.production)
```bash
TLS_ENABLED=true
HTTPS_REDIRECT_ENABLED=true
SECURITY_HEADERS_ENABLED=true
HSTS_MAX_AGE=31536000
HSTS_INCLUDE_SUBDOMAINS=true
HSTS_PRELOAD=false
```

## TLS/HTTPS Setup

### Option 1: Nginx Reverse Proxy (Recommended)

Create `/etc/nginx/sites-available/chicommerce`:

```nginx
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Certificate Configuration
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    # SSL Protocol and Cipher Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Proxy to FastAPI application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/chicommerce /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option 2: Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain and install certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal (certbot sets this up automatically)
sudo certbot renew --dry-run
```

### Option 3: AWS Application Load Balancer

1. **Create ALB with HTTPS listener**
   - Upload SSL certificate to ACM (AWS Certificate Manager)
   - Create target group pointing to EC2 instances
   - Add HTTPS listener on port 443
   - Add HTTP listener on port 80 with redirect to HTTPS

2. **Configure Target Group Health Check**
   ```
   Path: /health
   Port: 8000
   Protocol: HTTP
   ```

3. **Security Group Rules**
   - Inbound: Allow 443 (HTTPS) from 0.0.0.0/0
   - Inbound: Allow 80 (HTTP) from 0.0.0.0/0 (for redirect)
   - Outbound: Allow 8000 to EC2 security group

### Option 4: Docker with Traefik

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.9
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@yourdomain.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"

  chicommerce:
    build: .
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.chicommerce.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.chicommerce.entrypoints=websecure"
      - "traefik.http.routers.chicommerce.tls.certresolver=letsencrypt"
      - "traefik.http.services.chicommerce.loadbalancer.server.port=8000"
    environment:
      - TLS_ENABLED=true
      - HTTPS_REDIRECT_ENABLED=true
```

## API Key Management

### Protecting Admin Endpoints

The following endpoints require API key authentication:

**Products**
- `POST /api/v1/products/` - Create product
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product

**Templates**
- `POST /api/v1/templates/` - Create template
- `PUT /api/v1/templates/{id}` - Update template
- `DELETE /api/v1/templates/{id}` - Delete template

**Option Sets**
- `POST /api/v1/option-sets/` - Create option set
- `PUT /api/v1/option-sets/{id}` - Update option set
- `DELETE /api/v1/option-sets/{id}` - Delete option set

### Using API Keys

Include the API key in the `X-API-Key` header:

```bash
# cURL example
curl -X POST https://api.yourdomain.com/api/v1/products/ \
  -H "X-API-Key: your-admin-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Product", "base_price": 29.99}'

# Python example
import requests

headers = {
    "X-API-Key": "your-admin-api-key-here",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.yourdomain.com/api/v1/products/",
    headers=headers,
    json={"name": "New Product", "base_price": 29.99}
)
```

### API Key Rotation

Best practice: Rotate API keys regularly (e.g., every 90 days)

```bash
# 1. Generate new key
new_key=$(python3 -c "from app.core.security import generate_api_key; print(generate_api_key())")

# 2. Update environment variable
echo "ADMIN_API_KEY=$new_key" >> .env

# 3. Restart application
sudo systemctl restart chicommerce

# 4. Update all admin clients with new key

# 5. Monitor for failed auth attempts (old key usage)
```

## Security Headers

### Configured Headers

The application automatically adds the following security headers to all responses:

1. **Strict-Transport-Security (HSTS)**
   ```
   Strict-Transport-Security: max-age=31536000; includeSubDomains
   ```
   - Enforces HTTPS for 1 year
   - Applies to all subdomains

2. **Content-Security-Policy (CSP)**
   ```
   Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; ...
   ```
   - Prevents XSS attacks
   - Restricts resource loading

3. **X-Content-Type-Options**
   ```
   X-Content-Type-Options: nosniff
   ```
   - Prevents MIME type sniffing

4. **X-Frame-Options**
   ```
   X-Frame-Options: DENY
   ```
   - Prevents clickjacking

5. **X-XSS-Protection**
   ```
   X-XSS-Protection: 1; mode=block
   ```
   - Legacy XSS protection

6. **Referrer-Policy**
   ```
   Referrer-Policy: strict-origin-when-cross-origin
   ```
   - Controls referrer information

### Customizing CSP

To modify the Content Security Policy for your specific needs, edit `/app/middleware/security.py`:

```python
# Example: Allow images from CDN
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https: https://cdn.yourdomain.com; "  # Modified
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'"
)
```

## Deployment Scenarios

### Scenario 1: Single Server Deployment

```bash
# 1. Install dependencies
sudo apt-get update
sudo apt-get install nginx python3-pip postgresql redis-server

# 2. Setup application
cd /opt/chicommerce
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with production values

# 4. Setup database
alembic upgrade head

# 5. Configure Nginx (see above)

# 6. Create systemd service
sudo nano /etc/systemd/system/chicommerce.service
```

Service file content:
```ini
[Unit]
Description=ChiCommerce API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/chicommerce
Environment="PATH=/opt/chicommerce/venv/bin"
ExecStart=/opt/chicommerce/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 7. Start services
sudo systemctl enable chicommerce
sudo systemctl start chicommerce
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### Scenario 2: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TLS_ENABLED=true
      - HTTPS_REDIRECT_ENABLED=true
      - SECURITY_HEADERS_ENABLED=true
      - ADMIN_API_KEY=${ADMIN_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: chicommerce
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Scenario 3: Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chicommerce
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chicommerce
  template:
    metadata:
      labels:
        app: chicommerce
    spec:
      containers:
      - name: chicommerce
        image: chicommerce:latest
        ports:
        - containerPort: 8000
        env:
        - name: TLS_ENABLED
          value: "true"
        - name: HTTPS_REDIRECT_ENABLED
          value: "true"
        - name: SECURITY_HEADERS_ENABLED
          value: "true"
        - name: ADMIN_API_KEY
          valueFrom:
            secretKeyRef:
              name: chicommerce-secrets
              key: admin-api-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: chicommerce-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: chicommerce-service
spec:
  selector:
    app: chicommerce
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: chicommerce-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: chicommerce-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: chicommerce-service
            port:
              number: 80
```

## Testing and Verification

### 1. Test HTTPS Redirection

```bash
# Test HTTP redirect
curl -I http://api.yourdomain.com/health
# Should return 301/302/308 redirect to HTTPS

# Test HTTPS access
curl -I https://api.yourdomain.com/health
# Should return 200 OK
```

### 2. Verify Security Headers

```bash
curl -I https://api.yourdomain.com/health

# Check for headers:
# - Strict-Transport-Security
# - Content-Security-Policy
# - X-Content-Type-Options
# - X-Frame-Options
# - X-XSS-Protection
# - Referrer-Policy
```

### 3. Test API Key Authentication

```bash
# Test without API key (should fail with 401)
curl -X POST https://api.yourdomain.com/api/v1/products/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'

# Test with invalid API key (should fail with 403)
curl -X POST https://api.yourdomain.com/api/v1/products/ \
  -H "X-API-Key: invalid-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'

# Test with valid API key (should succeed with 201)
curl -X POST https://api.yourdomain.com/api/v1/products/ \
  -H "X-API-Key: your-valid-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "base_price": 10.00}'
```

### 4. SSL/TLS Testing

Use online tools:
- [SSL Labs](https://www.ssllabs.com/ssltest/) - Comprehensive SSL/TLS test
- [Security Headers](https://securityheaders.com/) - Security headers analysis
- [Mozilla Observatory](https://observatory.mozilla.org/) - Overall security scan

### 5. Automated Testing

Run the test suite:
```bash
# Run security tests
pytest tests/api/test_security.py -v

# Run with coverage
pytest tests/api/test_security.py --cov=app/middleware --cov=app/core/security -v
```

## Troubleshooting

### Issue: HTTP requests not redirecting to HTTPS

**Solution 1: Check middleware configuration**
```python
# In app/main.py, verify:
app.add_middleware(
    HTTPSRedirectMiddleware,
    enabled=settings.HTTPS_REDIRECT_ENABLED,  # Should be True
)
```

**Solution 2: Verify environment variable**
```bash
echo $HTTPS_REDIRECT_ENABLED  # Should output 'true'
```

**Solution 3: Check reverse proxy headers**
```nginx
# Nginx must set X-Forwarded-Proto
proxy_set_header X-Forwarded-Proto $scheme;
```

### Issue: Security headers not appearing

**Solution: Verify middleware order**
```python
# SecurityHeadersMiddleware must be added BEFORE other middleware
app.add_middleware(SecurityHeadersMiddleware, ...)
app.add_middleware(CORSMiddleware, ...)  # Add after security middleware
```

### Issue: API key authentication failing

**Solution 1: Verify header name**
```bash
# Correct header name is "X-API-Key" (case-insensitive)
curl -H "X-API-Key: your-key" ...
```

**Solution 2: Check environment variable**
```bash
# Verify ADMIN_API_KEY is set
echo $ADMIN_API_KEY
```

**Solution 3: Check logs for details**
```bash
journalctl -u chicommerce -f  # For systemd
docker logs -f chicommerce    # For Docker
kubectl logs -f deployment/chicommerce  # For Kubernetes
```

### Issue: HSTS preventing access to development server

**Solution: Clear HSTS in browser**

Chrome/Edge:
1. Visit `chrome://net-internals/#hsts`
2. Enter domain in "Delete domain security policies"
3. Click "Delete"

Firefox:
1. Close all Firefox windows
2. Delete `SiteSecurityServiceState.txt` from profile directory

## Security Best Practices

### 1. API Key Management

- **Never commit API keys to version control**
  ```bash
  # Add to .gitignore
  .env
  .env.*
  !.env.example
  ```

- **Use environment-specific keys**
  - Development: Short-lived, easily rotatable
  - Staging: Separate from production
  - Production: Long, random, rotated regularly

- **Monitor API key usage**
  - Log authentication attempts
  - Alert on repeated failures
  - Track key usage per client

### 2. TLS/SSL Configuration

- **Use TLS 1.2 or higher**
  - Disable TLS 1.0 and 1.1
  - Prefer TLS 1.3 when available

- **Regular certificate renewal**
  - Set up auto-renewal for Let's Encrypt
  - Monitor certificate expiration
  - Maintain certificate chain properly

- **Perfect Forward Secrecy**
  - Use ECDHE cipher suites
  - Disable weak ciphers (RC4, 3DES)

### 3. HSTS Configuration

- **Gradual rollout**
  ```bash
  # Start with short max-age
  HSTS_MAX_AGE=300  # 5 minutes

  # Increase gradually
  HSTS_MAX_AGE=86400  # 1 day
  HSTS_MAX_AGE=604800  # 1 week
  HSTS_MAX_AGE=31536000  # 1 year
  ```

- **HSTS Preloading**
  - Only enable after successful 1-year deployment
  - Submit to [hstspreload.org](https://hstspreload.org/)
  - Understand it's permanent (difficult to remove)

### 4. Monitoring and Logging

- **Log security events**
  - Failed authentication attempts
  - API key usage
  - HTTPS redirect triggers
  - Certificate warnings

- **Set up alerts**
  - Repeated authentication failures
  - Unusual API usage patterns
  - Certificate expiration warnings
  - TLS version downgrades

### 5. Defense in Depth

- **Multiple security layers**
  - Network: Firewall, security groups
  - Application: API keys, HTTPS
  - Data: Encryption at rest
  - Infrastructure: Regular updates, hardening

- **Rate limiting**
  ```python
  # Consider adding rate limiting middleware
  from slowapi import Limiter
  limiter = Limiter(key_func=get_remote_address)
  ```

- **Web Application Firewall (WAF)**
  - Use AWS WAF, Cloudflare, or similar
  - Protect against common attacks (SQL injection, XSS)

## Conclusion

Following this deployment guide ensures that your ChiCommerce application is deployed with enterprise-grade security:

- All traffic encrypted with TLS
- Admin operations protected with API key authentication
- Comprehensive security headers protecting against common attacks
- Multiple deployment scenarios supported
- Robust testing and verification procedures

For additional security concerns or questions, consult the development team or your security officer.

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Mozilla Web Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/advanced/security/)

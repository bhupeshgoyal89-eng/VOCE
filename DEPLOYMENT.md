# 🚀 VOCE Deployment & Configuration Guide

## System Requirements

- **Python:** 3.8 or higher
- **OS:** macOS, Linux, or Windows
- **RAM:** Minimum 2GB (4GB recommended)
- **Disk:** Minimum 500MB for application + file storage
- **Internet:** Required for Google Gemini API calls

## Installation Methods

### Method 1: Local Development (Recommended for Testing)

```bash
# 1. Clone/Navigate to project
cd /path/to/VOCE

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variable
export GEMINI_API_KEY="your_key_here"

# 5. Run application
streamlit run app.py
```

### Method 2: Using Docker (Enterprise Deployment)

**Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_CLIENT_BROWSER=false

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

**Build and Run:**
```bash
docker build -t voce:latest .
docker run -p 8501:8501 \
  -e GEMINI_API_KEY="your_key" \
  -v /path/to/data:/app/data \
  -v /path/to/agreements:/app/agreements \
  voce:latest
```

### Method 3: Using Docker Compose (Multi-Service)

**Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  voce:
    build: .
    ports:
      - "8501:8501"
    environment:
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      VOCE_DB_PATH: /app/data/voce.db
    volumes:
      - ./data:/app/data
      - ./agreements:/app/agreements
    restart: unless-stopped
```

**Run:**
```bash
docker-compose up -d
```

## Environment Configuration

### Development Environment

```bash
# .env file
GEMINI_API_KEY=your_dev_key
LOG_LEVEL=DEBUG
STREAMLIT_SERVER_PORT=8501
```

### Production Environment

```bash
# .env.production
GEMINI_API_KEY=your_prod_key
LOG_LEVEL=INFO
STREAMLIT_SERVER_PORT=80  # or 443 with HTTPS
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_CLIENT_BROWSER=false
```

## Configuration Files

### streamlit/config.toml (Optional)

Create `.streamlit/config.toml` for Streamlit settings:

```toml
[client]
showErrorDetails = false

[server]
headless = false
port = 8501
maxUploadSize = 200  # MB

[logger]
level = "info"

[theme]
primaryColor = "#003366"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#333333"
font = "sans serif"
```

## Database Configuration

### SQLite (Default - Recommended for Prototyping)

```python
# Configured in database.py
db_path = "data/voce.db"  # Auto-created
```

### PostgreSQL (For Production)

1. **Install PostgreSQL client:**
   ```bash
   pip install psycopg2-binary
   ```

2. **Modify database.py:**
   ```python
   import psycopg2
   
   class Database:
       def __init__(self, db_url):
           self.conn = psycopg2.connect(db_url)
   ```

3. **Set environment:**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/voce"
   ```

## Security Configuration

### 1. API Key Management

```bash
# Using environment variables (Recommended)
export GEMINI_API_KEY="sk-..."

# Using .env file (Development only)
# Create .env file (never commit to git)
GEMINI_API_KEY=your_key

# Using secrets manager (Production)
# AWS Secrets Manager, Azure Key Vault, etc.
```

### 2. Add .gitignore

```
# Environment files
.env
.env.local
.env.*.local

# Database
data/
*.db
*.db-journal

# Uploaded files
agreements/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store
```

### 3. Restrict File Access

```bash
# Set proper permissions
chmod 700 data/
chmod 700 agreements/
chmod 600 .env
```

### 4. Add Authentication (Optional)

For production, add Streamlit authentication:

```bash
pip install streamlit-authenticator
```

Example:

```python
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(...)
name, authentication_status, username = authenticator.login()

if authentication_status:
    # Show app
    pass
else:
    st.error("Invalid credentials")
```

## Performance Tuning

### 1. Cache Configuration

```python
# In app.py - Already implemented
@st.cache_resource
def get_database():
    return Database()
```

### 2. Database Optimization

```sql
-- Create indexes for faster queries
CREATE INDEX idx_vendor_id ON vendors(vendor_id);
CREATE INDEX idx_vendor_name ON vendors(vendor_name);
CREATE INDEX idx_obligation_vendor ON obligations(vendor_id);
CREATE INDEX idx_cert_vendor ON certifications(vendor_id);
```

### 3. Streamlit Configuration

```toml
# .streamlit/config.toml
[client]
maxMessageSize = 200

[logger]
level = "warning"

[cache]
maxEntries = 1000
```

## Monitoring & Logging

### 1. Application Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voce.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Monitor Health

```bash
# Check Gemini API availability
curl -X GET "https://generativelanguage.googleapis.com/v1/models:list" \
  -H "x-goog-api-key: $GEMINI_API_KEY"

# Check database
sqlite3 data/voce.db "SELECT COUNT(*) FROM vendors;"
```

## Backup & Recovery

### 1. Backup Strategy

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp data/voce.db $BACKUP_DIR/voce_$DATE.db

# Backup agreements
tar -czf $BACKUP_DIR/agreements_$DATE.tar.gz agreements/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -mtime +30 -delete
```

### 2. Restore from Backup

```bash
# Restore database
cp backups/voce_20260301_120000.db data/voce.db

# Restore agreements
tar -xzf backups/agreements_20260301_120000.tar.gz
```

## Troubleshooting Deployment

### Port Already in Use

```bash
# Change port
streamlit run app.py --server.port 8502
```

### Out of Memory

```bash
# Reduce cache
streamlit run app.py --logger.level=warning --client.maxMessageSize=100
```

### Database Lock

```bash
# Remove lock file
rm -f data/voce.db-shm
rm -f data/voce.db-wal

# Or reset database
rm -f data/voce.db
```

### API Rate Limiting

```python
# In ai_parser.py - Add retry logic
import time

def extract_obligations_with_retry(self, text, max_retries=3):
    for attempt in range(max_retries):
        try:
            return self.extract_obligations(text)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

## Performance Benchmarks

### Expected Performance

- **Vendor Upload:** 1000 vendors in ~5 seconds
- **PDF Text Extraction:** 10 pages in ~2 seconds
- **Gemini Obligation Extraction:** ~15-30 seconds per agreement
- **Database Queries:** <100ms for 1000 records
- **Dashboard Load:** <2 seconds

### Scalability

- **SQLite:** Supports up to 100K records efficiently
- **For larger data:** Migrate to PostgreSQL
- **Concurrent Users:** Streamlit Cloud/on-premises can handle 10-50 concurrent users

## Production Checklist

- [ ] Environment variables configured
- [ ] GEMINI_API_KEY set and tested
- [ ] Database backed up regularly
- [ ] Agreements directory mounted on persistent storage
- [ ] Error logging configured
- [ ] Monitoring/alerting set up
- [ ] Security hardened (HTTPS, authentication)
- [ ] Rate limiting configured
- [ ] Backup/recovery tested
- [ ] Performance benchmarked
- [ ] User documentation ready
- [ ] Training completed

## Support & Troubleshooting

### Get Logs

```bash
# Streamlit logs (terminal)
streamlit run app.py --logger.level=debug

# Database logs
sqlite3 data/voce.db ".log stdout"

# System logs (Linux)
journalctl -u voce-service -n 50
```

### Contact Support

- Check terminal output for error messages
- Review README.md and QUICKSTART.md
- Check firewall settings for port 8501
- Verify API key validity

---

**Version:** 1.0.0
**Last Updated:** March 2026

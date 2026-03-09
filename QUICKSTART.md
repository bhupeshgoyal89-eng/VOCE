# 🚀 VOCE Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
cd /path/to/VOCE
pip install -r requirements.txt
```

### 2. Set Gemini API Key
```bash
export GEMINI_API_KEY="your_key_here"
```

### 3. Run the Application
```bash
streamlit run app.py
```

### 4. Access the Web Interface
- Open browser to: `http://localhost:8501`
- You'll see the VOCE home page

## First Time Workflow

### Phase 1: Upload Vendor Data (2 min)
1. Click **📦 Vendor Master** in sidebar
2. Download the CSV template
3. Use `sample_vendors.csv` provided, or create your own
4. Click "Upload Vendors"
5. Confirm: "Successfully added X vendor(s)"

### Phase 2: Upload an Agreement (3 min)
1. Click **📄 Agreement Upload** in sidebar
2. Select a vendor from dropdown (e.g., "Acme Corporation")
3. Create a test agreement file:
   - Save as `test_agreement.txt`
   - Content can be any text describing terms and obligations
4. Upload the file
5. Click "Process Agreement"
6. Wait for Gemini to analyze (requires API key set)
7. See extracted obligations

### Phase 3: Review Results (2 min)
1. Click **📋 Obligation Register** in sidebar
2. View the extracted obligations in table
3. Click "View Full Details" to see details
4. Review fields like payment terms, SLAs, security requirements

### Phase 4: Certify (1 min)
1. Click **✅ HoD Certification** in sidebar
2. Select the vendor
3. Enter your name as "Head of Department"
4. Select "Confirmed" status
5. Click "Save Certification"

### Phase 5: Check Dashboard (1 min)
1. Click **📊 FP&A Dashboard** in sidebar
2. See metrics updated with your data
3. View charts showing vendor distribution

## Sample Test Data

A `sample_vendors.csv` file is included with 10 test vendors across different departments.

### Create Test Agreement File

**test_agreement.txt:**
```
SERVICE AGREEMENT

Vendor: Acme Corporation
Term: 12 months from January 1, 2024

SCOPE OF WORK:
- Provide software licensing and support services
- Include maintenance and bug fixes
- Deliver quarterly updates

SERVICE LEVELS:
- 99.5% uptime guarantee
- Response time: 4 hours for critical issues
- Resolution time: 24 hours for critical issues

PAYMENT TERMS:
- Monthly invoicing
- Payment due within 30 days of invoice
- Price: $10,000 per month

DATA SECURITY:
- ISO 27001 certification required
- Annual security audits
- Data encryption for all transfers

KPIs:
- Customer satisfaction score > 90%
- Monthly uptime > 99.5%
- Bug resolution rate > 95%

PENALTIES:
- SLA breach: $500 per incident
- Failure to deliver updates: $1,000
```

## File Structure After Usage

```
VOCE/
├── data/
│   └── voce.db                 # SQLite database (auto-created)
├── agreements/
│   ├── test_agreement.txt      # Uploaded files
│   └── [other agreements]
├── app.py
├── database.py
├── ai_parser.py
├── agreement_parser.py
├── models.py
├── utils.py
├── requirements.txt
├── README.md
└── sample_vendors.csv
```

## Common Commands

### Reset Everything (Start Fresh)
```bash
rm -f data/voce.db
rm -f agreements/*
streamlit run app.py
```

### View Database (SQLite CLI)
```bash
sqlite3 data/voce.db
> SELECT * FROM vendors;
> SELECT COUNT(*) FROM obligations;
> .quit
```

### Check Logs
```bash
# Streamlit runs in terminal, check terminal output for errors
# Most errors appear in both terminal and on web page
```

## Troubleshooting

### "GEMINI_API_KEY not set" warning
- This is expected if you haven't set the API key
- Obligation extraction won't work without it
- Get key from: https://makersuite.google.com/app/apikey

### Upload fails with "File format error"
- Ensure file is: PDF, DOCX, or TXT
- For TXT files, use UTF-8 encoding

### No data appears after upload
- Check terminal for error messages
- Verify CSV has all required columns
- Try sample_vendors.csv first

### Database appears locked
- Stop Streamlit (Ctrl+C)
- Delete: `data/voce.db`
- Restart: `streamlit run app.py`

## Environment Variables

```bash
# Required for AI extraction
export GEMINI_API_KEY="your_api_key"

# Optional: Change database location
export VOCE_DB_PATH="data/voce.db"

# Optional: Change upload directory
export VOCE_AGREEMENTS_DIR="agreements"
```

## Testing Checklist

- [ ] App starts without errors
- [ ] Vendor Master CSV uploads successfully
- [ ] Vendor list displays in table
- [ ] Can select vendor in Agreement Upload
- [ ] Can upload test agreement file
- [ ] Obligation extraction completes (if API key set)
- [ ] Obligations appear in Obligation Register
- [ ] Can save certification
- [ ] Dashboard shows updated metrics

## Next Steps

1. ✅ Complete first-time setup above
2. 📚 Read detailed README.md for advanced features
3. 🔑 Set up persistent GEMINI_API_KEY in .bashrc or .zshrc
4. 📊 Upload real vendor data and agreements
5. 🚀 Deploy to production (with authentication)

## Key Features Quick Reference

| Feature | Page | Purpose |
|---------|------|---------|
| Upload CSVs | Vendor Master | Manage vendor data |
| Extract text | Agreement Upload | Read agreement files |
| Parse with AI | Agreement Upload | Use Gemini for extraction |
| Search obligations | Obligation Register | Find specific obligations |
| Validate data | HoD Certification | Confirm or flag issues |
| Monitor metrics | FP&A Dashboard | See KPIs and trends |

## API Rate Limits

Google Gemini API has rate limits:
- Free tier: ~60 requests per minute
- Paid tier: Much higher limits

If you hit rate limits:
- Wait a few minutes
- Contact Google for higher limits
- Implement queue/batch processing

## Production Deployment

For production use:
1. Add user authentication
2. Use PostgreSQL instead of SQLite
3. Implement API key rotation
4. Add input validation/sanitization
5. Enable HTTPS
6. Add backup/recovery procedures
7. Implement audit logging
8. Add monitoring and alerting

---

**Happy Vendor Tracking! 🎉**

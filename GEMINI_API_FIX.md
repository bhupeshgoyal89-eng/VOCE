# ⚠️ Gemini API Extraction Failing - Troubleshooting Guide

## Issue
When uploading agreements for obligation extraction, you see:
```
WARNING:ai_parser:Extraction failed, returning empty structure

All obligation fields return None (agreement_type, scope_of_work, etc.)
```

## Root Cause
The Gemini API is not being called successfully. This is typically due to one of these issues:

### 1. **GEMINI_API_KEY Not Set in Streamlit Cloud Secrets** (Most Common)
The API key is missing from the Streamlit Cloud environment.

**Fix:**
1. Go to https://share.streamlit.io
2. Click on your "VOCE" app
3. Click 3 dots → **Settings**
4. Scroll to **"Secrets"**
5. Click **"Edit secrets"**
6. Add:
   ```
   GEMINI_API_KEY = "your-actual-api-key-from-google"
   ```
7. Save (app will restart)

**Get your API key:**
- Go to https://makersuite.google.com/app/apikey
- Click "Create API Key"
- Copy the key

### 2. **API Key is Invalid or Expired**
The API key exists but is invalid or has expired.

**Fix:**
1. Go to https://makersuite.google.com/app/apikey
2. Verify your API key is still active
3. If expired, create a new one
4. Update it in Streamlit Cloud Secrets

### 3. **Gemini API Quota Exceeded**
You've exceeded the free tier usage limits.

**Check your quota:**
1. Go to Google Cloud Console: https://console.cloud.google.com
2. Check your Gemini API usage
3. Either wait for quota reset or upgrade to paid plan

### 4. **Network or Connectivity Issue**
Streamlit Cloud can't reach Google API servers.

**Fix:**
- This is rare but wait a few minutes and try again
- Check Streamlit Cloud status at https://status.streamlit.io

## How to Diagnose

### Check Streamlit Cloud Logs
1. Go to https://share.streamlit.app
2. Click on VOCE app
3. Look at the Logs section for error messages
4. Look for:
   - `GEMINI_API_KEY environment variable not set!` → Key missing
   - `Empty response from Gemini API` → API issue
   - `Error calling Gemini API` → Connection/quota issue

### Test Locally
```bash
cd /Users/bhupesh.goyal/VOCE

# Set API key
export GEMINI_API_KEY="your-api-key"

# Run app
streamlit run app.py
```

Then try uploading an agreement. Check console output for detailed error messages.

### Check API Key Format
Make sure the key in Streamlit Secrets looks like:
```
AIza... (about 39 characters)
```

**NOT:**
- With quotes: `GEMINI_API_KEY = "AIza..."`
- Multiple lines
- Extra spaces

## Expected Behavior

### With API Key Working ✅
```
Starting obligation extraction with fallback...
Initializing Gemini with API key: AIza123456...
Gemini model initialized successfully
Sending request to Gemini API with 2299 characters
Gemini response: {"agreement_type": "Software License Agreement", ...}
Successfully parsed obligations: ['agreement_type', 'agreement_term', ...]
Extraction successful. Fields extracted:
  agreement_type: Software License Agreement...
  scope_of_work: Provision of cloud storage services...
  service_levels: 99.9% uptime SLA...
```

### Without API Key ❌
```
GEMINI_API_KEY environment variable not set!
Extraction failed, returning empty structure
IMPORTANT: Make sure GEMINI_API_KEY is set in Streamlit Cloud Secrets!
```

## What This Feature Does

The **Agreement Upload** page:
1. Accepts PDF, DOCX, or TXT files
2. Extracts text from the document
3. Sends text to Gemini API for AI analysis
4. Extracts structured obligations including:
   - Agreement type
   - Agreement term/duration
   - Scope of work
   - Service levels (SLAs)
   - Penalties for breach
   - Reporting obligations
   - KPIs and commitments
   - Data security requirements
   - Payment terms
   - Key milestones
   - Dependencies
   - Billing arrangements

## Current Status

✅ **Confirmation tracking working** - Vendors can be confirmed  
✅ **FP&A Dashboard metrics working** - Shows confirmation counts  
❌ **Gemini extraction failing** - Need to verify API key

## Next Steps

1. **Verify GEMINI_API_KEY is set** in Streamlit Cloud Secrets
2. **Hard refresh browser** (Cmd+Shift+R)
3. **Upload test agreement** and check logs for errors
4. **Share logs** if still failing

---

**Status:** Requires GEMINI_API_KEY configuration in Streamlit Cloud  
**Documentation:** See Streamlit Secrets setup at https://docs.streamlit.io/deploy/streamlit-cloud/deploy-your-app/secrets-management

# 🧪 VOCE Testing Guide

## Test Environment Setup

### Prerequisites
```bash
# Python 3.8+
python --version

# Virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Test Data Available
- `sample_vendors.csv` - 10 vendors across departments
- `sample_agreement.txt` - Realistic SLA document

---

## 🏠 Feature Testing Checklist

### 1. Home Page
**Test Steps:**
1. [ ] Launch app: `streamlit run app.py`
2. [ ] Verify landing page displays
3. [ ] Check sidebar navigation visible
4. [ ] Verify all 6 pages listed
5. [ ] Check API key status indicator

**Expected:**
- Home page with feature overview
- Sidebar with all navigation items
- API status (green or warning)
- System status showing 0 vendors/agreements initially

---

### 2. Vendor Master Page

#### Upload CSV Test
**Test Steps:**
1. [ ] Click "📦 Vendor Master"
2. [ ] Click "Upload Vendors" button
3. [ ] Select `sample_vendors.csv`
4. [ ] Preview displays correct columns
5. [ ] Click "Upload Vendors"
6. [ ] Success message shows "Added 10 vendors"

**Expected Output:**
```
✅ Successfully added 10 vendor(s)
```

**Validate:**
```bash
sqlite3 data/voce.db "SELECT COUNT(*) FROM vendors;"
# Should return: 10
```

#### Filter Test
**Test Steps:**
1. [ ] Stay on Vendor Master page
2. [ ] Open "Filter by Department"
3. [ ] Select a department (e.g., "IT")
4. [ ] Verify table shows only IT vendors
5. [ ] Test search box with vendor name
6. [ ] Verify search filters results

**Expected:**
- IT department shows: Acme Corporation, Cloud Systems Corp, Tech Solutions Inc
- Search for "Acme" shows only Acme Corporation

#### Download Template Test
**Test Steps:**
1. [ ] Click "Download Template" button
2. [ ] Verify CSV file downloads
3. [ ] Open CSV in editor
4. [ ] Verify all 8 required columns present

---

### 3. Agreement Upload Page

#### File Upload Test
**Test Steps:**
1. [ ] Click "📄 Agreement Upload"
2. [ ] Select vendor from dropdown
3. [ ] Upload `sample_agreement.txt`
4. [ ] Verify file info displays
5. [ ] Click "Process Agreement"

**Expected Timeline:**
- File saved: 1-2 seconds
- Text extracted: 1-2 seconds
- Gemini analysis: 15-30 seconds (if API key set)

**Expected Outputs:**
```
✅ File saved: agreements/sample_agreement.txt
✅ Extracted XXX characters
✅ Obligations extracted and saved!
```

#### Text Extraction Test
**Test Steps:**
1. [ ] Create test file `test.pdf` or `test.docx`
2. [ ] Upload via Agreement page
3. [ ] Verify text extraction works
4. [ ] Check agreements/ directory for file

**Supported Formats:**
- [ ] PDF extraction works
- [ ] DOCX extraction works
- [ ] TXT extraction works

#### Obligation Extraction Test
**Test Steps:**
1. [ ] Ensure GEMINI_API_KEY is set
2. [ ] Upload sample_agreement.txt
3. [ ] Wait for Gemini analysis
4. [ ] Verify 13 obligation fields extracted:

**Expected Fields Populated:**
- [ ] agreement_type: "Technology Services Agreement"
- [ ] agreement_term: "24 months"
- [ ] scope_of_work: "Provide enterprise software..."
- [ ] service_levels: "99.5% uptime..."
- [ ] penalties_for_breach: "SLA breach: $500..."
- [ ] payment_obligations: "Monthly service fee: $10,000..."
- [ ] billing_status: "Monthly billing cycle..."
- [ ] (Others may be populated based on document)

**Validate in Database:**
```bash
sqlite3 data/voce.db "SELECT * FROM obligations LIMIT 1;"
```

---

### 4. Obligation Register Page

#### Browse Obligations Test
**Test Steps:**
1. [ ] Click "📋 Obligation Register"
2. [ ] Table displays with 1 row (if you uploaded 1 agreement)
3. [ ] Verify columns visible:
   - vendor_name
   - department
   - scope_of_work
   - service_levels
   - payment_terms
   - billing_status

**Expected:**
- Row shows vendor name and extracted obligation data
- Scrollable table for large datasets

#### Search Functionality Test
**Test Steps:**
1. [ ] Type in search box: "payment"
2. [ ] Verify results filter to matching obligations
3. [ ] Type "uptime"
4. [ ] Verify matches service_levels fields
5. [ ] Clear search, verify all restored

**Expected Behavior:**
- Search matches vendor name, scope, payment terms
- Results update real-time
- Case-insensitive search

#### Detailed View Test
**Test Steps:**
1. [ ] Select obligation from dropdown
2. [ ] View full details in expandable section
3. [ ] Verify all fields displayed
4. [ ] Check formatting is readable

---

### 5. HoD Certification Page

#### Certification Form Test
**Test Steps:**
1. [ ] Click "✅ HoD Certification"
2. [ ] Select a vendor from dropdown
3. [ ] Verify associated obligations display
4. [ ] Enter "John Smith" as HOD name
5. [ ] Select "Confirmed" status
6. [ ] Type comment: "Obligations verified"
7. [ ] Click "Save Certification"

**Expected:**
```
✅ Certification saved for [vendor_name]
```

#### Status Indicators Test
**Test Steps:**
1. [ ] Return to certification page
2. [ ] Create certification with "Confirmed" status
3. [ ] Verify green success box displays
4. [ ] Create another with "Suggested Edit"
5. [ ] Verify yellow warning box displays
6. [ ] Create another with "Flagged"
7. [ ] Verify red error box displays

**Expected Colors:**
- Confirmed: Green (#d4edda)
- Suggested Edit: Yellow (#fff3cd)
- Flagged: Red (#f8d7da)

#### Certification History Test
**Test Steps:**
1. [ ] Scroll to "Certification History" section
2. [ ] Verify previous certifications display
3. [ ] Check timestamp is current
4. [ ] Update certification for same vendor
5. [ ] Verify history updated

**Validate in Database:**
```bash
sqlite3 data/voce.db "SELECT COUNT(*) FROM certifications;"
```

---

### 6. FP&A Dashboard Page

#### Metrics Display Test
**Test Steps:**
1. [ ] Click "📊 FP&A Dashboard"
2. [ ] Verify 6 metrics displayed:
   - [ ] Total Vendors (should be 10)
   - [ ] Active Vendors (should be 7)
   - [ ] Agreements (should be 1+)
   - [ ] Obligations (should be 1+)
   - [ ] Pending Certifications
   - [ ] Flagged Issues

**Expected Values (After Full Workflow):**
- Total Vendors: 10
- Active Vendors: 7
- Agreements: 1
- Obligations: 1
- Pending Certs: 9
- Flagged Issues: 0-1

#### Charts Test
**Test Steps:**
1. [ ] Verify "Vendors by Department" chart displays
2. [ ] Verify bars represent department counts
3. [ ] Verify "Obligations by Billing Status" chart
4. [ ] Add more agreements, verify charts update

**Expected:**
- Charts render without errors
- Bar heights reflect data
- Charts are interactive (hover tooltip)

#### Certification Summary Test
**Test Steps:**
1. [ ] Review "Certification Status Summary"
2. [ ] Verify counts for each status
3. [ ] Check against certifications table

**Expected Metrics:**
- Confirmed: Count of confirmed
- Suggested Edit: Count pending edits
- Flagged: Count of flagged items

#### Recent Certifications Test
**Test Steps:**
1. [ ] Scroll to "Recent Certifications"
2. [ ] Verify latest 10 certifications display
3. [ ] Check timestamps are current
4. [ ] Verify HOD names display correctly

---

## 🔧 Integration Tests

### Complete Workflow Test
**Objective:** Test entire end-to-end flow

**Steps:**
1. [ ] Start fresh: Delete data/voce.db
2. [ ] Restart app
3. [ ] Upload vendors from sample_vendors.csv
4. [ ] Verify 10 vendors in database
5. [ ] Upload sample_agreement.txt
6. [ ] Wait for Gemini extraction
7. [ ] View obligations in register
8. [ ] Certify a vendor as "Confirmed"
9. [ ] Certify another as "Flagged"
10. [ ] Check dashboard metrics
11. [ ] Export data (test if available)

**Success Criteria:**
- [ ] All steps complete without errors
- [ ] Data persists in database
- [ ] Dashboard reflects all changes
- [ ] No error messages in terminal

---

## 🐛 Error Handling Tests

### Missing Gemini API Key
**Test:**
1. [ ] Unset GEMINI_API_KEY: `unset GEMINI_API_KEY`
2. [ ] Restart app
3. [ ] Try to upload agreement

**Expected:**
- Warning message displays
- File still uploads
- Obligation extraction skipped
- No crash

### Invalid File Upload
**Test:**
1. [ ] Try to upload .exe file
2. [ ] Try to upload corrupted PDF
3. [ ] Try empty file

**Expected:**
- Error message displays
- Application continues working
- Error logged to terminal

### Invalid CSV Format
**Test:**
1. [ ] Create CSV missing required columns
2. [ ] Try to upload

**Expected:**
```
Missing required columns: [list of columns]
```

### Database Lock
**Test:**
1. [ ] Open database in SQLite while app running
2. [ ] Try to upload vendor

**Expected:**
- Operation queues or waits
- No crash
- Eventually completes

---

## 📊 Performance Tests

### Bulk Vendor Upload
**Test:**
1. [ ] Create CSV with 1000 vendors
2. [ ] Upload via Vendor Master
3. [ ] Measure time taken
4. [ ] Verify all uploaded: `SELECT COUNT(*) FROM vendors;`

**Expected Performance:**
- 1000 vendors: < 10 seconds
- Database query: < 100ms

### Large Agreement Processing
**Test:**
1. [ ] Create large PDF (100+ pages)
2. [ ] Upload via Agreement Upload
3. [ ] Measure extraction time
4. [ ] Verify text extracted

**Expected Performance:**
- 100-page PDF: < 30 seconds
- Text extraction: < 15 seconds

### Search Performance
**Test:**
1. [ ] Upload 100 vendors
2. [ ] Upload 50 agreements
3. [ ] Search for terms in obligation register
4. [ ] Measure response time

**Expected:**
- Search: < 2 seconds
- Results: Immediate display

---

## 🔍 Database Validation Tests

### Schema Verification
```bash
sqlite3 data/voce.db

# Check vendors table
.schema vendors

# Verify all 4 tables exist
.tables

# Check foreign keys
PRAGMA foreign_key_list(obligations);
```

**Expected:**
- 4 tables: vendors, agreements, obligations, certifications
- All columns present
- Foreign keys configured

### Data Integrity Tests
```bash
# No orphaned records
SELECT * FROM agreements WHERE vendor_id NOT IN (SELECT vendor_id FROM vendors);
# Should return empty

# No duplicate vendors
SELECT vendor_id, COUNT(*) FROM vendors GROUP BY vendor_id HAVING COUNT(*) > 1;
# Should return empty
```

---

## 🖥️ UI/UX Tests

### Responsive Design
- [ ] View on desktop (1920x1080)
- [ ] View on tablet (768x1024)
- [ ] View on mobile (375x667)
- [ ] Verify tables scroll properly
- [ ] Verify forms accessible

### Navigation
- [ ] Sidebar appears on all pages
- [ ] Navigation between pages works
- [ ] Back button works
- [ ] Refresh page doesn't lose state

### Visual Consistency
- [ ] Colors consistent across pages
- [ ] Font sizes readable
- [ ] Spacing consistent
- [ ] Icons display correctly

---

## 📋 Browser Compatibility

Test on:
- [ ] Chrome/Edge (Recommended)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Safari

**Expected:** All major features work on all browsers

---

## 🔐 Security Tests

### API Key Safety
- [ ] GEMINI_API_KEY not logged
- [ ] GEMINI_API_KEY not displayed
- [ ] Environment variable properly masked
- [ ] No API key in error messages

### File Upload Security
- [ ] Only allowed formats accepted
- [ ] Large files rejected (if limit set)
- [ ] No execution of uploaded files
- [ ] Path traversal prevented

### SQL Injection
- [ ] Test vendor ID with SQL characters: `'; DROP TABLE--`
- [ ] Verify proper escaping
- [ ] Test search with SQL injection attempts
- [ ] All parameterized queries

**Expected:** No SQL errors, proper escaping

---

## 📝 Test Report Template

```markdown
## Test Run Report

**Date:** [Date]
**Tester:** [Name]
**Environment:** [Python version, OS, Browser]

### Summary
- Total Tests: 
- Passed: 
- Failed: 
- Skipped: 

### Issues Found
1. [Issue 1]
2. [Issue 2]

### Performance Notes
- Vendor Upload: [Time]
- Agreement Processing: [Time]
- Search Query: [Time]

### Recommendations
- [Suggestion 1]
- [Suggestion 2]

### Approval
- Tester Signature: ________
- Date: ________
```

---

## ✅ Pre-Release Checklist

- [ ] All unit tests pass
- [ ] Integration workflow completes
- [ ] Error handling tested
- [ ] Performance acceptable
- [ ] Database validates
- [ ] UI responsive
- [ ] Security checks pass
- [ ] Documentation complete
- [ ] Sample data provided
- [ ] Deployment guide provided

---

## 🚀 Continuous Testing

### Automated Smoke Tests
```python
# test_voce.py
import pytest
from database import Database
from ai_parser import GeminiObligationParser
from agreement_parser import AgreementParser

def test_database_initialization():
    db = Database()
    vendors = db.get_all_vendors()
    assert isinstance(vendors, pd.DataFrame)

def test_text_extraction():
    text = AgreementParser.extract_text("sample_agreement.txt")
    assert text is not None
    assert len(text) > 0

def test_obligation_parsing():
    parser = GeminiObligationParser()
    sample_text = "Agreement term: 12 months"
    result = parser.extract_with_fallback(sample_text)
    assert result is not None
```

**Run Tests:**
```bash
pytest test_voce.py -v
```

---

**Last Updated:** March 2026
**Test Version:** 1.0.0

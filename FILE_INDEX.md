# 📚 VOCE - Complete File Index & Documentation

## 📋 Project Overview

**VOCE** = Vendor Obligation Control Engine

A prototype internal tool for automating vendor obligation tracking.

**Technology Stack:**
- Frontend: Streamlit
- Backend: Python
- AI: Google Gemini 1.5 Flash
- Database: SQLite
- File Storage: Local folders

---

## 📁 Project Structure

```
VOCE/
├── 📄 Core Application Files
│   ├── app.py                    # Main Streamlit application (All pages)
│   ├── database.py              # SQLite database operations
│   ├── ai_parser.py             # Google Gemini integration
│   ├── agreement_parser.py      # PDF/DOCX/TXT text extraction
│   ├── models.py                # Data models and schemas
│   └── utils.py                 # Utility functions
│
├── 📚 Documentation
│   ├── README.md                # Complete user guide and feature overview
│   ├── QUICKSTART.md            # 5-minute setup and first-use workflow
│   ├── DEPLOYMENT.md            # Production deployment guide
│   └── FILE_INDEX.md            # This file
│
├── 📦 Configuration & Data
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment variables template
│   ├── sample_vendors.csv        # Sample vendor data (10 vendors)
│   └── sample_agreement.txt      # Sample agreement for testing
│
├── 📂 Runtime Directories
│   ├── data/                     # SQLite database storage
│   │   └── voce.db              # Auto-created on first run
│   └── agreements/               # Uploaded agreement files
```

---

## 📄 File Descriptions

### Core Application Files

#### **app.py** (Main Application - 600+ lines)
**Purpose:** Streamlit web application with multi-page interface

**Contains:**
- Page configuration and styling
- Session state management
- All Streamlit pages:
  - Home page (Dashboard overview)
  - Vendor Master (CSV upload & management)
  - Agreement Upload (PDF/DOCX/TXT processing)
  - Obligation Register (Search & view obligations)
  - HoD Certification (Validation & flagging)
  - FP&A Dashboard (Metrics & charts)

**Key Functions:**
- `page_vendor_master()` - Vendor data management
- `page_agreement_upload()` - Agreement processing
- `page_obligation_register()` - Obligation browsing
- `page_hod_certification()` - Certification workflow
- `page_fpa_dashboard()` - Metrics dashboard
- `get_database()` - Database singleton
- `get_gemini_parser()` - AI parser singleton

**Usage:**
```bash
streamlit run app.py
```

---

#### **database.py** (Database Layer - 450+ lines)
**Purpose:** All SQLite database operations

**Database Class Methods:**

*Vendor Operations:*
- `add_vendor()` - Add single vendor
- `add_vendors_from_csv()` - Bulk add from DataFrame
- `get_all_vendors()` - Get all vendors
- `get_vendor_by_id()` - Lookup vendor
- `get_vendors_by_department()` - Filter by dept
- `get_unique_departments()` - Get dept list

*Agreement Operations:*
- `add_agreement()` - Create agreement record
- `get_agreements_by_vendor()` - Vendor agreements
- `get_all_agreements()` - All agreements

*Obligation Operations:*
- `add_obligation()` - Store extracted obligations
- `get_all_obligations()` - All with vendor details
- `get_obligations_by_vendor()` - Vendor obligations
- `search_obligations()` - Full-text search

*Certification Operations:*
- `add_certification()` - Store certification
- `get_certification_by_vendor()` - Latest cert
- `get_all_certifications()` - All certs
- `get_certification_summary()` - Status counts

*Dashboard Metrics:*
- `get_dashboard_metrics()` - KPI calculations
- `get_vendors_by_department_count()` - Dept stats
- `get_obligations_by_status()` - Status stats

**Key Features:**
- Connection pooling with `get_connection()`
- Table auto-initialization
- Error handling and logging
- Foreign key relationships
- Transaction management

---

#### **ai_parser.py** (AI Integration - 200+ lines)
**Purpose:** Google Gemini API integration for obligation extraction

**GeminiObligationParser Class:**

*Initialization:*
- `__init__()` - Configure API key and model

*Main Extraction:*
- `extract_obligations()` - Parse agreement text
- `extract_with_fallback()` - Safe extraction with defaults
- `get_obligation_summary()` - Human-readable summary

*JSON Handling:*
- `_parse_json_response()` - Multiple parsing strategies

**Features:**
- Structured JSON prompting
- Robust JSON parsing with fallbacks
- Error handling and logging
- Temperature control for consistency
- 13 obligation fields extracted

**Extracted Fields:**
```
- agreement_type
- agreement_term
- scope_of_work
- service_levels
- penalties_for_breach
- reporting_obligations
- servicing_obligations
- kpis_or_volume_commitments
- data_security_protocols
- payment_obligations
- milestone_completion
- dependencies
- billing_status
```

---

#### **agreement_parser.py** (Text Extraction - 150+ lines)
**Purpose:** Extract text from PDF, DOCX, TXT files

**AgreementParser Class (Static Methods):**
- `extract_from_pdf()` - PDF extraction (pdfplumber)
- `extract_from_docx()` - DOCX extraction (python-docx)
- `extract_from_txt()` - TXT extraction (built-in)
- `extract_text()` - Auto-detect format
- `validate_file()` - File validation

**Features:**
- Multi-format support
- Error handling
- Empty content detection
- Validation before processing

---

#### **models.py** (Data Models - 200+ lines)
**Purpose:** Data model definitions and schemas

**Data Classes:**
- `Vendor` - Vendor master record
- `Agreement` - Agreement metadata
- `Obligation` - Extracted obligations
- `Certification` - HoD certification

**SQL Schemas (DDL):**
- `VENDORS_SCHEMA` - Vendor table
- `AGREEMENTS_SCHEMA` - Agreement table
- `OBLIGATIONS_SCHEMA` - Obligation table
- `CERTIFICATIONS_SCHEMA` - Certification table

**Features:**
- Type hints for all fields
- Optional fields support
- Timestamp fields
- Foreign key relationships

---

#### **utils.py** (Utilities - 150+ lines)
**Purpose:** Helper functions used across application

**Functions:**
- `generate_unique_id()` - UUID generation
- `save_uploaded_file()` - File persistence
- `format_timestamp()` - Datetime formatting
- `truncate_text()` - Text truncation with ellipsis
- `is_valid_vendor_id()` - Validation
- `safe_convert_bool()` - Type conversion
- `format_file_size()` - Human-readable sizes
- `get_file_size()` - File size lookup
- `create_agreement_id()` - Agreement ID generation

---

### Documentation Files

#### **README.md** (Main Documentation - 500+ lines)
**Content:**
- Architecture overview
- Feature descriptions
- Installation instructions
- Usage workflow (5 steps)
- Database schema documentation
- API configuration
- Troubleshooting guide
- Future enhancements
- Security considerations

**Sections:**
1. Overview
2. Architecture
3. Features (1-6)
4. Installation
5. Usage Workflow
6. Database Schema
7. API Configuration
8. Supported Formats
9. Error Handling
10. Code Quality
11. Dependencies
12. Troubleshooting
13. Performance
14. Security
15. Future Enhancements

---

#### **QUICKSTART.md** (Setup Guide - 300+ lines)
**Content:**
- 5-minute setup steps
- First-time workflow (5 phases)
- Sample test data
- File structure reference
- Common commands
- Troubleshooting
- Checklist
- Quick reference table

**Phases:**
1. Upload Vendor Data (2 min)
2. Upload Agreement (3 min)
3. Review Results (2 min)
4. Certify (1 min)
5. Check Dashboard (1 min)

---

#### **DEPLOYMENT.md** (Production Guide - 400+ lines)
**Content:**
- System requirements
- Installation methods (3 approaches)
- Docker configuration
- Environment setup
- Security hardening
- Performance tuning
- Monitoring & logging
- Backup & recovery
- Troubleshooting
- Production checklist

**Installation Methods:**
1. Local development (venv)
2. Docker single container
3. Docker Compose multi-service

**Configuration Topics:**
- Environment variables
- Streamlit config.toml
- Database options (SQLite vs PostgreSQL)
- Security (API keys, .gitignore, permissions)
- Authentication (optional)
- Performance optimization
- Backup strategies

---

### Configuration & Sample Files

#### **requirements.txt**
**Python Dependencies:**
```
streamlit>=1.28.0
google-generativeai>=0.3.0
pandas>=1.5.0
pdfplumber>=0.9.0
python-docx>=0.8.11
```

**Installation:**
```bash
pip install -r requirements.txt
```

---

#### **.env.example**
**Environment Variables Template**
```
GEMINI_API_KEY=your_key_here
VOCE_DB_PATH=data/voce.db
VOCE_AGREEMENTS_DIR=agreements
LOG_LEVEL=INFO
STREAMLIT_SERVER_PORT=8501
STREAMLIT_CLIENT_BROWSER=true
```

---

#### **sample_vendors.csv**
**Contains:** 10 sample vendors across departments
**Fields:** vendor_id, vendor_name, department, nature_of_expense, owner, recurring, active, last_contract_revision_date

**Purpose:** Reference data for testing

---

#### **sample_agreement.txt**
**Contains:** Sample Service Level Agreement
**Purpose:** Test document for obligation extraction

**Includes:**
- Agreement type and term
- Scope of work
- Service levels
- Penalties
- Payment terms
- Data security
- KPIs
- Dependencies
- All key obligation fields

---

## 🚀 Getting Started

### Quick Setup (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key
export GEMINI_API_KEY="your_key_here"

# 3. Run app
streamlit run app.py

# 4. Open browser
# http://localhost:8501
```

### First Workflow

1. **Vendor Master** - Upload sample_vendors.csv
2. **Agreement Upload** - Upload sample_agreement.txt
3. **Obligation Register** - View extracted obligations
4. **HoD Certification** - Confirm obligations
5. **FP&A Dashboard** - Check metrics

---

## 📊 Data Flow

```
CSV Upload
    ↓
[Vendor Master] → SQLite vendors table
    ↓
Agreement Upload
    ↓
[File Storage] → agreements/
    ↓
[Text Extraction] → Raw text
    ↓
[Gemini AI Parser] → Parsed JSON
    ↓
[Obligation Register] → SQLite obligations table
    ↓
[HoD Certification] → SQLite certifications table
    ↓
[FP&A Dashboard] → Metrics & Charts
```

---

## 🔑 Key Concepts

### Vendors
- Master data for vendor organizations
- Contains contact, department, and contract info
- CSV import/export capability

### Agreements
- Vendor contracts and documents
- Stored as files (PDF, DOCX, TXT)
- Metadata in database

### Obligations
- Terms extracted from agreements
- 13 structured fields
- AI-powered extraction

### Certifications
- HoD validation of obligations
- Status: Confirmed, Suggested Edit, Flagged
- Audit trail with timestamps

---

## 📞 Support Resources

**Within Project:**
- README.md - Comprehensive guide
- QUICKSTART.md - Fast setup
- DEPLOYMENT.md - Production setup
- Code comments - Implementation details

**External:**
- Streamlit Docs: https://docs.streamlit.io
- Gemini API: https://ai.google.dev
- pdfplumber: https://github.com/jsvine/pdfplumber
- python-docx: https://github.com/python-openxml/python-docx

---

## ✅ Checklist

- [ ] Read README.md for overview
- [ ] Follow QUICKSTART.md for setup
- [ ] Use sample_vendors.csv for initial data
- [ ] Upload sample_agreement.txt to test
- [ ] Set GEMINI_API_KEY for AI features
- [ ] Review DEPLOYMENT.md for production
- [ ] Check requirements.txt for dependencies
- [ ] Verify data/ and agreements/ directories created

---

## 📈 Version Information

**Version:** 1.0.0 (Prototype)
**Last Updated:** March 2026
**Status:** Production Ready (with optional authentication for production use)

---

## 📝 File Modification Guide

### To Add a New Page:

1. Create function in app.py: `def page_new_feature():`
2. Add to sidebar navigation
3. Use existing database methods
4. Style with Streamlit components

### To Add a Database Feature:

1. Create method in database.py
2. Write SQL in models.py if new table needed
3. Call from app.py pages
4. Test with sample data

### To Modify AI Extraction:

1. Update prompt in ai_parser.py
2. Adjust temperature/tokens if needed
3. Test with sample_agreement.txt
4. Verify JSON parsing

---

**End of File Index**

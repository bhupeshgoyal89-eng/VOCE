# 🏢 Vendor Obligation Control Engine (VOCE)

A prototype internal tool for automated vendor obligation tracking using Streamlit, Python, Google Gemini AI, and SQLite.

## Overview

VOCE automates the process of tracking and managing vendor obligations across your organization. It enables FP&A teams to:

- Upload and manage vendor master data
- Process vendor agreements (PDF, DOCX, TXT)
- Extract obligations automatically using AI (Google Gemini)
- Track and certify vendor obligations
- Monitor compliance metrics and dashboards

## Architecture

```
Frontend:        Streamlit (Python web framework)
Backend:         Python
AI Model:        Google Gemini 1.5 Flash
Database:        SQLite
File Storage:    Local directory (agreements/)
```

## Project Structure

```
voce/
├── app.py                  # Main Streamlit application
├── database.py            # Database operations and queries
├── ai_parser.py           # Gemini integration for obligation extraction
├── agreement_parser.py    # Text extraction from PDF, DOCX, TXT
├── models.py              # Data models and schemas
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── agreements/            # Uploaded agreement files
├── data/                  # SQLite database files
└── README.md             # This file
```

## Features

### 1. **Vendor Master Management**
- Upload vendor data via CSV
- Store vendor information (ID, name, department, owner, etc.)
- Filter vendors by department
- Search vendor directory

### 2. **Agreement Processing**
- Upload PDF, DOCX, or TXT agreement documents
- Automatic text extraction
- AI-powered obligation extraction (Gemini)
- Store agreement metadata and files

### 3. **Obligation Extraction**
- Parse agreement text using Google Gemini AI
- Extract structured obligations:
  - Agreement type and term
  - Scope of work
  - Service levels and SLAs
  - Payment obligations
  - Data security protocols
  - KPIs and volume commitments
  - Penalties and compliance requirements
  - Reporting obligations

### 4. **Obligation Register**
- View all extracted obligations
- Search and filter capabilities
- Detailed obligation views
- Track billing status

### 5. **HoD Certification**
- Confirm vendor obligations
- Suggest edits
- Flag critical issues
- Store certification history

### 6. **FP&A Dashboard**
- Key metrics overview
- Vendor distribution by department
- Obligations by billing status
- Certification status summary
- Trend visualization

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Google Gemini API key

### Setup Steps

1. **Clone or navigate to the project directory:**
   ```bash
   cd /path/to/VOCE
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Gemini API key:**
   ```bash
   # On macOS/Linux
   export GEMINI_API_KEY="your_gemini_api_key_here"
   
   # On Windows (Command Prompt)
   set GEMINI_API_KEY=your_gemini_api_key_here
   
   # On Windows (PowerShell)
   $env:GEMINI_API_KEY="your_gemini_api_key_here"
   ```

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

The app will open at `http://localhost:8501`

## Usage Workflow

### Step 1: Upload Vendor Master Data
1. Navigate to **Vendor Master** page
2. Download the sample CSV template
3. Fill in your vendor information with required columns:
   - `vendor_id` - Unique vendor identifier
   - `vendor_name` - Vendor company name
   - `department` - Department (IT, Finance, etc.)
   - `nature_of_expense` - Type of expense
   - `owner` - Department owner/contact
   - `recurring` - TRUE/FALSE for recurring vendors
   - `active` - TRUE/FALSE for active status
   - `last_contract_revision_date` - Latest contract date (YYYY-MM-DD)
4. Upload the CSV file
5. Review and confirm

### Step 2: Upload Agreements
1. Navigate to **Agreement Upload** page
2. Select a vendor from the dropdown
3. Upload an agreement document (PDF, DOCX, or TXT)
4. Click "Process Agreement"
5. System will:
   - Extract text from document
   - Send to Gemini for obligation extraction
   - Store structured obligations

### Step 3: Review Obligations
1. Navigate to **Obligation Register** page
2. View all extracted obligations in table format
3. Use search to find specific obligations
4. Click on an obligation to view full details
5. Review extracted fields:
   - Agreement type and term
   - Scope of work
   - Service levels
   - Payment terms
   - Data security requirements
   - KPIs and commitments

### Step 4: Certify Obligations
1. Navigate to **HoD Certification** page
2. Select a vendor
3. Review associated obligations
4. Enter Head of Department name
5. Set certification status:
   - **Confirmed** - Obligations accepted
   - **Suggested Edit** - Changes needed
   - **Flagged** - Critical issue
6. Add comments/notes
7. Save certification

### Step 5: Monitor Dashboard
1. Navigate to **FP&A Dashboard** page
2. Review key metrics:
   - Total vendors and agreements
   - Pending certifications
   - Flagged issues
3. View charts:
   - Vendors by department
   - Obligations by billing status
   - Certification status distribution

## Database Schema

### vendors table
```sql
vendor_id (Primary Key)
vendor_name
department
nature_of_expense
owner
recurring (Boolean)
active (Boolean)
last_contract_revision_date
created_at (Timestamp)
```

### agreements table
```sql
agreement_id (Primary Key)
vendor_id (Foreign Key)
file_path
upload_date (Timestamp)
```

### obligations table
```sql
obligation_id (Primary Key, Auto-increment)
vendor_id (Foreign Key)
agreement_type
agreement_term
scope_of_work
service_levels
penalties
reporting_obligations
payment_terms
kpis
data_security
dependencies
billing_status
created_at (Timestamp)
```

### certifications table
```sql
certification_id (Primary Key, Auto-increment)
vendor_id (Foreign Key)
hod_name
status (Confirmed/Suggested Edit/Flagged)
comments
timestamp (Timestamp)
```

## API Configuration

### Google Gemini

VOCE uses Google Gemini 1.5 Flash for AI-powered obligation extraction.

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set the environment variable `GEMINI_API_KEY`
3. The app will automatically use Gemini for extraction

**Note:** If Gemini is not configured, the app will still work but obligation extraction will be skipped.

## Supported File Formats

### Text Extraction
- **PDF** (.pdf) - Uses pdfplumber
- **DOCX** (.docx) - Uses python-docx
- **TXT** (.txt) - Plain text files

## Error Handling

The application includes robust error handling for:

- Missing Gemini API key
- Failed file uploads
- PDF/DOCX extraction errors
- Invalid JSON responses from Gemini
- Database operation failures
- Missing vendor data

## Code Quality

- Modular Python code with clear separation of concerns
- Comprehensive error handling and logging
- Input validation and sanitization
- Type hints for better code clarity
- Detailed inline comments
- Robust JSON parsing with fallback handling

## Dependencies

See `requirements.txt` for complete list:
- **streamlit** - Web framework
- **google-generativeai** - Gemini API client
- **pandas** - Data manipulation
- **pdfplumber** - PDF text extraction
- **python-docx** - DOCX text extraction

## Troubleshooting

### Gemini API Not Working
- Verify `GEMINI_API_KEY` is set correctly
- Check API key validity on Google AI Studio
- Review API usage limits and quotas
- Check internet connectivity

### PDF Extraction Issues
- Ensure PDF is not password protected
- Try converting scanned PDF to OCR first
- Verify PDF is not corrupted

### Database Errors
- Delete `data/voce.db` to reset database
- Ensure `data/` directory has write permissions
- Check disk space availability

### Streamlit Connection Issues
- Check if port 8501 is available
- Clear Streamlit cache: `streamlit cache clear`
- Restart the app: `streamlit run app.py`

## Performance Considerations

- Large PDF files may take longer to extract text
- Gemini API calls have rate limits - implement queuing if needed
- SQLite is suitable for small-to-medium data volumes
- For large-scale deployments, consider PostgreSQL

## Security Considerations

1. **API Keys**: Store Gemini API key securely
2. **File Access**: Agreements stored in `agreements/` directory
3. **Database**: SQLite is file-based, consider encryption for sensitive data
4. **Authentication**: Add authentication layer for production use
5. **Input Validation**: All user inputs are validated

## Future Enhancements

- Multi-user authentication and authorization
- PostgreSQL support for enterprise deployments
- Advanced workflow with approval chains
- Automated alerts for pending certifications
- Integration with third-party systems
- Advanced analytics and reporting
- Document versioning and change tracking
- Email notifications
- API endpoints for external integration
- Export to Excel/PDF reports

## Support & Maintenance

For issues or feature requests:
1. Check troubleshooting section
2. Review application logs
3. Ensure all dependencies are installed
4. Try clearing cache and restarting

## License

Internal tool - Use only within authorized organization

## Version

Version 1.0.0 - VOCE Prototype

---

**Last Updated:** March 2026

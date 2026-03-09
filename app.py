"""
Vendor Obligation Control Engine (VOCE)
An internal tool for automated vendor obligation tracking

Frontend: Streamlit
Backend: Python
AI: Google Gemini 1.5 Flash
Database: SQLite
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
from io import StringIO

from database import Database
from agreement_parser import AgreementParser
from ai_parser import GeminiObligationParser
from utils import (
    generate_unique_id,
    save_uploaded_file,
    format_timestamp,
    truncate_text,
    create_agreement_id
)


# ============ PAGE CONFIGURATION ============

st.set_page_config(
    page_title="VOCE - Vendor Obligation Control Engine",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
    </style>
""", unsafe_allow_html=True)


# ============ SESSION STATE INITIALIZATION ============

@st.cache_resource
def get_database():
    """Initialize database connection"""
    return Database(db_path="data/voce.db")


@st.cache_resource
def get_gemini_parser():
    """Initialize Gemini parser"""
    try:
        return GeminiObligationParser()
    except ValueError as e:
        st.error(f"⚠️ {str(e)}")
        return None


# ============ HELPER FUNCTIONS ============

def is_gemini_configured():
    """Check if Gemini API is properly configured"""
    return os.getenv('GEMINI_API_KEY') is not None


# ============ PAGE: VENDOR MASTER ============

def page_vendor_master():
    """Vendor Master page - Upload and manage vendor data"""
    st.header("📦 Vendor Master")
    st.markdown("Upload vendor master data and manage vendor information.")
    
    db = get_database()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Upload Vendor Master CSV")
        
        uploaded_file = st.file_uploader(
            "Select CSV file with vendor data",
            type=['csv']
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                
                st.write("**Preview of uploaded data:**")
                st.dataframe(df.head())
                
                required_columns = [
                    'vendor_id', 'vendor_name', 'department',
                    'nature_of_expense', 'owner', 'recurring', 'active',
                    'last_contract_revision_date'
                ]
                
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"Missing required columns: {', '.join(missing_columns)}")
                else:
                    if st.button("✅ Upload Vendors", key="upload_vendors"):
                        added, errors = db.add_vendors_from_csv(df)
                        
                        if added > 0:
                            st.success(f"✅ Successfully added {added} vendor(s)")
                        
                        if errors:
                            with st.expander("View Errors"):
                                for error in errors:
                                    st.warning(error)
                
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
    
    with col2:
        st.subheader("Sample CSV Template")
        sample_csv = """vendor_id,vendor_name,department,nature_of_expense,owner,recurring,active,last_contract_revision_date
V001,Acme Corp,IT,Software,John Smith,TRUE,TRUE,2024-01-15
V002,Tech Solutions,Finance,Consulting,Jane Doe,FALSE,TRUE,2023-12-01"""
        
        st.download_button(
            label="📥 Download Template",
            data=sample_csv,
            file_name="vendor_template.csv",
            mime="text/csv"
        )
    
    # Display vendors
    st.subheader("Vendor Directory")
    
    col1, col2 = st.columns(2)
    
    with col1:
        filter_department = st.selectbox(
            "Filter by Department",
            ["All"] + db.get_unique_departments(),
            key="vendor_filter"
        )
    
    with col2:
        search_term = st.text_input("Search by vendor name", key="vendor_search")
    
    # Get vendors
    if filter_department == "All":
        vendors_df = db.get_all_vendors()
    else:
        vendors_df = db.get_vendors_by_department(filter_department)
    
    # Apply search filter
    if search_term:
        vendors_df = vendors_df[
            vendors_df['vendor_name'].str.contains(search_term, case=False, na=False)
        ]
    
    if not vendors_df.empty:
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Vendors", len(vendors_df))
        
        with col2:
            active_count = (vendors_df['active'] == True).sum()
            st.metric("Active", active_count)
        
        with col3:
            inactive_count = (vendors_df['active'] == False).sum()
            st.metric("Inactive", inactive_count)
        
        # Display vendor table
        st.dataframe(
            vendors_df[[
                'vendor_id', 'vendor_name', 'department',
                'nature_of_expense', 'owner', 'active'
            ]],
            use_container_width=True
        )
    else:
        st.info("No vendors found. Upload vendor master data to get started.")


# ============ PAGE: AGREEMENT UPLOAD ============

def page_agreement_upload():
    """Agreement Upload page - Upload and process agreements"""
    st.header("📄 Agreement Upload")
    st.markdown("Upload agreement documents for processing and obligation extraction.")
    
    db = get_database()
    gemini_parser = get_gemini_parser()
    
    # Check Gemini configuration
    if not is_gemini_configured():
        st.warning("⚠️ GEMINI_API_KEY environment variable not set. Obligation extraction will not work.")
    
    # Get vendors for selection
    vendors_df = db.get_all_vendors()
    
    if vendors_df.empty:
        st.error("❌ No vendors found. Please upload vendor master data first.")
        return
    
    vendor_options = vendors_df['vendor_name'].tolist()
    vendor_mapping = dict(zip(vendor_options, vendors_df['vendor_id'].tolist()))
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_vendor_name = st.selectbox(
            "Select Vendor",
            vendor_options,
            key="select_vendor"
        )
        selected_vendor_id = vendor_mapping[selected_vendor_name]
    
    with col2:
        st.markdown("**Supported Formats:** PDF, DOCX, TXT")
        uploaded_file = st.file_uploader(
            "Upload Agreement Document",
            type=['pdf', 'docx', 'txt'],
            key="agreement_upload"
        )
    
    if uploaded_file is not None:
        st.info(f"📋 File: {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        if st.button("🔄 Process Agreement", key="process_agreement"):
            with st.spinner("Processing agreement..."):
                try:
                    # Save file
                    file_path = save_uploaded_file(
                        uploaded_file,
                        "agreements"
                    )
                    
                    if not file_path:
                        st.error("Failed to save file")
                        return
                    
                    st.success(f"✅ File saved: {file_path}")
                    
                    # Create agreement record
                    agreement_id = create_agreement_id(selected_vendor_id, uploaded_file.name)
                    agreement_added = db.add_agreement(
                        agreement_id,
                        selected_vendor_id,
                        file_path
                    )
                    
                    if not agreement_added:
                        st.error("Failed to create agreement record")
                        return
                    
                    st.info(f"📝 Agreement ID: {agreement_id}")
                    
                    # Extract text
                    st.write("Extracting text from document...")
                    agreement_text = AgreementParser.extract_text(file_path)
                    
                    if not agreement_text:
                        st.error("Could not extract text from file")
                        return
                    
                    st.success(f"✅ Extracted {len(agreement_text)} characters")
                    
                    # Extract obligations with Gemini
                    if gemini_parser and is_gemini_configured():
                        st.write("Analyzing obligations with Gemini AI...")
                        
                        obligations = gemini_parser.extract_with_fallback(
                            agreement_text
                        )
                        
                        # Prepare obligation data for storage
                        obligation_data = {
                            'vendor_id': selected_vendor_id,
                            'agreement_type': obligations.get('agreement_type'),
                            'agreement_term': obligations.get('agreement_term'),
                            'scope_of_work': obligations.get('scope_of_work'),
                            'service_levels': obligations.get('service_levels'),
                            'penalties': obligations.get('penalties_for_breach'),
                            'reporting_obligations': obligations.get('reporting_obligations'),
                            'payment_terms': obligations.get('payment_obligations'),
                            'kpis': obligations.get('kpis_or_volume_commitments'),
                            'data_security': obligations.get('data_security_protocols'),
                            'dependencies': obligations.get('dependencies'),
                            'billing_status': obligations.get('billing_status')
                        }
                        
                        # Save to database
                        if db.add_obligation(obligation_data):
                            st.success("✅ Obligations extracted and saved!")
                            
                            # Display extracted obligations
                            st.subheader("Extracted Obligations")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Agreement Details**")
                                st.write(f"Type: {obligations.get('agreement_type') or 'N/A'}")
                                st.write(f"Term: {obligations.get('agreement_term') or 'N/A'}")
                                st.write(f"Scope: {truncate_text(obligations.get('scope_of_work', 'N/A'), 100)}")
                            
                            with col2:
                                st.write("**Key Obligations**")
                                st.write(f"SLAs: {truncate_text(obligations.get('service_levels', 'N/A'), 100)}")
                                st.write(f"Payment: {truncate_text(obligations.get('payment_obligations', 'N/A'), 100)}")
                                st.write(f"Security: {truncate_text(obligations.get('data_security_protocols', 'N/A'), 100)}")
                        else:
                            st.error("Failed to save obligations")
                    else:
                        st.warning("⚠️ Gemini API not configured. Skipping obligation extraction.")
                        st.write("To enable AI extraction, set GEMINI_API_KEY environment variable.")
                    
                except Exception as e:
                    st.error(f"Error processing agreement: {e}")
    
    # Display recent agreements
    st.subheader("Recent Agreements")
    agreements_df = db.get_all_agreements()
    
    if not agreements_df.empty:
        st.dataframe(
            agreements_df[[
                'agreement_id', 'vendor_name', 'file_path', 'upload_date'
            ]].head(10),
            use_container_width=True
        )
    else:
        st.info("No agreements uploaded yet.")


# ============ PAGE: OBLIGATION REGISTER ============

def page_obligation_register():
    """Obligation Register page - View and search obligations"""
    st.header("📋 Obligation Register")
    st.markdown("View and search vendor obligations extracted from agreements.")
    
    db = get_database()
    
    # Search and filter options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input(
            "🔍 Search obligations",
            placeholder="Search by vendor name, scope, or payment terms...",
            key="obligation_search"
        )
    
    with col2:
        view_type = st.radio("View", ["All", "Search Results"], horizontal=True)
    
    # Get obligations
    if view_type == "Search Results" and search_term:
        obligations_df = db.search_obligations(search_term)
        st.write(f"**Found {len(obligations_df)} result(s)**")
    else:
        obligations_df = db.get_all_obligations()
    
    if not obligations_df.empty:
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Obligations", len(obligations_df))
        
        with col2:
            active_vendors = obligations_df['vendor_name'].nunique()
            st.metric("Vendors", active_vendors)
        
        with col3:
            departments = obligations_df['department'].nunique()
            st.metric("Departments", departments)
        
        with col4:
            status_counts = obligations_df['billing_status'].value_counts()
            st.metric("Billing Statuses", len(status_counts))
        
        # Main obligation table
        st.subheader("Obligation Details")
        
        display_columns = [
            'vendor_name', 'department', 'scope_of_work',
            'service_levels', 'payment_terms', 'billing_status', 'created_at'
        ]
        
        st.dataframe(
            obligations_df[display_columns],
            use_container_width=True,
            height=400
        )
        
        # Detailed view
        st.subheader("Detailed Obligation View")
        
        if not obligations_df.empty:
            selected_idx = st.selectbox(
                "Select obligation to view details",
                range(len(obligations_df)),
                format_func=lambda i: f"{obligations_df.iloc[i]['vendor_name']} - {obligations_df.iloc[i]['agreement_type'] or 'N/A'}"
            )
            
            obligation = obligations_df.iloc[selected_idx]
            
            with st.expander("📄 View Full Details", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Vendor & Agreement**")
                    st.write(f"Vendor: {obligation['vendor_name']}")
                    st.write(f"Department: {obligation['department']}")
                    st.write(f"Type: {obligation['agreement_type'] or 'N/A'}")
                    st.write(f"Term: {obligation['agreement_term'] or 'N/A'}")
                
                with col2:
                    st.write("**Financial & Status**")
                    st.write(f"Payment Terms: {obligation['payment_terms'] or 'N/A'}")
                    st.write(f"Billing Status: {obligation['billing_status'] or 'N/A'}")
                    st.write(f"Created: {obligation['created_at']}")
                
                st.write("**Scope of Work**")
                st.write(obligation['scope_of_work'] or "Not specified")
                
                st.write("**Service Levels**")
                st.write(obligation['service_levels'] or "Not specified")
                
                st.write("**Data Security**")
                st.write(obligation['data_security'] or "Not specified")
                
                st.write("**KPIs & Commitments**")
                st.write(obligation['kpis'] or "Not specified")
                
                st.write("**Penalties**")
                st.write(obligation['penalties'] or "Not specified")
    else:
        st.info("No obligations found. Upload agreements to extract obligations.")


# ============ PAGE: HOD CERTIFICATION ============

def page_hod_certification():
    """HoD Certification page - Certification and validation"""
    st.header("✅ HoD Certification")
    st.markdown("Confirm, suggest edits, or flag issues for vendor obligations.")
    
    db = get_database()
    
    # Get vendors
    vendors_df = db.get_all_vendors()
    
    if vendors_df.empty:
        st.error("No vendors found. Please upload vendor master data first.")
        return
    
    vendor_options = vendors_df['vendor_name'].tolist()
    vendor_mapping = dict(zip(vendor_options, vendors_df['vendor_id'].tolist()))
    
    selected_vendor_name = st.selectbox(
        "Select Vendor to Certify",
        vendor_options,
        key="hod_select_vendor"
    )
    
    selected_vendor_id = vendor_mapping[selected_vendor_name]
    
    # Get vendor details and obligations
    vendor_info = db.get_vendor_by_id(selected_vendor_id)
    obligations_df = db.get_obligations_by_vendor(selected_vendor_id)
    existing_cert = db.get_certification_by_vendor(selected_vendor_id)
    
    if vendor_info:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Vendor", vendor_info['vendor_name'])
        
        with col2:
            st.metric("Department", vendor_info['department'])
        
        with col3:
            st.metric("Owner", vendor_info['owner'])
        
        with col4:
            status = "Active" if vendor_info['active'] else "Inactive"
            st.metric("Status", status)
    
    # Display obligations
    if not obligations_df.empty:
        st.subheader("Associated Obligations")
        st.dataframe(
            obligations_df[[
                'agreement_type', 'scope_of_work', 'service_levels', 'payment_terms'
            ]],
            use_container_width=True
        )
    else:
        st.info("No obligations found for this vendor.")
    
    # Certification form
    st.subheader("Certification")
    
    col1, col2 = st.columns(2)
    
    with col1:
        hod_name = st.text_input(
            "Head of Department Name",
            value=existing_cert.get('hod_name', '') if existing_cert else "",
            key="hod_name"
        )
    
    with col2:
        cert_status = st.radio(
            "Certification Status",
            ["Confirmed", "Suggested Edit", "Flagged"],
            index=0 if not existing_cert else ["Confirmed", "Suggested Edit", "Flagged"].index(existing_cert.get('status', 'Confirmed')),
            key="cert_status"
        )
    
    comments = st.text_area(
        "Comments",
        value=existing_cert.get('comments', '') if existing_cert else "",
        height=150,
        key="cert_comments"
    )
    
    # Color coding for status
    if cert_status == "Confirmed":
        st.markdown('<div class="success-box">✅ Obligations confirmed and accepted</div>', unsafe_allow_html=True)
    elif cert_status == "Suggested Edit":
        st.markdown('<div class="warning-box">⚠️ Suggested edits to be made</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="error-box">🚩 Critical issue flagged</div>', unsafe_allow_html=True)
    
    if st.button("💾 Save Certification", key="save_cert"):
        if not hod_name:
            st.error("Please enter Head of Department name")
        else:
            if db.add_certification(selected_vendor_id, hod_name, cert_status, comments):
                st.success(f"✅ Certification saved for {selected_vendor_name}")
            else:
                st.error("Failed to save certification")
    
    # Display certification history
    st.subheader("Certification History")
    all_certs = db.get_all_certifications()
    
    if not all_certs.empty:
        st.dataframe(
            all_certs[[
                'vendor_name', 'hod_name', 'status', 'comments', 'timestamp'
            ]],
            use_container_width=True,
            height=300
        )
    else:
        st.info("No certifications recorded yet.")


# ============ PAGE: FP&A DASHBOARD ============

def page_fpa_dashboard():
    """FP&A Dashboard - Summary metrics and visualizations"""
    st.header("📊 FP&A Dashboard")
    st.markdown("Overview of vendor obligations and compliance metrics.")
    
    db = get_database()
    
    # Get metrics
    metrics = db.get_dashboard_metrics()
    
    # Display key metrics
    st.subheader("Key Metrics")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("👥 Total Vendors", metrics['total_vendors'])
    
    with col2:
        st.metric("✅ Active Vendors", metrics['active_vendors'])
    
    with col3:
        st.metric("📄 Agreements", metrics['total_agreements'])
    
    with col4:
        st.metric("📋 Obligations", metrics['total_obligations'])
    
    with col5:
        st.metric("⏳ Pending Certs", metrics['pending_certifications'])
    
    with col6:
        st.metric("🚩 Flagged Issues", metrics['flagged_issues'])
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Vendors by Department")
        dept_counts = db.get_vendors_by_department_count()
        
        if dept_counts:
            import pandas as pd
            dept_df = pd.DataFrame(list(dept_counts.items()), columns=['Department', 'Count'])
            st.bar_chart(dept_df.set_index('Department'))
        else:
            st.info("No vendor data available")
    
    with col2:
        st.subheader("Obligations by Billing Status")
        status_counts = db.get_obligations_by_status()
        
        if status_counts:
            import pandas as pd
            status_df = pd.DataFrame(list(status_counts.items()), columns=['Billing Status', 'Count'])
            st.bar_chart(status_df.set_index('Billing Status'))
        else:
            st.info("No obligation data available")
    
    # Certification summary
    st.subheader("Certification Status Summary")
    cert_summary = db.get_certification_summary()
    
    if cert_summary:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            confirmed = cert_summary.get('Confirmed', 0)
            st.metric("✅ Confirmed", confirmed)
        
        with col2:
            suggested = cert_summary.get('Suggested Edit', 0)
            st.metric("⚠️ Suggested Edit", suggested)
        
        with col3:
            flagged = cert_summary.get('Flagged', 0)
            st.metric("🚩 Flagged", flagged)
    else:
        st.info("No certifications recorded yet")
    
    # Recent certifications
    st.subheader("Recent Certifications")
    all_certs = db.get_all_certifications()
    
    if not all_certs.empty:
        st.dataframe(
            all_certs[[
                'vendor_name', 'hod_name', 'status', 'timestamp'
            ]].head(10),
            use_container_width=True
        )
    else:
        st.info("No certifications recorded yet")


# ============ MAIN APP ============

def main():
    """Main application"""
    
    # Sidebar navigation
    st.sidebar.title("🏢 VOCE")
    st.sidebar.markdown("Vendor Obligation Control Engine")
    st.sidebar.divider()
    
    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Home",
            "📦 Vendor Master",
            "📄 Agreement Upload",
            "📋 Obligation Register",
            "✅ HoD Certification",
            "📊 FP&A Dashboard"
        ]
    )
    
    st.sidebar.divider()
    
    # Display API status
    if is_gemini_configured():
        st.sidebar.success("✅ Gemini API Configured")
    else:
        st.sidebar.warning("⚠️ GEMINI_API_KEY not set")
    
    st.sidebar.info(
        "**Setup Instructions:**\n\n"
        "1. Set GEMINI_API_KEY environment variable\n"
        "2. Upload vendor master data\n"
        "3. Upload agreement documents\n"
        "4. Review extracted obligations\n"
        "5. Certify obligations"
    )
    
    # Route to pages
    if page == "🏠 Home":
        st.title("🏢 Vendor Obligation Control Engine (VOCE)")
        st.markdown("""
        Welcome to VOCE - an automated vendor obligation tracking system.
        
        ### Features
        
        **📦 Vendor Master**
        - Upload vendor master data from CSV
        - Manage vendor information
        - Filter by department
        
        **📄 Agreement Upload**
        - Upload PDF, DOCX, or TXT agreements
        - Automatic text extraction
        - AI-powered obligation parsing with Gemini
        
        **📋 Obligation Register**
        - View all extracted obligations
        - Search and filter capabilities
        - Detailed obligation information
        
        **✅ HoD Certification**
        - Confirm vendor obligations
        - Suggest edits
        - Flag critical issues
        
        **📊 FP&A Dashboard**
        - Summary metrics and KPIs
        - Vendor and obligation analytics
        - Certification status overview
        
        ### Quick Start
        
        1. **Upload Vendor Data** → Use the Vendor Master page to upload your vendor CSV
        2. **Upload Agreements** → Go to Agreement Upload to process vendor contracts
        3. **Review Obligations** → Check the Obligation Register for extracted data
        4. **Certify** → Use HoD Certification to validate obligations
        5. **Dashboard** → Monitor metrics on the FP&A Dashboard
        
        ### Supported File Formats
        
        - **PDF** (.pdf)
        - **Word** (.docx)
        - **Text** (.txt)
        
        ### Environment Setup
        
        To enable AI-powered obligation extraction, set your Gemini API key:
        
        ```bash
        export GEMINI_API_KEY="your_api_key_here"
        streamlit run app.py
        ```
        """)
        
        # Quick stats
        db = get_database()
        metrics = db.get_dashboard_metrics()
        
        st.subheader("System Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Vendors", metrics['total_vendors'])
        
        with col2:
            st.metric("Agreements", metrics['total_agreements'])
        
        with col3:
            st.metric("Obligations", metrics['total_obligations'])
    
    elif page == "📦 Vendor Master":
        page_vendor_master()
    
    elif page == "📄 Agreement Upload":
        page_agreement_upload()
    
    elif page == "📋 Obligation Register":
        page_obligation_register()
    
    elif page == "✅ HoD Certification":
        page_hod_certification()
    
    elif page == "📊 FP&A Dashboard":
        page_fpa_dashboard()


if __name__ == "__main__":
    main()

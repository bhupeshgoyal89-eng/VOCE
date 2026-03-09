"""
Vendor Obligation Control Engine (VOCE)
An internal tool for automated vendor obligation tracking with department-level certification workflows

Frontend: Streamlit
Backend: Python
AI: Google Gemini 2.5 Flash
Database: SQLite
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import logging
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

# ============ CONSTANTS ============

CURRENT_CYCLE = "2026-03"
USER_EMAILS = [
    "cto@company.com",
    "cro@company.com",
    "cfo@company.com",
    "cmo@company.com",
    "headcx@company.com",
    "chro@company.com",
    "coo@company.com",
    "cdo@company.com",
    "fpna@company.com"
]
CERTIFICATION_STATUSES = ["confirmed", "edit_requested", "issue_flagged"]
STATUS_LABELS = {
    "confirmed": "✅ Confirmed",
    "edit_requested": "📝 Edit Requested",
    "issue_flagged": "🚩 Issue Flagged"
}

# ============ PAGE CONFIGURATION ============

st.set_page_config(
    page_title="VOCE - Vendor Obligation Control Engine",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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

def is_gemini_configured():
    """Check if Gemini API is properly configured"""
    return os.getenv('GEMINI_API_KEY') is not None

# Initialize session state
if 'current_user_email' not in st.session_state:
    st.session_state.current_user_email = USER_EMAILS[0]

# ============ SIDEBAR ============

with st.sidebar:
    st.title("🏢 VOCE")
    
    # User selection
    st.markdown("### 👤 User Login")
    st.session_state.current_user_email = st.selectbox(
        "Select User Email",
        USER_EMAILS,
        index=USER_EMAILS.index(st.session_state.current_user_email) if st.session_state.current_user_email in USER_EMAILS else 0,
        key="user_selector"
    )
    st.info(f"Logged in as: **{st.session_state.current_user_email}**")
    
    # Navigation
    st.markdown("### 📊 Navigation")
    page = st.radio(
        "Select Page",
        [
            "🏠 Home",
            "📦 Vendor Master",
            "📄 Agreement Upload",
            "📋 Obligation Register",
            "🎯 HoD Dashboard",
            "📈 FP&A Dashboard"
        ]
    )
    
    # API status
    st.markdown("### ⚙️ System Status")
    if is_gemini_configured():
        st.success("✅ Gemini API Configured")
    else:
        st.warning("⚠️ Gemini API Not Set")
    
    st.markdown(f"**Current Cycle:** {CURRENT_CYCLE}")

# ============ PAGE: HOME ============

def page_home():
    """Home page with overview"""
    st.title("🏢 Vendor Obligation Control Engine (VOCE)")
    st.markdown("Automated vendor obligation tracking with department-level certification workflows.")
    
    db = get_database()
    metrics = db.get_dashboard_metrics()
    
    # Dashboard metrics
    st.markdown("### 📊 System Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Vendors", metrics['total_vendors'])
    
    with col2:
        st.metric("Active Vendors", metrics['active_vendors'])
    
    with col3:
        st.metric("Total Agreements", metrics['total_agreements'])
    
    with col4:
        st.metric("Total Obligations", metrics['total_obligations'])
    
    # Features
    st.markdown("### ✨ Key Features")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📦 Vendor Master**
        - Upload and manage vendor data
        - Track vendor departments and contacts
        - Monitor active vendors
        
        **📄 Agreement Upload**
        - Upload PDF, DOCX, TXT agreements
        - AI-powered obligation extraction
        - Automatic obligation parsing
        """)
    
    with col2:
        st.markdown("""
        **📋 Obligation Register**
        - View extracted vendor obligations
        - Search and filter capabilities
        - Full obligation details
        
        **🎯 HoD Dashboard**
        - Department head certification
        - Vendor-specific workflows
        - Action tracking
        """)

# ============ PAGE: VENDOR MASTER ============

def page_vendor_master():
    """Vendor Master page"""
    st.header("📦 Vendor Master")
    st.markdown("Upload vendor master data and manage vendor information.")
    
    db = get_database()
    
    tabs = st.tabs(["View Vendors", "Upload CSV"])
    
    with tabs[0]:
        st.subheader("All Vendors")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_vendor = st.text_input("Search vendor name", "")
        
        with col2:
            departments = db.get_unique_departments()
            dept_options = ["All"] + (departments if departments else [])
            selected_dept = st.selectbox("Filter by department", dept_options)
        
        with col3:
            owners = db.get_unique_owners()
            owner_options = ["All"] + (owners if owners else [])
            selected_owner = st.selectbox("Filter by owner", owner_options)
        
        # Get vendors
        vendors_df = db.get_all_vendors()
        
        # Apply filters
        if search_vendor:
            vendors_df = vendors_df[vendors_df['vendor_name'].str.contains(search_vendor, case=False, na=False)]
        if selected_dept != "All":
            vendors_df = vendors_df[vendors_df['department'] == selected_dept]
        if selected_owner != "All":
            vendors_df = vendors_df[vendors_df['owner_email'] == selected_owner]
        
        # Display table
        if not vendors_df.empty:
            st.dataframe(
                vendors_df[[
                    'vendor_id', 'vendor_name', 'department', 'nature_of_expense',
                    'owner_email', 'recurring', 'active', 'last_contract_revision_date'
                ]],
                use_container_width=True,
                hide_index=True
            )
            st.success(f"Showing {len(vendors_df)} vendor(s)")
        else:
            st.info("No vendors found")
    
    with tabs[1]:
        st.subheader("Upload Vendors from CSV")
        
        # CSV template info
        st.info("""
        **CSV Format Required:**
        - vendor_id, vendor_name, department, nature_of_expense, owner_email, recurring, active, last_contract_revision_date
        
        **Example:**
        - v001, Acme Corp, IT, Software License, cto@company.com, 1, 1, 2025-12-31
        """)
        
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview:")
                st.dataframe(df.head(), use_container_width=True)
                
                if st.button("✅ Upload Vendors"):
                    added, errors = db.add_vendors_from_csv(df)
                    st.success(f"✅ Added {added} vendor(s)")
                    if errors:
                        st.warning("Errors:")
                        for error in errors:
                            st.write(f"- {error}")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

# ============ PAGE: AGREEMENT UPLOAD ============

def page_agreement_upload():
    """Agreement Upload page"""
    st.header("📄 Agreement Upload")
    st.markdown("Upload agreement documents for processing and obligation extraction.")
    
    db = get_database()
    gemini_parser = get_gemini_parser()
    
    if not is_gemini_configured():
        st.warning("⚠️ Gemini API not configured. Obligation extraction will not work.")
    
    # Get vendors
    vendors_df = db.get_all_vendors()
    
    if vendors_df.empty:
        st.error("❌ No vendors found. Please upload vendor master data first.")
        return
    
    vendor_options = vendors_df['vendor_name'].tolist()
    vendor_mapping = dict(zip(vendor_options, vendors_df['vendor_id'].tolist()))
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_vendor_name = st.selectbox("Select Vendor", vendor_options)
        selected_vendor_id = vendor_mapping[selected_vendor_name]
    
    with col2:
        st.markdown("**Supported Formats:** PDF, DOCX, TXT")
        uploaded_file = st.file_uploader(
            "Upload Agreement Document",
            type=['pdf', 'docx', 'txt']
        )
    
    if uploaded_file is not None:
        st.info(f"📋 File: {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        if st.button("🔄 Process Agreement"):
            with st.spinner("Processing agreement..."):
                try:
                    # Save file
                    file_path = save_uploaded_file(uploaded_file, "agreements")
                    if not file_path:
                        st.error("Failed to save file")
                        return
                    
                    st.success(f"✅ File saved: {file_path}")
                    
                    # Create agreement record
                    agreement_id = create_agreement_id(selected_vendor_id, uploaded_file.name)
                    if not db.add_agreement(agreement_id, selected_vendor_id, file_path):
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
                        logger.info(f"Calling Gemini for vendor {selected_vendor_id}...")
                        
                        obligations = gemini_parser.extract_with_fallback(agreement_text)
                        logger.info(f"Gemini returned: {obligations}")
                        
                        obligation_data = {
                            'vendor_id': selected_vendor_id,
                            'agreement_type': obligations.get('agreement_type'),
                            'agreement_term': obligations.get('agreement_term'),
                            'scope_of_work': obligations.get('scope_of_work'),
                            'service_levels': obligations.get('service_levels'),
                            'penalties': obligations.get('penalties_for_breach'),
                            'reporting_obligations': obligations.get('reporting_obligations'),
                            'servicing_obligations': obligations.get('servicing_obligations'),
                            'kpis_or_volume_commitments': obligations.get('kpis_or_volume_commitments'),
                            'data_security_protocols': obligations.get('data_security_protocols'),
                            'payment_obligations': obligations.get('payment_obligations'),
                            'milestone_completion': obligations.get('milestone_completion'),
                            'dependencies': obligations.get('dependencies'),
                            'billing_status': obligations.get('billing_status')
                        }
                        
                        logger.info(f"Storing obligation data: {obligation_data}")
                        
                        if db.add_obligation(obligation_data):
                            st.success("✅ Obligations extracted and saved!")
                            
                            st.subheader("Extracted Obligations")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Agreement Details**")
                                st.write(f"Type: {obligations.get('agreement_type') or 'N/A'}")
                                st.write(f"Term: {obligations.get('agreement_term') or 'N/A'}")
                            
                            with col2:
                                st.write("**Key Obligations**")
                                st.write(f"Scope: {truncate_text(obligations.get('scope_of_work', 'N/A'), 100)}")
                                st.write(f"SLAs: {truncate_text(obligations.get('service_levels', 'N/A'), 100)}")
                        else:
                            st.error("Failed to save obligations")
                    else:
                        st.warning("⚠️ Gemini API not configured. Skipping obligation extraction.")
                
                except Exception as e:
                    st.error(f"Error processing agreement: {e}")
    
    # Display recent agreements
    st.subheader("Recent Agreements")
    agreements_df = db.get_all_agreements()
    
    if not agreements_df.empty:
        st.dataframe(
            agreements_df[['agreement_id', 'vendor_id', 'vendor_name', 'file_path', 'upload_date']].head(20),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No agreements uploaded yet")

# ============ PAGE: OBLIGATION REGISTER ============

def page_obligation_register():
    """Obligation Register page"""
    st.header("📋 Obligation Register")
    st.markdown("View and manage all extracted vendor obligations.")
    
    db = get_database()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search obligations", "")
    
    with col2:
        departments = db.get_unique_departments()
        dept_options = ["All"] + (departments if departments else [])
        selected_dept = st.selectbox("Filter by department", dept_options)
    
    with col3:
        vendors_df = db.get_all_vendors()
        vendor_names = ["All"] + (vendors_df['vendor_name'].tolist() if not vendors_df.empty else [])
        selected_vendor = st.selectbox("Filter by vendor", vendor_names)
    
    # Get obligations
    if search_term:
        obligations_df = db.search_obligations(search_term)
    else:
        obligations_df = db.get_all_obligations()
    
    # Apply filters
    if selected_dept != "All":
        obligations_df = obligations_df[obligations_df['department'] == selected_dept]
    if selected_vendor != "All":
        obligations_df = obligations_df[obligations_df['vendor_name'] == selected_vendor]
    
    # Display
    if not obligations_df.empty:
        # Select only columns that exist
        available_cols = [col for col in [
            'vendor_name', 'department', 'agreement_type', 'agreement_term',
            'scope_of_work', 'service_levels', 'penalties', 'reporting_obligations',
            'servicing_obligations', 'kpis_or_volume_commitments', 'data_security_protocols',
            'payment_obligations', 'milestone_completion', 'dependencies', 'billing_status', 'created_at'
        ] if col in obligations_df.columns]
        
        if available_cols:
            st.dataframe(
                obligations_df[available_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            # Fallback: show all columns
            st.dataframe(obligations_df, use_container_width=True, hide_index=True)
        
        st.success(f"Showing {len(obligations_df)} obligation(s)")
    else:
        st.info("No obligations found")

# ============ PAGE: HOD DASHBOARD ============

def page_hod_dashboard():
    """HoD Dashboard page"""
    st.header("🎯 HoD Dashboard")
    st.markdown(f"Vendor certification dashboard for **{st.session_state.current_user_email}**")
    
    db = get_database()
    current_user = st.session_state.current_user_email
    
    # Get vendors assigned to this HoD
    try:
        hod_vendors = db.get_vendors_by_owner(current_user)
    except Exception as e:
        st.error(f"Error loading vendors: {e}")
        return
    
    if hod_vendors.empty:
        st.info(f"No vendors assigned to {current_user}")
        return
    
    st.subheader("My Vendors")
    
    # Display vendors with certification actions
    for idx, vendor in hod_vendors.iterrows():
        try:
            vendor_name = vendor.get('vendor_name', 'Unknown')
            vendor_id = vendor.get('vendor_id', 'Unknown')
            
            with st.expander(f"🏢 {vendor_name} ({vendor_id})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Vendor Details**")
                    st.write(f"Department: {vendor.get('department', 'N/A')}")
                    st.write(f"Nature of Expense: {vendor.get('nature_of_expense', 'N/A')}")
                    st.write(f"Recurring: {'Yes' if vendor.get('recurring', False) else 'No'}")
                    st.write(f"Active: {'Yes' if vendor.get('active', False) else 'No'}")
                    st.write(f"Last Contract Revision: {vendor.get('last_contract_revision_date', 'N/A')}")
                
                with col2:
                    st.write("**Certification Status**")
                    
                    # Check existing certification
                    cert = db.get_certification_by_vendor_cycle(vendor_id, CURRENT_CYCLE)
                    
                    if cert:
                        st.write(f"Status: {STATUS_LABELS.get(cert['status'], cert['status'])}")
                        st.write(f"Comments: {cert['comments'] or 'None'}")
                        st.write(f"Last Updated: {cert['timestamp']}")
                    else:
                        st.write("Status: ⏳ Pending")
                
                # Action buttons
                st.write("**Take Action**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✅ Confirm", key=f"confirm_{vendor_id}"):
                        comments = st.text_input(f"Comments for {vendor_name}", key=f"comments_confirm_{vendor_id}")
                        if st.button("Submit Confirmation", key=f"submit_confirm_{vendor_id}"):
                            if db.add_certification(
                                vendor_id,
                                CURRENT_CYCLE,
                                current_user,
                                "confirmed",
                                comments
                            ):
                                st.success("✅ Vendor confirmed!")
                                st.rerun()
                
                with col2:
                    if st.button("📝 Request Edit", key=f"edit_{vendor_id}"):
                        comments = st.text_input(f"Edit request for {vendor_name}", key=f"comments_edit_{vendor_id}")
                        if st.button("Submit Edit Request", key=f"submit_edit_{vendor_id}"):
                            if db.add_certification(
                                vendor_id,
                                CURRENT_CYCLE,
                                current_user,
                                "edit_requested",
                                comments
                            ):
                                st.success("📝 Edit request submitted!")
                                st.rerun()
                
                with col3:
                    if st.button("🚩 Flag Issue", key=f"flag_{vendor_id}"):
                        comments = st.text_input(f"Issue for {vendor_name}", key=f"comments_flag_{vendor_id}")
                        if st.button("Submit Flag", key=f"submit_flag_{vendor_id}"):
                            if db.add_certification(
                                vendor_id,
                                CURRENT_CYCLE,
                                current_user,
                                "issue_flagged",
                                comments
                            ):
                                st.success("🚩 Issue flagged!")
                                st.rerun()
        except Exception as e:
            st.error(f"Error displaying vendor: {e}")
            continue
    
    # Summary
    st.subheader("Certification Summary")
    certifications = db.get_certifications_by_hod(current_user, CURRENT_CYCLE)
    
    if not certifications.empty:
        status_counts = certifications['status'].value_counts().to_dict()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Confirmed", status_counts.get("confirmed", 0))
        with col2:
            st.metric("Edit Requested", status_counts.get("edit_requested", 0))
        with col3:
            st.metric("Issues Flagged", status_counts.get("issue_flagged", 0))

# ============ PAGE: FP&A DASHBOARD ============

def page_fpa_dashboard():
    """FP&A Dashboard page"""
    st.header("📈 FP&A Dashboard")
    st.markdown("Finance & Procurement Analytics Dashboard")
    
    db = get_database()
    
    # Metrics
    st.subheader("Key Metrics")
    metrics = db.get_dashboard_metrics()
    certifications = db.get_all_certifications(CURRENT_CYCLE)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Vendors", metrics['total_vendors'])
    
    with col2:
        st.metric("Active Agreements", metrics['total_agreements'])
    
    with col3:
        # Calculate pending certifications
        if not certifications.empty and 'status' in certifications.columns:
            certified_count = len(certifications[certifications['status'].notna()])
        else:
            certified_count = 0
        pending = metrics['total_vendors'] - certified_count
        st.metric("Pending Certifications", max(0, pending))
    
    with col4:
        # Count confirmed
        if not certifications.empty and 'status' in certifications.columns:
            confirmed = len(certifications[certifications['status'] == 'confirmed'])
        else:
            confirmed = 0
        st.metric("Confirmed", confirmed)
    
    with col5:
        # Count flagged
        if not certifications.empty and 'status' in certifications.columns:
            flagged = len(certifications[certifications['status'] == 'issue_flagged'])
        else:
            flagged = 0
        st.metric("Issues Flagged", flagged)
    
    # Certification table
    st.subheader("Certification Details")
    
    col1, col2 = st.columns(2)
    with col1:
        if not certifications.empty and 'status' in certifications.columns:
            selected_status = st.multiselect(
                "Filter by status",
                certifications['status'].unique().tolist(),
                default=certifications['status'].unique().tolist()
            )
        else:
            selected_status = []
    with col2:
        selected_cycle = st.selectbox("Filter by cycle", [CURRENT_CYCLE, "All"], key="cycle_filter")
    
    if selected_cycle == "All":
        filtered_certs = db.get_all_certifications()
    else:
        filtered_certs = certifications
    
    if selected_status and 'status' in filtered_certs.columns:
        filtered_certs = filtered_certs[filtered_certs['status'].isin(selected_status)]
    
    if not filtered_certs.empty:
        # Only select columns that exist
        available_cols = [col for col in [
            'vendor_id', 'vendor_name', 'department', 'owner_email',
            'certification_cycle', 'status', 'comments', 'timestamp'
        ] if col in filtered_certs.columns]
        
        if available_cols:
            st.dataframe(
                filtered_certs[available_cols].sort_values('timestamp', ascending=False) if 'timestamp' in available_cols else filtered_certs[available_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            # Fallback: show all available columns
            st.dataframe(
                filtered_certs.sort_values('timestamp', ascending=False) if 'timestamp' in filtered_certs.columns else filtered_certs,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No certifications found")

# ============ MAIN ROUTER ============

if page == "🏠 Home":
    page_home()
elif page == "📦 Vendor Master":
    page_vendor_master()
elif page == "📄 Agreement Upload":
    page_agreement_upload()
elif page == "📋 Obligation Register":
    page_obligation_register()
elif page == "🎯 HoD Dashboard":
    page_hod_dashboard()
elif page == "📈 FP&A Dashboard":
    page_fpa_dashboard()

# Footer
st.markdown("---")
st.markdown(f"**VOCE** | Cycle: {CURRENT_CYCLE} | User: {st.session_state.current_user_email} | Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

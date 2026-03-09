"""
Data models and database schemas for VOCE
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Vendor:
    """Vendor master data model"""
    vendor_id: str
    vendor_name: str
    department: str
    nature_of_expense: str
    owner_email: str
    recurring: bool
    active: bool
    last_contract_revision_date: str


@dataclass
class Agreement:
    """Agreement data model"""
    agreement_id: str
    vendor_id: str
    file_path: str
    upload_date: datetime


@dataclass
class Obligation:
    """Obligation register data model"""
    vendor_id: str
    agreement_type: Optional[str] = None
    agreement_term: Optional[str] = None
    scope_of_work: Optional[str] = None
    service_levels: Optional[str] = None
    penalties: Optional[str] = None
    reporting_obligations: Optional[str] = None
    servicing_obligations: Optional[str] = None
    kpis_or_volume_commitments: Optional[str] = None
    data_security_protocols: Optional[str] = None
    payment_obligations: Optional[str] = None
    milestone_completion: Optional[str] = None
    dependencies: Optional[str] = None
    billing_status: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Certification:
    """HoD certification data model"""
    vendor_id: str
    certification_cycle: str
    hod_email: str
    status: str  # "confirmed", "edit_requested", "issue_flagged"
    comments: str
    timestamp: datetime


# SQLite Schema SQL statements

VENDORS_SCHEMA = """
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id TEXT PRIMARY KEY,
    vendor_name TEXT NOT NULL,
    department TEXT NOT NULL,
    nature_of_expense TEXT NOT NULL,
    owner_email TEXT NOT NULL,
    recurring INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    last_contract_revision_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

AGREEMENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS agreements (
    agreement_id TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
)
"""

OBLIGATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS obligations (
    obligation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id TEXT NOT NULL,
    agreement_type TEXT,
    agreement_term TEXT,
    scope_of_work TEXT,
    service_levels TEXT,
    penalties TEXT,
    reporting_obligations TEXT,
    servicing_obligations TEXT,
    kpis_or_volume_commitments TEXT,
    data_security_protocols TEXT,
    payment_obligations TEXT,
    milestone_completion TEXT,
    dependencies TEXT,
    billing_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
)
"""

CERTIFICATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id TEXT NOT NULL,
    certification_cycle TEXT NOT NULL,
    hod_email TEXT NOT NULL,
    status TEXT NOT NULL,
    comments TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    UNIQUE(vendor_id, certification_cycle)
)
"""

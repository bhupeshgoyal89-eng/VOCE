"""
Database operations for VOCE
Handles all SQLite interactions for vendors, agreements, obligations, and certifications
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from models import (
    VENDORS_SCHEMA,
    AGREEMENTS_SCHEMA,
    OBLIGATIONS_SCHEMA,
    CERTIFICATIONS_SCHEMA,
    Vendor,
    Agreement,
    Obligation,
    Certification
)


class Database:
    """SQLite database manager for VOCE"""

    def __init__(self, db_path: str = "data/voce.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.ensure_db_exists()
        self.initialize_tables()
        self.migrate_schema()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def ensure_db_exists(self):
        """Ensure database directory and file exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            conn.close()

    def initialize_tables(self):
        """Create all necessary tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        schemas = [
            VENDORS_SCHEMA,
            AGREEMENTS_SCHEMA,
            OBLIGATIONS_SCHEMA,
            CERTIFICATIONS_SCHEMA
        ]
        
        for schema in schemas:
            cursor.execute(schema)
        
        conn.commit()
        conn.close()

    def migrate_schema(self):
        """Migrate existing database schema to new format"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if vendors table has 'owner' column (old schema)
            cursor.execute("PRAGMA table_info(vendors)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'owner' in columns and 'owner_email' not in columns:
                cursor.execute("ALTER TABLE vendors RENAME COLUMN owner TO owner_email")
                conn.commit()
            
            # Check if certifications table needs updates
            cursor.execute("PRAGMA table_info(certifications)")
            cert_columns = [col[1] for col in cursor.fetchall()]
            
            if 'certification_cycle' not in cert_columns:
                cursor.execute("ALTER TABLE certifications ADD COLUMN certification_cycle TEXT DEFAULT '2026-03'")
                conn.commit()
            
            if 'hod_email' not in cert_columns:
                cursor.execute("ALTER TABLE certifications ADD COLUMN hod_email TEXT")
                conn.commit()
        except Exception as e:
            print(f"Schema migration notice: {e}")
        
        conn.close()

    # ============ VENDOR OPERATIONS ============
    
    def add_vendor(self, vendor: Vendor) -> bool:
        """Add a single vendor to the database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO vendors 
                (vendor_id, vendor_name, department, nature_of_expense, owner_email, recurring, active, last_contract_revision_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vendor.vendor_id,
                vendor.vendor_name,
                vendor.department,
                vendor.nature_of_expense,
                vendor.owner_email,
                vendor.recurring,
                vendor.active,
                vendor.last_contract_revision_date
            ))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error adding vendor: {e}")
            return False

    def add_vendors_from_csv(self, df: pd.DataFrame) -> tuple[int, List[str]]:
        """Add multiple vendors from DataFrame (CSV upload)"""
        added = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                owner_email = str(row.get('owner_email', row.get('owner', '')))
                
                vendor = Vendor(
                    vendor_id=str(row['vendor_id']),
                    vendor_name=str(row['vendor_name']),
                    department=str(row['department']),
                    nature_of_expense=str(row['nature_of_expense']),
                    owner_email=owner_email,
                    recurring=bool(row.get('recurring', False)),
                    active=bool(row.get('active', True)),
                    last_contract_revision_date=str(row.get('last_contract_revision_date', ''))
                )
                
                if self.add_vendor(vendor):
                    added += 1
                else:
                    errors.append(f"Row {idx + 1}: Vendor ID {row['vendor_id']} already exists")
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
        
        return added, errors

    def get_all_vendors(self) -> pd.DataFrame:
        """Get all vendors as DataFrame"""
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM vendors ORDER BY vendor_name", conn)
        conn.close()
        return df

    def get_vendor_by_id(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        """Get vendor by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vendors WHERE vendor_id = ?", (vendor_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None

    def get_vendors_by_department(self, department: str) -> pd.DataFrame:
        """Get vendors filtered by department"""
        conn = self.get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM vendors WHERE department = ? ORDER BY vendor_name",
            conn,
            params=(department,)
        )
        conn.close()
        return df

    def get_vendors_by_owner(self, owner_email: str) -> pd.DataFrame:
        """Get vendors assigned to a specific owner/HoD"""
        conn = self.get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM vendors WHERE owner_email = ? ORDER BY vendor_name",
            conn,
            params=(owner_email,)
        )
        conn.close()
        return df

    def get_unique_departments(self) -> List[str]:
        """Get list of unique departments"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT department FROM vendors ORDER BY department")
        departments = [row[0] for row in cursor.fetchall()]
        conn.close()
        return departments

    def get_unique_owners(self) -> List[str]:
        """Get list of unique owner emails"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT owner_email FROM vendors ORDER BY owner_email")
        owners = [row[0] for row in cursor.fetchall()]
        conn.close()
        return owners

    # ============ AGREEMENT OPERATIONS ============
    
    def add_agreement(self, agreement_id: str, vendor_id: str, file_path: str) -> bool:
        """Add agreement record"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agreements 
                (agreement_id, vendor_id, file_path, upload_date)
                VALUES (?, ?, ?, ?)
            """, (agreement_id, vendor_id, file_path, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding agreement: {e}")
            return False

    def get_agreements_by_vendor(self, vendor_id: str) -> pd.DataFrame:
        """Get all agreements for a vendor"""
        conn = self.get_connection()
        df = pd.read_sql_query(
            "SELECT a.* FROM agreements a WHERE a.vendor_id = ? ORDER BY a.upload_date DESC",
            conn,
            params=(vendor_id,)
        )
        conn.close()
        return df

    def get_all_agreements(self) -> pd.DataFrame:
        """Get all agreements with vendor details"""
        conn = self.get_connection()
        df = pd.read_sql_query(
            "SELECT a.agreement_id, a.vendor_id, a.file_path, a.upload_date, v.vendor_name FROM agreements a LEFT JOIN vendors v ON a.vendor_id = v.vendor_id ORDER BY a.upload_date DESC",
            conn
        )
        conn.close()
        return df

    # ============ OBLIGATION OPERATIONS ============
    
    def add_obligation(self, obligation_data: Dict[str, Any]) -> bool:
        """Add obligation record"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO obligations 
                (vendor_id, agreement_type, agreement_term, scope_of_work, service_levels, 
                 penalties, reporting_obligations, servicing_obligations, kpis_or_volume_commitments,
                 data_security_protocols, payment_obligations, milestone_completion, dependencies,
                 billing_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                obligation_data.get('vendor_id'),
                obligation_data.get('agreement_type'),
                obligation_data.get('agreement_term'),
                obligation_data.get('scope_of_work'),
                obligation_data.get('service_levels'),
                obligation_data.get('penalties'),
                obligation_data.get('reporting_obligations'),
                obligation_data.get('servicing_obligations'),
                obligation_data.get('kpis_or_volume_commitments'),
                obligation_data.get('data_security_protocols'),
                obligation_data.get('payment_obligations'),
                obligation_data.get('milestone_completion'),
                obligation_data.get('dependencies'),
                obligation_data.get('billing_status'),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding obligation: {e}")
            return False

    def get_all_obligations(self) -> pd.DataFrame:
        """Get all obligations with vendor details"""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT 
                o.obligation_id,
                v.vendor_name,
                v.department,
                o.agreement_type,
                o.agreement_term,
                o.scope_of_work,
                o.service_levels,
                o.penalties,
                o.reporting_obligations,
                o.servicing_obligations,
                o.kpis_or_volume_commitments,
                o.data_security_protocols,
                o.payment_obligations,
                o.milestone_completion,
                o.dependencies,
                o.billing_status,
                o.created_at
            FROM obligations o
            LEFT JOIN vendors v ON o.vendor_id = v.vendor_id
            ORDER BY o.created_at DESC
        """, conn)
        conn.close()
        return df

    def get_obligations_by_vendor(self, vendor_id: str) -> pd.DataFrame:
        """Get obligations for a specific vendor"""
        conn = self.get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM obligations WHERE vendor_id = ? ORDER BY created_at DESC",
            conn,
            params=(vendor_id,)
        )
        conn.close()
        return df

    def search_obligations(self, search_term: str) -> pd.DataFrame:
        """Search obligations by keyword"""
        conn = self.get_connection()
        search_pattern = f"%{search_term}%"
        df = pd.read_sql_query("""
            SELECT 
                o.obligation_id,
                v.vendor_name,
                v.department,
                o.agreement_type,
                o.scope_of_work,
                o.service_levels,
                o.payment_obligations,
                o.billing_status,
                o.created_at
            FROM obligations o
            LEFT JOIN vendors v ON o.vendor_id = v.vendor_id
            WHERE 
                v.vendor_name LIKE ? OR
                o.scope_of_work LIKE ? OR
                o.service_levels LIKE ? OR
                o.payment_obligations LIKE ?
            ORDER BY o.created_at DESC
        """, conn, params=(search_pattern, search_pattern, search_pattern, search_pattern))
        conn.close()
        return df

    # ============ CERTIFICATION OPERATIONS ============
    
    def add_certification(self, vendor_id: str, certification_cycle: str, 
                         hod_email: str, status: str, comments: str = "") -> bool:
        """Add or update certification for a cycle"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM certifications WHERE vendor_id = ? AND certification_cycle = ?",
                (vendor_id, certification_cycle)
            )
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE certifications 
                    SET hod_email = ?, status = ?, comments = ?, timestamp = ?
                    WHERE id = ?
                """, (hod_email, status, comments, datetime.now(), existing[0]))
            else:
                cursor.execute("""
                    INSERT INTO certifications 
                    (vendor_id, certification_cycle, hod_email, status, comments, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (vendor_id, certification_cycle, hod_email, status, comments, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding certification: {e}")
            return False

    def get_certification_by_vendor_cycle(self, vendor_id: str, cycle: str) -> Optional[Dict[str, Any]]:
        """Get certification for a vendor in specific cycle"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM certifications WHERE vendor_id = ? AND certification_cycle = ?",
            (vendor_id, cycle)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None

    def get_all_certifications(self, cycle: str = None) -> pd.DataFrame:
        """Get all certifications, optionally filtered by cycle"""
        conn = self.get_connection()
        if cycle:
            df = pd.read_sql_query("""
                SELECT 
                    c.id,
                    c.vendor_id,
                    v.vendor_name,
                    v.department,
                    v.owner_email,
                    c.certification_cycle,
                    c.hod_email,
                    c.status,
                    c.comments,
                    c.timestamp
                FROM certifications c
                LEFT JOIN vendors v ON c.vendor_id = v.vendor_id
                WHERE c.certification_cycle = ?
                ORDER BY c.timestamp DESC
            """, conn, params=(cycle,))
        else:
            df = pd.read_sql_query("""
                SELECT 
                    c.id,
                    c.vendor_id,
                    v.vendor_name,
                    v.department,
                    v.owner_email,
                    c.certification_cycle,
                    c.hod_email,
                    c.status,
                    c.comments,
                    c.timestamp
                FROM certifications c
                LEFT JOIN vendors v ON c.vendor_id = v.vendor_id
                ORDER BY c.certification_cycle DESC, c.timestamp DESC
            """, conn)
        conn.close()
        return df

    def get_certifications_by_hod(self, hod_email: str, cycle: str) -> pd.DataFrame:
        """Get certifications for a specific HoD in a cycle"""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT 
                c.id,
                c.vendor_id,
                v.vendor_name,
                v.department,
                c.certification_cycle,
                c.hod_email,
                c.status,
                c.comments,
                c.timestamp
            FROM certifications c
            LEFT JOIN vendors v ON c.vendor_id = v.vendor_id
            WHERE c.hod_email = ? AND c.certification_cycle = ?
            ORDER BY c.timestamp DESC
        """, conn, params=(hod_email, cycle))
        conn.close()
        return df

    def get_certification_status_summary(self, cycle: str = None) -> Dict[str, int]:
        """Get certification status summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if cycle:
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM certifications
                WHERE certification_cycle = ?
                GROUP BY status
            """, (cycle,))
        else:
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM certifications
                GROUP BY status
            """)
        
        summary = {}
        for status, count in cursor.fetchall():
            summary[status] = count
        
        conn.close()
        return summary

    # ============ DASHBOARD METRICS ============
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get metrics for FP&A dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM vendors")
        total_vendors = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vendors WHERE active = 1")
        active_vendors = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agreements")
        total_agreements = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM obligations")
        total_obligations = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_vendors": total_vendors,
            "active_vendors": active_vendors,
            "total_agreements": total_agreements,
            "total_obligations": total_obligations,
        }

    def get_vendors_by_department_count(self) -> Dict[str, int]:
        """Get vendor count by department"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT department, COUNT(*) as count
            FROM vendors
            GROUP BY department
            ORDER BY count DESC
        """)
        
        result = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return result

    def get_obligations_by_status(self) -> Dict[str, int]:
        """Get obligation count by billing status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT billing_status, COUNT(*) as count
            FROM obligations
            WHERE billing_status IS NOT NULL
            GROUP BY billing_status
            ORDER BY count DESC
        """)
        
        result = {row[0] or "Unknown": row[1] for row in cursor.fetchall()}
        conn.close()
        return result

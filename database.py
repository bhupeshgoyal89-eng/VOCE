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
            print(f"DEBUG migrate_schema: Current vendor columns: {columns}")
            
            if 'owner' in columns and 'owner_email' not in columns:
                print("DEBUG migrate_schema: Migrating owner -> owner_email")
                try:
                    # SQLite 3.25.0+ supports RENAME COLUMN
                    cursor.execute("ALTER TABLE vendors RENAME COLUMN owner TO owner_email")
                    conn.commit()
                    print("DEBUG migrate_schema: Successfully renamed owner to owner_email")
                except Exception as e:
                    print(f"DEBUG migrate_schema: RENAME COLUMN failed: {e}")
                    # Fallback: create new column and copy data
                    try:
                        # Add new column
                        cursor.execute("ALTER TABLE vendors ADD COLUMN owner_email TEXT")
                        # Copy data
                        cursor.execute("UPDATE vendors SET owner_email = owner")
                        conn.commit()
                        print("DEBUG migrate_schema: Added owner_email column and copied data from owner")
                    except Exception as e2:
                        print(f"DEBUG migrate_schema: Fallback also failed: {e2}")
            
            # Check if certifications table needs updates
            cursor.execute("PRAGMA table_info(certifications)")
            cert_columns = [col[1] for col in cursor.fetchall()]
            print(f"DEBUG migrate_schema: Current cert columns: {cert_columns}")
            
            if 'certification_cycle' not in cert_columns:
                try:
                    cursor.execute("ALTER TABLE certifications ADD COLUMN certification_cycle TEXT DEFAULT '2026-03'")
                    conn.commit()
                    print("DEBUG migrate_schema: Added certification_cycle column")
                except Exception as e:
                    print(f"DEBUG migrate_schema: Failed to add certification_cycle: {e}")
            
            if 'hod_email' not in cert_columns:
                try:
                    cursor.execute("ALTER TABLE certifications ADD COLUMN hod_email TEXT")
                    conn.commit()
                    print("DEBUG migrate_schema: Added hod_email column")
                except Exception as e:
                    print(f"DEBUG migrate_schema: Failed to add hod_email: {e}")
                    
        except Exception as e:
            print(f"Schema migration notice: {e}")
            import traceback
            traceback.print_exc()
        
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
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check which column name exists
            cursor.execute("PRAGMA table_info(vendors)")
            columns = cursor.fetchall()
            vendor_cols = {row[1] for row in columns}
            print(f"DEBUG: Available vendor columns: {vendor_cols}")
            
            df = pd.DataFrame()
            
            # Try new schema first
            if 'owner_email' in vendor_cols:
                try:
                    print(f"DEBUG: Querying with owner_email column")
                    df = pd.read_sql_query(
                        "SELECT * FROM vendors WHERE owner_email = ? ORDER BY vendor_name",
                        conn,
                        params=(owner_email,)
                    )
                    print(f"DEBUG: Found {len(df)} vendors with owner_email={owner_email}")
                except Exception as e:
                    print(f"DEBUG: owner_email query failed: {e}, trying owner column")
                    df = pd.DataFrame()
            
            # Fallback to old schema
            if df.empty and 'owner' in vendor_cols:
                try:
                    print(f"DEBUG: Querying with owner column")
                    df = pd.read_sql_query(
                        "SELECT * FROM vendors WHERE owner = ? ORDER BY vendor_name",
                        conn,
                        params=(owner_email,)
                    )
                    print(f"DEBUG: Found {len(df)} vendors with owner={owner_email}")
                except Exception as e:
                    print(f"DEBUG: owner query also failed: {e}")
                    df = pd.DataFrame()
            
            # Last resort: get all vendors
            if df.empty:
                print(f"DEBUG: No owner/owner_email columns found, returning all vendors")
                try:
                    df = pd.read_sql_query("SELECT * FROM vendors ORDER BY vendor_name", conn)
                    print(f"DEBUG: Returned {len(df)} total vendors")
                except Exception as e:
                    print(f"DEBUG: Even basic query failed: {e}")
                    df = pd.DataFrame()
            
            conn.close()
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            print(f"Error getting vendors by owner: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def get_unique_departments(self) -> List[str]:
        """Get list of unique departments"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT department FROM vendors WHERE department IS NOT NULL ORDER BY department")
            departments = [row[0] for row in cursor.fetchall()]
            conn.close()
            return departments if departments else []
        except Exception as e:
            print(f"Error getting unique departments: {e}")
            return []

    def get_unique_owners(self) -> List[str]:
        """Get list of unique owner emails"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Try owner_email first (new schema), fall back to owner (old schema)
            try:
                cursor.execute("SELECT DISTINCT owner_email FROM vendors WHERE owner_email IS NOT NULL ORDER BY owner_email")
                owners = [row[0] for row in cursor.fetchall()]
            except:
                # Fallback to old schema
                cursor.execute("SELECT DISTINCT owner FROM vendors WHERE owner IS NOT NULL ORDER BY owner")
                owners = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return owners if owners else []
        except Exception as e:
            print(f"Error getting unique owners: {e}")
            return []

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
            
            # Check which columns exist in the table
            cursor.execute("PRAGMA table_info(obligations)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            
            # Build INSERT statement with only existing columns
            cols_to_insert = []
            values_to_insert = []
            
            col_mapping = {
                'vendor_id': obligation_data.get('vendor_id'),
                'agreement_type': obligation_data.get('agreement_type'),
                'agreement_term': obligation_data.get('agreement_term'),
                'scope_of_work': obligation_data.get('scope_of_work'),
                'service_levels': obligation_data.get('service_levels'),
                'penalties': obligation_data.get('penalties'),
                'reporting_obligations': obligation_data.get('reporting_obligations'),
                'servicing_obligations': obligation_data.get('servicing_obligations'),
                'kpis_or_volume_commitments': obligation_data.get('kpis_or_volume_commitments'),
                'data_security_protocols': obligation_data.get('data_security_protocols'),
                'payment_obligations': obligation_data.get('payment_obligations'),
                'milestone_completion': obligation_data.get('milestone_completion'),
                'dependencies': obligation_data.get('dependencies'),
                'billing_status': obligation_data.get('billing_status'),
                'created_at': datetime.now()
            }
            
            for col, val in col_mapping.items():
                if col in existing_cols:
                    cols_to_insert.append(col)
                    values_to_insert.append(val)
            
            # Only insert if we have at least vendor_id
            if 'vendor_id' not in cols_to_insert:
                return False
            
            placeholders = ', '.join(['?' for _ in values_to_insert])
            cols_str = ', '.join(cols_to_insert)
            
            sql = f"INSERT INTO obligations ({cols_str}) VALUES ({placeholders})"
            cursor.execute(sql, values_to_insert)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding obligation: {e}")
            return False

    def get_all_obligations(self) -> pd.DataFrame:
        """Get all obligations with vendor details"""
        try:
            conn = self.get_connection()
            # Try new schema first, fall back to simple query
            try:
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
            except:
                # Fallback to simple query for old schema
                df = pd.read_sql_query("""
                    SELECT 
                        o.*,
                        v.vendor_name,
                        v.department
                    FROM obligations o
                    LEFT JOIN vendors v ON o.vendor_id = v.vendor_id
                    ORDER BY o.created_at DESC
                """, conn)
            
            conn.close()
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            print(f"Error getting all obligations: {e}")
            return pd.DataFrame()

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
        try:
            conn = self.get_connection()
            search_pattern = f"%{search_term}%"
            
            try:
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
            except:
                # Fallback for old schema
                df = pd.read_sql_query("""
                    SELECT 
                        o.*,
                        v.vendor_name,
                        v.department
                    FROM obligations o
                    LEFT JOIN vendors v ON o.vendor_id = v.vendor_id
                    WHERE 
                        v.vendor_name LIKE ? OR
                        o.scope_of_work LIKE ?
                    ORDER BY o.created_at DESC
                """, conn, params=(search_pattern, search_pattern))
            
            conn.close()
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            print(f"Error searching obligations: {e}")
            return pd.DataFrame()

    # ============ CERTIFICATION OPERATIONS ============
    
    def add_certification(self, vendor_id: str, certification_cycle: str, 
                         hod_email: str, status: str, comments: str = "") -> bool:
        """Add or update certification for a cycle"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            print(f"DEBUG add_certification: vendor_id={vendor_id}, cycle={certification_cycle}, hod_email={hod_email}, status={status}")
            
            # First verify vendor exists
            cursor.execute("SELECT vendor_id FROM vendors WHERE vendor_id = ?", (vendor_id,))
            vendor_check = cursor.fetchone()
            print(f"DEBUG add_certification: vendor_check = {vendor_check}")
            
            if not vendor_check:
                print(f"ERROR: Vendor {vendor_id} does not exist in database")
                return False
            
            # Check for existing certification
            cursor.execute(
                "SELECT id FROM certifications WHERE vendor_id = ? AND certification_cycle = ?",
                (vendor_id, certification_cycle)
            )
            existing = cursor.fetchone()
            print(f"DEBUG add_certification: existing record = {existing}")
            
            if existing:
                print(f"DEBUG add_certification: Updating existing record id={existing[0]}")
                try:
                    cursor.execute("""
                        UPDATE certifications 
                        SET hod_email = ?, status = ?, comments = ?, timestamp = ?
                        WHERE id = ?
                    """, (hod_email, status, comments, datetime.now(), existing[0]))
                    conn.commit()
                    print(f"DEBUG add_certification: Updated successfully, rows: {cursor.rowcount}")
                except sqlite3.IntegrityError as e:
                    print(f"ERROR: IntegrityError during UPDATE: {e}")
                    conn.rollback()
                    return False
            else:
                print(f"DEBUG add_certification: Inserting new record")
                try:
                    cursor.execute("""
                        INSERT INTO certifications 
                        (vendor_id, certification_cycle, hod_email, status, comments, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (vendor_id, certification_cycle, hod_email, status, comments, datetime.now()))
                    conn.commit()
                    print(f"DEBUG add_certification: Inserted successfully, rows: {cursor.rowcount}")
                except sqlite3.IntegrityError as e:
                    print(f"ERROR: IntegrityError during INSERT: {e}")
                    conn.rollback()
                    return False
            
            conn.close()
            print(f"DEBUG add_certification: Success - returning True")
            return True
        except Exception as e:
            print(f"Error adding certification: {e}")
            import traceback
            traceback.print_exc()
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
        try:
            conn = self.get_connection()
            
            # Check if certification_cycle column exists
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(certifications)")
            cert_cols = {row[1] for row in cursor.fetchall()}
            
            if 'certification_cycle' in cert_cols:
                # New schema with cycles
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
            else:
                # Old schema without cycles - return basic certifications
                df = pd.read_sql_query("""
                    SELECT 
                        c.certification_id as id,
                        c.vendor_id,
                        v.vendor_name,
                        v.department,
                        v.owner_email,
                        c.status,
                        c.comments,
                        c.timestamp
                    FROM certifications c
                    LEFT JOIN vendors v ON c.vendor_id = v.vendor_id
                    ORDER BY c.timestamp DESC
                """, conn)
            
            conn.close()
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            print(f"Error getting certifications: {e}")
            return pd.DataFrame()

    def get_certifications_by_hod(self, hod_email: str, cycle: str) -> pd.DataFrame:
        """Get certifications for a specific HoD in a cycle"""
        try:
            conn = self.get_connection()
            
            # Check if hod_email column exists
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(certifications)")
            cert_cols = {row[1] for row in cursor.fetchall()}
            print(f"DEBUG get_certifications_by_hod: Available cert columns: {cert_cols}")
            
            if 'hod_email' in cert_cols and 'certification_cycle' in cert_cols:
                # New schema
                print(f"DEBUG get_certifications_by_hod: Using new schema, querying hod_email={hod_email}, cycle={cycle}")
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
                print(f"DEBUG get_certifications_by_hod: Found {len(df)} records")
            else:
                # Old schema - can't filter by hod_email or cycle
                print(f"DEBUG get_certifications_by_hod: Using old schema, returning all certifications")
                df = pd.read_sql_query("""
                    SELECT 
                        c.certification_id as id,
                        c.vendor_id,
                        v.vendor_name,
                        v.department,
                        c.status,
                        c.comments,
                        c.timestamp
                    FROM certifications c
                    LEFT JOIN vendors v ON c.vendor_id = v.vendor_id
                    ORDER BY c.timestamp DESC
                """, conn)
            
            conn.close()
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            print(f"Error getting HoD certifications: {e}")
            return pd.DataFrame()

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

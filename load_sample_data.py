#!/usr/bin/env python3
"""
Load sample vendor data into the database
Run this once to populate the database with test vendors
"""

import pandas as pd
import sys
sys.path.insert(0, '.')

from database import Database
from models import Vendor

def load_sample_vendors():
    """Load vendors from CSV file"""
    db = Database(db_path="data/voce.db")
    
    # Read CSV
    vendors_df = pd.read_csv('sample_vendors.csv')
    print(f"Read {len(vendors_df)} vendors from sample_vendors.csv")
    
    # Convert 'owner' column to 'owner_email' if needed
    if 'owner' in vendors_df.columns and 'owner_email' not in vendors_df.columns:
        print("Converting 'owner' column to 'owner_email'")
        # Map owner names to email addresses
        owner_email_map = {
            'John Smith': 'cto@company.com',
            'Jane Doe': 'cfo@company.com',
            'Mike Johnson': 'coo@company.com',
            'Sarah Williams': 'cto@company.com',
            'Robert Brown': 'cfo@company.com',
            'James Wilson': 'coo@company.com',
            'Emma Taylor': 'cmo@company.com',
            'Lisa Anderson': 'chro@company.com',
            'David Martinez': 'cdo@company.com',
            'Jennifer Lee': 'coo@company.com'
        }
        vendors_df['owner_email'] = vendors_df['owner'].map(owner_email_map)
    
    # Add missing vendors that are referenced in the app
    # Add V015 for testing (Internet Leased Line from the UI)
    additional_vendors = pd.DataFrame([
        {'vendor_id': 'V015', 'vendor_name': 'Internet Leased Line', 'department': 'Technology', 
         'nature_of_expense': 'Internet Leased Line', 'owner_email': 'cto@company.com', 
         'recurring': 1, 'active': 1, 'last_contract_revision_date': '2024-08-30'}
    ])
    
    vendors_df = pd.concat([vendors_df, additional_vendors], ignore_index=True)
    print(f"Total vendors to load: {len(vendors_df)}")
    
    # Load into database
    added_count = 0
    errors = []
    
    for idx, row in vendors_df.iterrows():
        try:
            vendor = Vendor(
                vendor_id=row['vendor_id'],
                vendor_name=row['vendor_name'],
                department=row['department'],
                nature_of_expense=row['nature_of_expense'],
                owner_email=row.get('owner_email', row.get('owner', 'unknown@company.com')),
                recurring=bool(row['recurring']),
                active=bool(row['active']),
                last_contract_revision_date=str(row.get('last_contract_revision_date', ''))
            )
            
            db.add_vendor(vendor)
            added_count += 1
            print(f"  ✅ Added {row['vendor_id']}: {row['vendor_name']}")
            
        except Exception as e:
            errors.append(f"{row['vendor_id']}: {str(e)}")
            print(f"  ❌ Error adding {row['vendor_id']}: {e}")
    
    print(f"\n✅ Successfully loaded {added_count} vendors")
    if errors:
        print(f"\n⚠️  {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
    
    return added_count, errors

if __name__ == '__main__':
    load_sample_vendors()

"""
Resume Database Creation Script
Checks what's already created and continues from there
"""

import psycopg2
from psycopg2.extras import execute_values
import sys

DB_CONFIG = {
    "dbname": "mydb",
    "user": "admin",
    "password": "admin123",
    "host": "192.168.1.81",
    "port": 5432
}

def check_table_status():
    """Check which tables exist and their row counts"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        tables = [
            'test_users', 'test_customers', 'test_products', 'test_orders',
            'test_order_items', 'test_transactions', 'test_logs', 'test_sessions',
            'test_analytics', 'test_audit_log'
        ]
        
        print("\n" + "="*80)
        print("DATABASE STATUS CHECK")
        print("="*80)
        
        status = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                status[table] = count
                print(f"✓ {table:25s}: {count:>10,} rows")
            except Exception as e:
                status[table] = 0
                print(f"✗ {table:25s}: Not created or empty")
        
        cursor.close()
        conn.close()
        
        return status
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return None

def main():
    print("\n" + "="*80)
    print("RESUME DATABASE CREATION")
    print("="*80)
    
    status = check_table_status()
    
    if status is None:
        print("\n❌ Cannot connect to database. Please check connection details.")
        return
    
    # Check what's completed
    expected_counts = {
        'test_users': 50000,
        'test_customers': 20000,
        'test_products': 10000,
        'test_orders': 100000,
        'test_order_items': 250000,
        'test_transactions': 150000,
        'test_logs': 500000,
        'test_sessions': 30000,
        'test_analytics': 200000,
        'test_audit_log': 50000
    }
    
    print("\n" + "="*80)
    print("COMPLETION STATUS")
    print("="*80)
    
    all_complete = True
    for table, expected in expected_counts.items():
        actual = status.get(table, 0)
        if actual >= expected:
            print(f"✓ {table:25s}: Complete ({actual:,}/{expected:,})")
        else:
            print(f"⏳ {table:25s}: Incomplete ({actual:,}/{expected:,})")
            all_complete = False
    
    if all_complete:
        print("\n✅ All tables are fully populated!")
        print("\nYou can now:")
        print("  1. Run: python test_all_issues.py")
        print("  2. Connect to the database in AI SQL Optimizer")
        print("  3. Test the queries from QUICK_TEST_QUERIES.md")
    else:
        print("\n⚠️  Database creation was interrupted.")
        print("\nOptions:")
        print("  1. Re-run: python create_test_database_enhanced.py")
        print("  2. Or manually complete the missing tables")
        print("\nNote: The script will drop and recreate all tables.")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

"""
Run database migration inside Docker container
"""
import sqlite3
import sys

def migrate_database():
    """Add detected_issues column to optimizations table"""
    db_path = "/app/app/db/observability.db"
    
    print(f"📁 Database path: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(optimizations)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"📋 Current columns: {columns}")
        
        if 'detected_issues' not in columns:
            print("🔧 Adding detected_issues column to optimizations table...")
            cursor.execute("""
                ALTER TABLE optimizations 
                ADD COLUMN detected_issues TEXT
            """)
            conn.commit()
            print("✅ Migration completed successfully!")
            return True
        else:
            print("✅ Column 'detected_issues' already exists")
            return True
    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("DATABASE MIGRATION (Docker Container)")
    print("="*70 + "\n")
    
    success = migrate_database()
    
    print("\n" + "="*70)
    if success:
        print("✅ MIGRATION COMPLETE")
    else:
        print("❌ MIGRATION FAILED")
        sys.exit(1)
    print("="*70 + "\n")

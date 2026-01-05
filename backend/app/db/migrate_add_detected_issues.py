"""
Database Migration: Add detected_issues column to optimizations table
"""
import sqlite3
import os
import sys

def migrate_database():
    """Add detected_issues column to optimizations table"""
    
    # Determine database path
    db_path = os.path.join(os.path.dirname(__file__), "observability.db")
    
    if not os.path.exists(db_path):
        print("ℹ️  Database does not exist yet. Will be created with correct schema on first run.")
        return True
    
    print(f"📁 Database path: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(optimizations)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'detected_issues' not in columns:
            print("🔧 Adding detected_issues column to optimizations table...")
            cursor.execute("""
                ALTER TABLE optimizations 
                ADD COLUMN detected_issues TEXT
            """)
            conn.commit()
            print("✅ Migration completed successfully!")
            print("   Column 'detected_issues' added to 'optimizations' table")
            return True
        else:
            print("✅ Column 'detected_issues' already exists, no migration needed")
            return True
    
    except sqlite3.Error as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("DATABASE MIGRATION: Add detected_issues column")
    print("="*70 + "\n")
    
    success = migrate_database()
    
    print("\n" + "="*70)
    if success:
        print("✅ MIGRATION COMPLETE")
        print("="*70)
        print("\nNext steps:")
        print("1. Restart the backend: docker-compose restart backend")
        print("2. Test optimization: python add_optimizations.py")
        print("3. Check dashboard at http://localhost:3000")
    else:
        print("❌ MIGRATION FAILED")
        print("="*70)
        print("\nPlease check the error messages above and try again.")
        sys.exit(1)

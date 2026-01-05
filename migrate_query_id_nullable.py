"""
Run database migration to make query_id nullable in optimizations table
"""
import sqlite3

def migrate_database():
    """Make query_id nullable in optimizations table"""
    db_path = "/app/app/db/observability.db"
    
    print(f"📁 Database path: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Making query_id nullable in optimizations table...")
        print("   This requires recreating the table...")
        
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        # Step 1: Create new table with correct schema
        cursor.execute("""
            CREATE TABLE optimizations_new (
                id INTEGER PRIMARY KEY,
                query_id INTEGER,
                connection_id INTEGER NOT NULL,
                original_sql TEXT NOT NULL,
                optimized_sql TEXT NOT NULL,
                execution_plan TEXT,
                explanation TEXT NOT NULL,
                recommendations TEXT,
                estimated_improvement_pct REAL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                applied_at TIMESTAMP,
                validated_at TIMESTAMP,
                detected_issues TEXT
            )
        """)
        
        # Step 2: Copy data from old table to new table
        cursor.execute("""
            INSERT INTO optimizations_new 
            SELECT * FROM optimizations
        """)
        
        # Step 3: Drop old table
        cursor.execute("DROP TABLE optimizations")
        
        # Step 4: Rename new table to original name
        cursor.execute("ALTER TABLE optimizations_new RENAME TO optimizations")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print("   query_id is now nullable in optimizations table")
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
    print("DATABASE MIGRATION: Make query_id nullable")
    print("="*70 + "\n")
    
    success = migrate_database()
    
    print("\n" + "="*70)
    if success:
        print("✅ MIGRATION COMPLETE")
    else:
        print("❌ MIGRATION FAILED")
    print("="*70 + "\n")

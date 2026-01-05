"""
Fix query_id column to be nullable in optimizations table
"""
import sqlite3
import os

def migrate_database():
    """Make query_id nullable in optimizations table"""
    db_path = "backend/app/db/observability.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    print(f"✓ Found database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(optimizations)")
        columns = cursor.fetchall()
        
        print("\nCurrent optimizations table schema:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
        
        # Check if query_id is already nullable
        query_id_col = [col for col in columns if col[1] == 'query_id'][0]
        if query_id_col[3] == 0:  # notnull = 0 means nullable
            print("\n✓ query_id is already nullable")
            conn.close()
            return True
        
        print("\n🔧 Making query_id nullable...")
        
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        # Step 1: Create new table with nullable query_id
        cursor.execute("""
            CREATE TABLE optimizations_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER,
                connection_id INTEGER NOT NULL,
                original_sql TEXT NOT NULL,
                optimized_sql TEXT NOT NULL,
                execution_plan TEXT,
                explanation TEXT,
                recommendations TEXT,
                estimated_improvement_pct REAL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                applied_at TIMESTAMP,
                validated_at TIMESTAMP,
                detected_issues TEXT,
                FOREIGN KEY (query_id) REFERENCES queries(id),
                FOREIGN KEY (connection_id) REFERENCES connections(id)
            )
        """)
        
        # Step 2: Copy data from old table
        cursor.execute("""
            INSERT INTO optimizations_new 
            SELECT * FROM optimizations
        """)
        
        # Step 3: Drop old table
        cursor.execute("DROP TABLE optimizations")
        
        # Step 4: Rename new table
        cursor.execute("ALTER TABLE optimizations_new RENAME TO optimizations")
        
        conn.commit()
        
        print("✓ Successfully made query_id nullable")
        
        # Verify
        cursor.execute("PRAGMA table_info(optimizations)")
        columns = cursor.fetchall()
        query_id_col = [col for col in columns if col[1] == 'query_id'][0]
        
        if query_id_col[3] == 0:
            print("✓ Verification passed: query_id is now nullable")
            conn.close()
            return True
        else:
            print("❌ Verification failed: query_id is still NOT NULL")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("DATABASE MIGRATION: Make query_id nullable")
    print("="*70 + "\n")
    
    success = migrate_database()
    
    if success:
        print("\n✅ Migration completed successfully")
    else:
        print("\n❌ Migration failed")

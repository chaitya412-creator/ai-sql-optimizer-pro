"""
Initialize PostgreSQL Database Schema
Creates all required tables in the PostgreSQL database
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from app.models.database import Base

# PostgreSQL Database configuration
DB_CONFIG = {
    "dbname": "mydb",
    "user": "admin",
    "password": "admin123",
    "host": "192.168.1.81",
    "port": 5432
}

DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"


def init_schema():
    """Initialize database schema"""
    
    print("\n" + "="*80)
    print("POSTGRESQL DATABASE SCHEMA INITIALIZATION")
    print("="*80)
    print(f"\nDatabase: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    print(f"User: {DB_CONFIG['user']}")
    print("="*80 + "\n")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✓ Connected to PostgreSQL")
            print(f"  Version: {version.split(',')[0]}\n")
        
        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
        
        print(f"\n✓ Created {len(tables)} tables:")
        for table in tables:
            print(f"  • {table}")
        
        print("\n" + "="*80)
        print("✅ SCHEMA INITIALIZATION COMPLETE")
        print("="*80 + "\n")
        
        print("Next step: Run the data population script")
        print("  python populate_test_data_auto.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_schema()
    sys.exit(0 if success else 1)

"""
Migration script to add index_recommendations table
Run this to ensure the IndexRecommendation table exists
"""
from app.models.database import Base, engine, IndexRecommendation

def migrate():
    """Add index_recommendations table"""
    print("Creating index_recommendations table...")
    try:
        Base.metadata.create_all(bind=engine, tables=[IndexRecommendation.__table__])
        print("✅ Migration complete! IndexRecommendation table is ready.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate()

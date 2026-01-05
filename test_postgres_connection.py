"""
Test PostgreSQL Connection and Database Operations
"""
import sys
sys.path.insert(0, 'backend')

from app.models.database import engine, SessionLocal, Base
from app.models.database import Connection, Query, Optimization, QueryIssue
from app.models.database import OptimizationFeedback, OptimizationPattern, ConfigurationChange, WorkloadMetrics
from app.config import settings
from sqlalchemy import text
from loguru import logger
from datetime import datetime


def test_connection():
    """Test basic database connection"""
    try:
        logger.info("Testing PostgreSQL connection...")
        logger.info(f"Database URL: {settings.DATABASE_URL}")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✅ Connected to PostgreSQL")
            logger.info(f"   Version: {version[:50]}...")
        
        return True
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False


def test_tables():
    """Test that all tables exist"""
    try:
        logger.info("\nTesting tables...")
        
        with engine.connect() as conn:
            # Get list of tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'connections',
                'queries',
                'optimizations',
                'query_issues',
                'optimization_feedback',
                'optimization_patterns',
                'configuration_changes',
                'workload_metrics'
            ]
            
            logger.info(f"Found {len(tables)} tables:")
            for table in expected_tables:
                if table in tables:
                    logger.info(f"  ✅ {table}")
                else:
                    logger.error(f"  ❌ {table} - MISSING!")
            
            return len(tables) == len(expected_tables)
            
    except Exception as e:
        logger.error(f"❌ Table check failed: {e}")
        return False


def test_crud_operations():
    """Test CRUD operations"""
    try:
        logger.info("\nTesting CRUD operations...")
        
        db = SessionLocal()
        
        # CREATE - Add a test connection
        logger.info("Testing CREATE...")
        test_conn = Connection(
            name="Test PostgreSQL Connection",
            engine="postgresql",
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password_encrypted="encrypted_password_here"
        )
        db.add(test_conn)
        db.commit()
        db.refresh(test_conn)
        logger.info(f"  ✅ Created connection with ID: {test_conn.id}")
        
        # READ - Query the connection
        logger.info("Testing READ...")
        conn = db.query(Connection).filter(Connection.name == "Test PostgreSQL Connection").first()
        if conn:
            logger.info(f"  ✅ Read connection: {conn.name}")
        else:
            logger.error("  ❌ Failed to read connection")
            return False
        
        # UPDATE - Update the connection
        logger.info("Testing UPDATE...")
        conn.port = 5433
        db.commit()
        db.refresh(conn)
        if conn.port == 5433:
            logger.info(f"  ✅ Updated connection port to: {conn.port}")
        else:
            logger.error("  ❌ Failed to update connection")
            return False
        
        # DELETE - Remove the connection
        logger.info("Testing DELETE...")
        db.delete(conn)
        db.commit()
        
        # Verify deletion
        conn = db.query(Connection).filter(Connection.name == "Test PostgreSQL Connection").first()
        if conn is None:
            logger.info("  ✅ Deleted connection successfully")
        else:
            logger.error("  ❌ Failed to delete connection")
            return False
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ CRUD operations failed: {e}")
        return False


def test_new_tables():
    """Test new ML-related tables"""
    try:
        logger.info("\nTesting new ML tables...")
        
        db = SessionLocal()
        
        # Create parent records first (connection and optimization)
        logger.info("Creating parent records...")
        test_conn = Connection(
            name="Test ML Connection",
            engine="postgresql",
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password_encrypted="encrypted_password"
        )
        db.add(test_conn)
        db.commit()
        db.refresh(test_conn)
        
        test_opt = Optimization(
            connection_id=test_conn.id,
            original_sql="SELECT * FROM users",
            optimized_sql="SELECT id, name FROM users",
            explanation="Optimized by selecting only needed columns",
            status="pending"
        )
        db.add(test_opt)
        db.commit()
        db.refresh(test_opt)
        logger.info(f"  ✅ Created test connection (ID: {test_conn.id}) and optimization (ID: {test_opt.id})")
        
        # Test OptimizationFeedback
        logger.info("Testing OptimizationFeedback table...")
        feedback = OptimizationFeedback(
            optimization_id=test_opt.id,
            connection_id=test_conn.id,
            before_metrics={"exec_time": 1000, "cpu": 50},
            after_metrics={"exec_time": 500, "cpu": 25},
            actual_improvement_pct=50.0,
            estimated_improvement_pct=45.0,
            accuracy_score=0.9,
            applied_at=datetime.now(),
            dba_rating=5
        )
        db.add(feedback)
        db.commit()
        logger.info("  ✅ OptimizationFeedback table works")
        
        # Test OptimizationPattern
        logger.info("Testing OptimizationPattern table...")
        pattern = OptimizationPattern(
            pattern_type="index",
            pattern_signature="missing_index_on_email",
            original_pattern="SELECT * FROM users WHERE email = ?",
            optimized_pattern="CREATE INDEX idx_users_email ON users(email)",
            success_rate=0.95,
            avg_improvement_pct=60.0,
            times_applied=10,
            times_successful=9,
            database_type="postgresql"
        )
        db.add(pattern)
        db.commit()
        logger.info("  ✅ OptimizationPattern table works")
        
        # Test ConfigurationChange
        logger.info("Testing ConfigurationChange table...")
        config = ConfigurationChange(
            connection_id=test_conn.id,
            parameter_name="work_mem",
            old_value="4MB",
            new_value="16MB",
            change_reason="Improve sort performance",
            status="pending"
        )
        db.add(config)
        db.commit()
        logger.info("  ✅ ConfigurationChange table works")
        
        # Test WorkloadMetrics
        logger.info("Testing WorkloadMetrics table...")
        metrics = WorkloadMetrics(
            connection_id=test_conn.id,
            total_queries=1000,
            avg_exec_time=50.5,
            cpu_usage=45.0,
            io_usage=30.0,
            workload_type="oltp"
        )
        db.add(metrics)
        db.commit()
        logger.info("  ✅ WorkloadMetrics table works")
        
        # Clean up test data (in correct order due to foreign keys)
        db.query(OptimizationFeedback).delete()
        db.query(OptimizationPattern).delete()
        db.query(ConfigurationChange).delete()
        db.query(WorkloadMetrics).delete()
        db.query(Optimization).delete()
        db.query(Connection).filter(Connection.name == "Test ML Connection").delete()
        db.commit()
        logger.info("  ✅ Cleaned up test data")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ New tables test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    logger.info("="*70)
    logger.info("PostgreSQL Connection and Operations Test")
    logger.info("="*70)
    
    results = {
        "Connection Test": test_connection(),
        "Tables Test": test_tables(),
        "CRUD Operations": test_crud_operations(),
        "New ML Tables": test_new_tables()
    }
    
    logger.info("\n" + "="*70)
    logger.info("TEST RESULTS")
    logger.info("="*70)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    logger.info("="*70)
    if all_passed:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("\nPostgreSQL is ready to use!")
        logger.info("Next steps:")
        logger.info("1. Start the backend: uvicorn backend.main:app --reload")
        logger.info("2. Test API endpoints at http://localhost:8000/docs")
        logger.info("3. Verify connections page in frontend")
    else:
        logger.error("❌ SOME TESTS FAILED!")
        logger.error("Please check the errors above and fix them.")
    
    logger.info("="*70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

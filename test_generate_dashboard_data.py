"""
Generate test data for dashboard display
This script will create test connections, queries, and optimizations with detected issues
"""
import sys
import os
import asyncio
import requests
from datetime import datetime, timedelta
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, Connection, Query, Optimization, QueryIssue
from app.core.security import security_manager
from app.core.plan_analyzer import PlanAnalyzer

# Sample execution plan (PostgreSQL format)
SAMPLE_PLAN = {
    "Plan": {
        "Node Type": "Seq Scan",
        "Relation Name": "users",
        "Plan Rows": 10000,
        "Total Cost": 1234.56
    }
}

# Sample problematic queries
TEST_QUERIES = [
    "SELECT * FROM users WHERE id > 100",
    "SELECT name FROM products WHERE name LIKE '%phone%'",
    "SELECT * FROM orders WHERE status = 'pending' OR status = 'processing' OR status = 'shipped' OR status = 'delivered'",
    "SELECT * FROM users WHERE UPPER(email) = 'TEST@EXAMPLE.COM'",
    """
    SELECT u.*, o.*, p.*
    FROM users u
    JOIN orders o ON u.id = o.user_id
    JOIN products p ON o.product_id = p.id
    WHERE u.created_at > '2024-01-01'
    """
]

async def generate_test_data():
    """Generate test data for dashboard"""
    print("\n" + "="*70)
    print("GENERATING TEST DATA FOR DASHBOARD")
    print("="*70)
    
    # Create database engine
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///./test.db')
    engine = create_engine(db_url)
    
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Step 1: Create test connection if none exists
        connection = db.query(Connection).first()
        if not connection:
            print("\nCreating test connection...")
            connection = Connection(
                name="Test PostgreSQL",
                engine="postgresql",
                host="localhost",
                port=5432,
                database="testdb",
                username="postgres",
                password_encrypted=security_manager.encrypt("password"),
                ssl_enabled=False,
                monitoring_enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(connection)
            db.commit()
            db.refresh(connection)
            print(f"✓ Created connection with ID: {connection.id}")
        else:
            print(f"\nUsing existing connection: {connection.name} (ID: {connection.id})")
        
        # Step 2: Create test queries
        print("\nCreating test queries...")
        queries = []
        for i, sql in enumerate(TEST_QUERIES):
            query = Query(
                connection_id=connection.id,
                query_hash=f"test_hash_{i}",
                sql_text=sql,
                avg_exec_time_ms=100 * (i + 1),
                total_exec_time_ms=1000 * (i + 1),
                calls=10 * (i + 1),
                rows_returned=100 * (i + 1),
                buffer_hits=500 * (i + 1),
                buffer_reads=50 * (i + 1),
                discovered_at=datetime.utcnow() - timedelta(hours=i),
                last_seen_at=datetime.utcnow(),
                optimized=False
            )
            db.add(query)
            queries.append(query)
        
        db.commit()
        for query in queries:
            db.refresh(query)
            print(f"✓ Created query with ID: {query.id}")
        
        # Step 3: Create optimizations with detected issues
        print("\nCreating optimizations with detected issues...")
        for i, query in enumerate(queries):
            # Analyze query to get detection results
            detection_result = PlanAnalyzer.analyze_plan(
                plan=SAMPLE_PLAN,
                engine="postgresql",
                sql_query=query.sql_text,
                query_stats={
                    "buffer_hits": query.buffer_hits,
                    "buffer_reads": query.buffer_reads,
                    "avg_time_ms": query.avg_exec_time_ms,
                    "calls": query.calls
                }
            )
            
            # Create optimization
            optimization = Optimization(
                query_id=query.id,
                connection_id=connection.id,
                original_sql=query.sql_text,
                optimized_sql=f"/* Optimized */ {query.sql_text}",
                execution_plan=SAMPLE_PLAN,
                explanation="This is a test optimization with detected issues",
                recommendations="Add indexes, use specific columns instead of *",
                estimated_improvement_pct=25.0,
                status="pending",
                created_at=datetime.utcnow() - timedelta(hours=i),
                detected_issues=detection_result
            )
            
            db.add(optimization)
            db.commit()
            db.refresh(optimization)
            print(f"✓ Created optimization with ID: {optimization.id} - {detection_result['total_issues']} issues")
            
            # Create individual issues
            for issue in detection_result.get("issues", []):
                query_issue = QueryIssue(
                    query_id=query.id,
                    optimization_id=optimization.id,
                    connection_id=connection.id,
                    issue_type=issue["issue_type"],
                    severity=issue["severity"],
                    title=issue["title"],
                    description=issue["description"],
                    affected_objects=issue["affected_objects"],
                    recommendations=issue["recommendations"],
                    metrics=issue.get("metrics", {}),
                    detected_at=datetime.utcnow() - timedelta(hours=i),
                    resolved=False
                )
                db.add(query_issue)
            
            # Mark query as optimized
            query.optimized = True
            db.commit()
        
        # Step 4: Verify data
        total_queries = db.query(Query).count()
        total_optimizations = db.query(Optimization).count()
        total_issues = db.query(QueryIssue).count()
        
        print("\n" + "="*70)
        print("✅ TEST DATA GENERATION COMPLETE")
        print("="*70)
        print(f"Total Queries: {total_queries}")
        print(f"Total Optimizations: {total_optimizations}")
        print(f"Total Issues: {total_issues}")
        print("\nDashboard should now display these values.")
        print("Please restart the backend service to ensure data is refreshed:")
        print("docker-compose restart backend")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(generate_test_data())

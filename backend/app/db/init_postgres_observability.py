"""
PostgreSQL Observability Database Initialization Script
Creates the ai_sql_optimizer_observability database and all required tables
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
from loguru import logger

# PostgreSQL connection details
POSTGRES_CONFIG = {
    "user": "admin",
    "password": "admin123",
    "host": "192.168.1.81",
    "port": 5432
}

DB_NAME = "ai_sql_optimizer_observability"


def create_database():
    """Create the observability database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (default postgres database)
        conn = psycopg2.connect(
            dbname="postgres",
            **POSTGRES_CONFIG
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if exists:
            logger.info(f"Database '{DB_NAME}' already exists")
        else:
            # Create database
            cursor.execute(f'CREATE DATABASE {DB_NAME}')
            logger.info(f"✅ Created database '{DB_NAME}'")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create database: {e}")
        return False


def create_tables():
    """Create all required tables with indexes and constraints"""
    try:
        # Connect to the observability database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            **POSTGRES_CONFIG
        )
        cursor = conn.cursor()
        
        logger.info("Creating tables...")
        
        # Table 1: Connections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                engine VARCHAR(50) NOT NULL,
                host VARCHAR(255) NOT NULL,
                port INTEGER NOT NULL,
                database VARCHAR(255) NOT NULL,
                username VARCHAR(255) NOT NULL,
                password_encrypted TEXT NOT NULL,
                ssl_enabled BOOLEAN DEFAULT FALSE,
                monitoring_enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_monitored_at TIMESTAMP NULL
            )
        """)
        logger.info("✅ Created table: connections")
        
        # Table 2: Queries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id SERIAL PRIMARY KEY,
                connection_id INTEGER NOT NULL,
                query_hash VARCHAR(64) NOT NULL,
                sql_text TEXT NOT NULL,
                avg_exec_time_ms DOUBLE PRECISION NOT NULL,
                total_exec_time_ms DOUBLE PRECISION NOT NULL,
                calls INTEGER NOT NULL,
                rows_returned INTEGER NULL,
                buffer_hits INTEGER NULL,
                buffer_reads INTEGER NULL,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                optimized BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (connection_id) REFERENCES connections(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Created table: queries")
        
        # Table 3: Optimizations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimizations (
                id SERIAL PRIMARY KEY,
                query_id INTEGER NULL,
                connection_id INTEGER NOT NULL,
                original_sql TEXT NOT NULL,
                optimized_sql TEXT NOT NULL,
                execution_plan JSONB NULL,
                explanation TEXT NOT NULL,
                recommendations TEXT NULL,
                estimated_improvement_pct DOUBLE PRECISION NULL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                applied_at TIMESTAMP NULL,
                validated_at TIMESTAMP NULL,
                detected_issues JSONB NULL,
                FOREIGN KEY (query_id) REFERENCES queries(id) ON DELETE SET NULL,
                FOREIGN KEY (connection_id) REFERENCES connections(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Created table: optimizations")
        
        # Table 4: Query Issues
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_issues (
                id SERIAL PRIMARY KEY,
                query_id INTEGER NULL,
                optimization_id INTEGER NULL,
                connection_id INTEGER NOT NULL,
                issue_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                affected_objects JSONB NOT NULL,
                recommendations JSONB NOT NULL,
                metrics JSONB NULL,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at TIMESTAMP NULL,
                FOREIGN KEY (query_id) REFERENCES queries(id) ON DELETE SET NULL,
                FOREIGN KEY (optimization_id) REFERENCES optimizations(id) ON DELETE SET NULL,
                FOREIGN KEY (connection_id) REFERENCES connections(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Created table: query_issues")
        
        # Table 5: Optimization Feedback (NEW)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_feedback (
                id SERIAL PRIMARY KEY,
                optimization_id INTEGER NOT NULL,
                connection_id INTEGER NOT NULL,
                before_metrics JSONB NOT NULL,
                after_metrics JSONB NOT NULL,
                actual_improvement_pct DOUBLE PRECISION NULL,
                estimated_improvement_pct DOUBLE PRECISION NULL,
                accuracy_score DOUBLE PRECISION NULL,
                applied_at TIMESTAMP NOT NULL,
                measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                feedback_status VARCHAR(50) DEFAULT 'success',
                dba_rating INTEGER NULL CHECK (dba_rating >= 1 AND dba_rating <= 5),
                dba_comments TEXT NULL,
                FOREIGN KEY (optimization_id) REFERENCES optimizations(id) ON DELETE CASCADE,
                FOREIGN KEY (connection_id) REFERENCES connections(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Created table: optimization_feedback")
        
        # Table 6: Optimization Patterns (NEW)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_patterns (
                id SERIAL PRIMARY KEY,
                pattern_type VARCHAR(50) NOT NULL,
                pattern_signature VARCHAR(255) NOT NULL,
                original_pattern TEXT NOT NULL,
                optimized_pattern TEXT NOT NULL,
                success_rate DOUBLE PRECISION DEFAULT 0.0,
                avg_improvement_pct DOUBLE PRECISION DEFAULT 0.0,
                times_applied INTEGER DEFAULT 0,
                times_successful INTEGER DEFAULT 0,
                database_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created table: optimization_patterns")
        
        # Table 7: Configuration Changes (NEW)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuration_changes (
                id SERIAL PRIMARY KEY,
                connection_id INTEGER NOT NULL,
                parameter_name VARCHAR(255) NOT NULL,
                old_value VARCHAR(255) NULL,
                new_value VARCHAR(255) NOT NULL,
                change_reason TEXT NOT NULL,
                estimated_impact JSONB NULL,
                actual_impact JSONB NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reverted_at TIMESTAMP NULL,
                status VARCHAR(50) DEFAULT 'pending',
                FOREIGN KEY (connection_id) REFERENCES connections(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Created table: configuration_changes")
        
        # Table 8: Workload Metrics (NEW)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workload_metrics (
                id SERIAL PRIMARY KEY,
                connection_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_queries INTEGER NOT NULL,
                avg_exec_time DOUBLE PRECISION NOT NULL,
                cpu_usage DOUBLE PRECISION NULL,
                io_usage DOUBLE PRECISION NULL,
                memory_usage DOUBLE PRECISION NULL,
                active_connections INTEGER NULL,
                slow_queries_count INTEGER NULL,
                workload_type VARCHAR(50) NULL,
                FOREIGN KEY (connection_id) REFERENCES connections(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Created table: workload_metrics")
        
        # Create indexes for performance
        logger.info("Creating indexes...")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_connection_id ON queries(connection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_query_hash ON queries(query_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_optimized ON queries(optimized)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_last_seen ON queries(last_seen_at DESC)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_optimizations_connection_id ON optimizations(connection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_optimizations_query_id ON optimizations(query_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_optimizations_status ON optimizations(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_optimizations_created_at ON optimizations(created_at DESC)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_issues_connection_id ON query_issues(connection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_issues_issue_type ON query_issues(issue_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_issues_severity ON query_issues(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_issues_detected_at ON query_issues(detected_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_issues_resolved ON query_issues(resolved)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_optimization_id ON optimization_feedback(optimization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_connection_id ON optimization_feedback(connection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_measured_at ON optimization_feedback(measured_at DESC)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_pattern_type ON optimization_patterns(pattern_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_database_type ON optimization_patterns(database_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_success_rate ON optimization_patterns(success_rate DESC)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_config_connection_id ON configuration_changes(connection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_config_status ON configuration_changes(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_config_applied_at ON configuration_changes(applied_at DESC)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workload_connection_id ON workload_metrics(connection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workload_timestamp ON workload_metrics(timestamp DESC)")
        
        logger.info("✅ Created all indexes")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ All tables and indexes created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False


def verify_setup():
    """Verify that all tables were created successfully"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            **POSTGRES_CONFIG
        )
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
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
        
        logger.info("\n" + "="*70)
        logger.info("DATABASE VERIFICATION")
        logger.info("="*70)
        logger.info(f"Database: {DB_NAME}")
        logger.info(f"Host: {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
        logger.info(f"\nTables created: {len(tables)}")
        
        for table in expected_tables:
            if table in tables:
                logger.info(f"  ✅ {table}")
            else:
                logger.error(f"  ❌ {table} - MISSING!")
        
        # Get index count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE schemaname = 'public'
        """)
        index_count = cursor.fetchone()[0]
        logger.info(f"\nIndexes created: {index_count}")
        
        cursor.close()
        conn.close()
        
        logger.info("="*70 + "\n")
        
        return len(tables) == len(expected_tables)
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def main():
    """Main execution function"""
    logger.info("\n" + "="*70)
    logger.info("PostgreSQL Observability Database Initialization")
    logger.info("="*70 + "\n")
    
    # Step 1: Create database
    logger.info("Step 1: Creating database...")
    if not create_database():
        logger.error("Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 2: Create tables
    logger.info("\nStep 2: Creating tables and indexes...")
    if not create_tables():
        logger.error("Failed to create tables. Exiting.")
        sys.exit(1)
    
    # Step 3: Verify setup
    logger.info("\nStep 3: Verifying setup...")
    if not verify_setup():
        logger.error("Verification failed. Please check the logs.")
        sys.exit(1)
    
    logger.info("\n" + "="*70)
    logger.info("✅ PostgreSQL Observability Database Setup Complete!")
    logger.info("="*70)
    logger.info("\nNext steps:")
    logger.info("1. Update backend/app/config.py with PostgreSQL connection string")
    logger.info("2. Run migration script to transfer existing SQLite data")
    logger.info("3. Test the application with PostgreSQL")
    logger.info("\n")


if __name__ == "__main__":
    main()

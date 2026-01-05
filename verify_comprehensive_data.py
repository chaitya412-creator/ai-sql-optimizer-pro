"""
Verification Script for Comprehensive Test Data
Checks that all 10 issue types, 17 optimizations, and 20 issues are present
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models.database import Optimization, Connection
import json

# PostgreSQL Database configuration
DB_CONFIG = {
    "dbname": "mydb",
    "user": "admin",
    "password": "admin123",
    "host": "192.168.1.81",
    "port": 5432
}

DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"


def verify_data():
    """Verify the populated test data"""
    
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("\n" + "="*80)
        print("VERIFICATION REPORT")
        print("="*80 + "\n")
        
        # Get all optimizations with detected issues
        optimizations = session.query(Optimization).filter(
            Optimization.detected_issues.isnot(None)
        ).all()
        
        print(f"✓ Total optimizations with detected issues: {len(optimizations)}")
        
        if len(optimizations) != 17:
            print(f"  ⚠ WARNING: Expected 17 optimizations, found {len(optimizations)}")
        
        # Analyze issues
        issue_type_counts = {}
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        total_issues = 0
        
        print("\nOptimization Details:")
        print("-" * 80)
        
        for i, opt in enumerate(optimizations, 1):
            detected_issues = opt.detected_issues
            if detected_issues and isinstance(detected_issues, dict):
                issues = detected_issues.get("issues", [])
                issue_count = len(issues)
                total_issues += issue_count
                
                # Count by type and severity
                for issue in issues:
                    issue_type = issue.get("issue_type", "unknown")
                    severity = issue.get("severity", "unknown")
                    
                    issue_type_counts[issue_type] = issue_type_counts.get(issue_type, 0) + 1
                    if severity in severity_counts:
                        severity_counts[severity] += 1
                
                # Display optimization info
                issue_types = ", ".join(set(issue.get("issue_type", "unknown") for issue in issues))
                print(f"{i:2d}. ID {opt.id:3d}: {issue_count} issue(s) - {issue_types}")
        
        print("\n" + "="*80)
        print("ISSUE TYPE DISTRIBUTION")
        print("="*80 + "\n")
        
        expected_types = [
            "missing_index", "inefficient_index", "poor_join_strategy",
            "full_table_scan", "suboptimal_pattern", "stale_statistics",
            "wrong_cardinality", "orm_generated", "high_io_workload",
            "inefficient_reporting"
        ]
        
        print(f"Issue types found: {len(issue_type_counts)}/10")
        
        for issue_type in expected_types:
            count = issue_type_counts.get(issue_type, 0)
            status = "✓" if count > 0 else "✗"
            print(f"  {status} {issue_type.replace('_', ' ').title():35s}: {count:2d} issue(s)")
        
        # Check for unexpected types
        unexpected = set(issue_type_counts.keys()) - set(expected_types)
        if unexpected:
            print(f"\n  ⚠ Unexpected issue types found: {unexpected}")
        
        print("\n" + "="*80)
        print("SEVERITY DISTRIBUTION")
        print("="*80 + "\n")
        
        for severity, count in severity_counts.items():
            print(f"  • {severity.title():10s}: {count:2d} issues")
        
        print(f"\n✓ Total issues: {total_issues}")
        
        if total_issues != 20:
            print(f"  ⚠ WARNING: Expected 20 issues, found {total_issues}")
        
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80 + "\n")
        
        checks = []
        checks.append(("Optimizations", len(optimizations) == 17, f"{len(optimizations)}/17"))
        checks.append(("Issue Types", len(issue_type_counts) == 10, f"{len(issue_type_counts)}/10"))
        checks.append(("Total Issues", total_issues == 20, f"{total_issues}/20"))
        
        all_passed = all(check[1] for check in checks)
        
        for name, passed, value in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {name:20s}: {value}")
        
        if all_passed:
            print("\n✅ All verification checks passed!")
            print("\nYour dashboard should now display:")
            print("  • 17 optimizations with detected issues")
            print("  • All 10 issue types represented")
            print("  • 20 total issues across various severity levels")
        else:
            print("\n⚠ Some verification checks failed. Review the details above.")
        
        session.close()
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST DATA VERIFICATION")
    print("="*80)
    print(f"\nConnecting to: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    print("="*80)
    
    success = verify_data()
    
    if success:
        print("\n✅ Verification complete - Data is correct!")
    else:
        print("\n⚠ Verification complete - Please review warnings above.")

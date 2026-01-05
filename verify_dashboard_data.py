"""
Verify dashboard detection data
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Optimization
import json

DATABASE_URL = "sqlite:///backend/app/db/observability.db"

def verify_data():
    """Verify the populated data"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all optimizations with detected issues
        opts = session.query(Optimization).filter(
            Optimization.detected_issues.isnot(None)
        ).all()
        
        print(f"\n✓ Total optimizations with detected_issues: {len(opts)}")
        
        if not opts:
            print("❌ No optimizations with detected issues found!")
            return False
        
        # Analyze issue types
        issue_type_counts = {}
        total_issues = 0
        
        for opt in opts:
            if opt.detected_issues:
                if isinstance(opt.detected_issues, str):
                    issues_data = json.loads(opt.detected_issues)
                else:
                    issues_data = opt.detected_issues
                
                total_issues += issues_data.get("total_issues", 0)
                
                for issue in issues_data.get("issues", []):
                    issue_type = issue.get("issue_type")
                    if issue_type:
                        issue_type_counts[issue_type] = issue_type_counts.get(issue_type, 0) + 1
        
        print(f"✓ Total issues across all optimizations: {total_issues}")
        print(f"\n✓ Issue Type Distribution:")
        for issue_type, count in sorted(issue_type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {issue_type.replace('_', ' ').title()}: {count}")
        
        print(f"\n✓ Unique issue types: {len(issue_type_counts)}")
        
        # Sample one optimization
        sample = opts[0]
        if isinstance(sample.detected_issues, str):
            sample_issues = json.loads(sample.detected_issues)
        else:
            sample_issues = sample.detected_issues
        
        print(f"\n✓ Sample optimization structure:")
        print(f"  - ID: {sample.id}")
        print(f"  - Total issues: {sample_issues.get('total_issues')}")
        print(f"  - Critical: {sample_issues.get('critical_issues')}")
        print(f"  - High: {sample_issues.get('high_issues')}")
        print(f"  - Medium: {sample_issues.get('medium_issues')}")
        print(f"  - Low: {sample_issues.get('low_issues')}")
        
        if sample_issues.get("issues"):
            first_issue = sample_issues["issues"][0]
            print(f"\n✓ Sample issue:")
            print(f"  - Type: {first_issue.get('issue_type')}")
            print(f"  - Severity: {first_issue.get('severity')}")
            print(f"  - Title: {first_issue.get('title')}")
        
        print(f"\n{'='*70}")
        print("✅ DATA VERIFICATION PASSED")
        print(f"{'='*70}")
        print("\nThe dashboard should now display:")
        print(f"  - {len(opts)} optimizations with detected issues")
        print(f"  - {total_issues} total issues")
        print(f"  - {len(issue_type_counts)} different issue types")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("DASHBOARD DATA VERIFICATION")
    print("="*70)
    
    success = verify_data()
    
    if not success:
        print("\n❌ Verification failed")
        sys.exit(1)

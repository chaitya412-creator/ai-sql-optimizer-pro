"""
Quick Setup Script for Test Database
Runs the enhanced test database generator with minimal user interaction
"""

import subprocess
import sys

def main():
    print("\n" + "="*80)
    print("AI SQL OPTIMIZER PRO - QUICK TEST DATABASE SETUP")
    print("="*80)
    
    print("\nThis will create a comprehensive test database with:")
    print("  • 11 tables with ~1.36 million records")
    print("  • All 10 SQL optimization issue types")
    print("  • Problematic queries for testing")
    print("\nEstimated time: 5-10 minutes")
    
    response = input("\nProceed? (y/n): ")
    
    if response.lower() != 'y':
        print("\n❌ Setup cancelled")
        return
    
    print("\n🚀 Starting test database creation...")
    print("="*80)
    
    try:
        # Run the enhanced test database generator
        result = subprocess.run(
            [sys.executable, "create_test_database_enhanced.py"],
            check=True
        )
        
        if result.returncode == 0:
            print("\n" + "="*80)
            print("✅ TEST DATABASE SETUP COMPLETE!")
            print("="*80)
            print("\nYou can now:")
            print("  1. Connect to the database in the AI SQL Optimizer")
            print("  2. Test the problematic queries")
            print("  3. Verify issue detection")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

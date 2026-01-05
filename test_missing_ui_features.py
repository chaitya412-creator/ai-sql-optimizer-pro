"""
Test script for new UI features backend endpoints
Tests the 4 new API endpoints added to optimizer.py
"""
import asyncio
import httpx
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api"

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_test(test_name: str):
    """Print test header"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}TEST: {test_name}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")


def print_success(message: str):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"{YELLOW}ℹ {message}{RESET}")


async def test_explain_plan():
    """Test POST /api/optimizer/explain-plan endpoint"""
    print_test("Explain Execution Plan Endpoint")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Valid request with SQL query
        print_info("Test 1: Valid request with SQL query")
        try:
            response = await client.post(
                f"{API_BASE_URL}/optimizer/explain-plan",
                json={
                    "connection_id": 1,
                    "sql_query": "SELECT * FROM users WHERE id > 100"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Status: {response.status_code}")
                print_success(f"Response keys: {list(data.keys())}")
                
                if data.get("success"):
                    print_success("Explanation generated successfully")
                    print_info(f"Summary: {data.get('summary', 'N/A')[:100]}...")
                    print_info(f"Key operations: {data.get('key_operations', [])}")
                    print_info(f"Bottlenecks: {data.get('bottlenecks', [])}")
                else:
                    print_error(f"API returned success=False: {data.get('explanation')}")
            else:
                print_error(f"Status: {response.status_code}")
                print_error(f"Response: {response.text}")
        except Exception as e:
            print_error(f"Exception: {str(e)}")
        
        # Test 2: Invalid connection ID
        print_info("\nTest 2: Invalid connection ID")
        try:
            response = await client.post(
                f"{API_BASE_URL}/optimizer/explain-plan",
                json={
                    "connection_id": 99999,
                    "sql_query": "SELECT * FROM users"
                }
            )
            
            if response.status_code == 404:
                print_success("Correctly returned 404 for invalid connection")
            else:
                print_error(f"Expected 404, got {response.status_code}")
        except Exception as e:
            print_error(f"Exception: {str(e)}")
        
        # Test 3: Missing required fields
        print_info("\nTest 3: Missing required fields")
        try:
            response = await client.post(
                f"{API_BASE_URL}/optimizer/explain-plan",
                json={
                    "connection_id": 1
                    # Missing sql_query
                }
            )
            
            if response.status_code == 422:
                print_success("Correctly returned 422 for missing fields")
            else:
                print_error(f"Expected 422, got {response.status_code}")
        except Exception as e:
            print_error(f"Exception: {str(e)}")


async def test_generate_fixes():
    """Test POST /api/optimizer/generate-fixes endpoint"""
    print_test("Generate Fix Recommendations Endpoint")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # First, get an existing optimization ID
        print_info("Getting existing optimization ID...")
        try:
            response = await client.get(f"{API_BASE_URL}/optimizer/optimizations?limit=1")
            if response.status_code == 200:
                optimizations = response.json()
                if optimizations:
                    optimization_id = optimizations[0]["id"]
                    print_success(f"Found optimization ID: {optimization_id}")
                else:
                    print_error("No optimizations found. Please run an optimization first.")
                    return
            else:
                print_error(f"Failed to get optimizations: {response.status_code}")
                return
        except Exception as e:
            print_error(f"Exception getting optimizations: {str(e)}")
            return
        
        # Test 1: Valid request
        print_info("\nTest 1: Valid request with existing optimization")
        try:
            response = await client.post(
                f"{API_BASE_URL}/optimizer/generate-fixes",
                json={
                    "optimization_id": optimization_id,
                    "include_maintenance": True,
                    "include_indexes": True,
                    "include_rewrites": True,
                    "include_config": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Status: {response.status_code}")
                print_success(f"Response keys: {list(data.keys())}")
                
                if data.get("success"):
                    print_success("Fix recommendations generated successfully")
                    print_info(f"Total fixes: {data.get('total_fixes', 0)}")
                    print_info(f"High impact count: {data.get('high_impact_count', 0)}")
                    print_info(f"Index recommendations: {len(data.get('index_recommendations', []))}")
                    print_info(f"Maintenance tasks: {len(data.get('maintenance_tasks', []))}")
                    print_info(f"Query rewrites: {len(data.get('query_rewrites', []))}")
                    
                    # Show sample recommendations
                    if data.get('index_recommendations'):
                        print_info(f"\nSample index recommendation:")
                        rec = data['index_recommendations'][0]
                        print_info(f"  Type: {rec.get('fix_type')}")
                        print_info(f"  SQL: {rec.get('sql', 'N/A')[:100]}")
                        print_info(f"  Impact: {rec.get('estimated_impact')}")
                else:
                    print_error(f"API returned success=False")
            else:
                print_error(f"Status: {response.status_code}")
                print_error(f"Response: {response.text}")
        except Exception as e:
            print_error(f"Exception: {str(e)}")
        
        # Test 2: Invalid optimization ID
        print_info("\nTest 2: Invalid optimization ID")
        try:
            response = await client.post(
                f"{API_BASE_URL}/optimizer/generate-fixes",
                json={
                    "optimization_id": 99999,
                    "include_maintenance": True,
                    "include_indexes": True
                }
            )
            
            if response.status_code == 404:
                print_success("Correctly returned 404 for invalid optimization")
            else:
                print_error(f"Expected 404, got {response.status_code}")
        except Exception as e:
            print_error(f"Exception: {str(e)}")


async def test_apply_fix():
    """Test POST /api/optimizer/apply-fix endpoint"""
    print_test("Apply Fix Endpoint")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Get an existing optimization ID
        print_info("Getting existing optimization ID...")
        try:
            response = await client.get(f"{API_BASE_URL}/optimizer/optimizations?limit=1")
            if response.status_code == 200:
                optimizations = response.json()
                if optimizations:
                    optimization_id = optimizations[0]["id"]
                    print_success(f"Found optimization ID: {optimization_id}")
                else:
                    print_error("No optimizations found. Please run an optimization first.")
                    return
            else:
                print_error(f"Failed to get optimizations: {response.status_code}")
                return
        except Exception as e:
            print_error(f"Exception getting optimizations: {str(e)}")
            return
        
        # Test 1: Dry run mode (safe)
        print_info("\nTest 1: Apply fix in DRY RUN mode")
        try:
            response = await client.post(
                f"{API_BASE_URL}/optimizer/apply-fix",
                json={
                    "optimization_id": optimization_id,
                    "fix_type": "index_creation",
                    "fix_sql": "CREATE INDEX idx_test ON users(email);",
                    "dry_run": True,
                    "skip_safety_checks": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Status: {response.status_code}")
                print_success(f"Response keys: {list(data.keys())}")
                
                if data.get("success"):
                    print_success("Dry run completed successfully")
                    print_info(f"Fix type: {data.get('fix_type')}")
                    print_info(f"Status: {data.get('status')}")
                    print_info(f"Message: {data.get('message')}")
                    
                    if data.get('safety_checks'):
                        sc = data['safety_checks']
                        print_info(f"Safety checks passed: {sc.get('passed')}")
                        print_info(f"Checks performed: {sc.get('checks_performed', [])}")
                    
                    if data.get('rollback_sql'):
                        print_info(f"Rollback SQL: {data.get('rollback_sql')}")
                else:
                    print_error(f"Dry run failed: {data.get('message')}")
            else:
                print_error(f"Status: {response.status_code}")
                print_error(f"Response: {response.text}")
        except Exception as e:
            print_error(f"Exception: {str(e)}")
        
        # Test 2: Invalid SQL (should fail validation)
        print_info("\nTest 2: Invalid SQL (should fail validation)")
        try:
            response = await client.post(
                f"{API_BASE_URL}/optimizer/apply-fix",
                json={
                    "optimization_id": optimization_id,
                    "fix_type": "index_creation",
                    "fix_sql": "INVALID SQL STATEMENT",
                    "dry_run": True,
                    "skip_safety_checks": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("success"):
                    print_success("Correctly rejected invalid SQL")
                    print_info(f"Error message: {data.get('message')}")
                else:
                    print_error("Should have rejected invalid SQL")
            else:
                print_error(f"Unexpected status: {response.status_code}")
        except Exception as e:
            print_error(f"Exception: {str(e)}")
        
        # Test 3: Statistics update (ANALYZE)
        print_info("\nTest 3: Statistics update (ANALYZE) in dry run")
        try:
            response = await client.post(
                f"{API_BASE_URL}/optimizer/apply-fix",
                json={
                    "optimization_id": optimization_id,
                    "fix_type": "statistics_update",
                    "fix_sql": "ANALYZE users;",
                    "dry_run": True,
                    "skip_safety_checks": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print_success("ANALYZE command validated successfully")
                    print_info(f"Status: {data.get('status')}")
                else:
                    print_error(f"Failed: {data.get('message')}")
            else:
                print_error(f"Status: {response.status_code}")
        except Exception as e:
            print_error(f"Exception: {str(e)}")


async def test_validate_performance():
    """Test POST /api/optimizer/validate-performance endpoint"""
    print_test("Validate Performance Endpoint")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Get an existing optimization ID
        print_info("Getting existing optimization ID...")
        try:
            response = await client.get(f"{API_BASE_URL}/optimizer/optimizations?limit=1")
            if response.status_code == 200:
                optimizations = response.json()
                if optimizations:
                    optimization_id = optimizations[0]["id"]
                    print_success(f"Found optimization ID: {optimization_id}")
                else:
                    print_error("No optimizations found. Please run an optimization first.")
                    return
            else:
                print_error(f"Failed to get optimizations: {response.status_code}")
                return
        except Exception as e:
            print_error(f"Exception getting optimizations: {str(e)}")
            return
        
        # Test 1: Valid performance validation
        print_info("\nTest 1: Validate performance with 2 iterations")
        print_info("Note: This may take 30-60 seconds as it runs queries...")
        try:
            response = await client.post(
                f"{API_BASE_URL}/optimizer/validate-performance",
                json={
                    "optimization_id": optimization_id,
                    "run_original": True,
                    "run_optimized": True,
                    "iterations": 2
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Status: {response.status_code}")
                print_success(f"Response keys: {list(data.keys())}")
                
                if data.get("success"):
                    print_success("Performance validation completed")
                    print_info(f"Is faster: {data.get('is_faster')}")
                    print_info(f"Improvement: {data.get('improvement_pct')}%")
                    print_info(f"Improvement (ms): {data.get('improvement_ms')}")
                    
                    if data.get('original_metrics'):
                        om = data['original_metrics']
                        print_info(f"\nOriginal metrics:")
                        print_info(f"  Execution time: {om.get('execution_time_ms')}ms")
                        print_info(f"  Rows returned: {om.get('rows_returned')}")
                    
                    if data.get('optimized_metrics'):
                        opt_m = data['optimized_metrics']
                        print_info(f"\nOptimized metrics:")
                        print_info(f"  Execution time: {opt_m.get('execution_time_ms')}ms")
                        print_info(f"  Rows returned: {opt_m.get('rows_returned')}")
                    
                    if data.get('validation_notes'):
                        print_info(f"\nValidation notes:")
                        for note in data['validation_notes']:
                            print_info(f"  - {note}")
                else:
                    print_error(f"Validation failed")
            else:
                print_error(f"Status: {response.status_code}")
                print_error(f"Response: {response.text}")
        except Exception as e:
            print_error(f"Exception: {str(e)}")
        
        # Test 2: Invalid optimization ID
        print_info("\nTest 2: Invalid optimization ID")
        try:
            response = await client.post(
                f"{API_BASE_URL}/optimizer/validate-performance",
                json={
                    "optimization_id": 99999,
                    "iterations": 1
                }
            )
            
            if response.status_code == 404:
                print_success("Correctly returned 404 for invalid optimization")
            else:
                print_error(f"Expected 404, got {response.status_code}")
        except Exception as e:
            print_error(f"Exception: {str(e)}")


async def test_integration():
    """Test integration between endpoints"""
    print_test("Integration Testing")
    
    print_info("Testing complete workflow:")
    print_info("1. Get optimization")
    print_info("2. Explain plan")
    print_info("3. Generate fixes")
    print_info("4. Apply fix (dry run)")
    print_info("5. Validate performance")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 1: Get optimization
        try:
            response = await client.get(f"{API_BASE_URL}/optimizer/optimizations?limit=1")
            if response.status_code != 200 or not response.json():
                print_error("No optimizations available for integration test")
                return
            
            optimization = response.json()[0]
            opt_id = optimization["id"]
            conn_id = optimization["connection_id"]
            sql_query = optimization["original_sql"]
            
            print_success(f"Step 1: Got optimization {opt_id}")
            
            # Step 2: Explain plan
            response = await client.post(
                f"{API_BASE_URL}/optimizer/explain-plan",
                json={
                    "connection_id": conn_id,
                    "sql_query": sql_query
                }
            )
            
            if response.status_code == 200:
                print_success("Step 2: Explained execution plan")
            else:
                print_error(f"Step 2 failed: {response.status_code}")
            
            # Step 3: Generate fixes
            response = await client.post(
                f"{API_BASE_URL}/optimizer/generate-fixes",
                json={
                    "optimization_id": opt_id,
                    "include_maintenance": True,
                    "include_indexes": True
                }
            )
            
            if response.status_code == 200:
                fixes = response.json()
                print_success(f"Step 3: Generated {fixes.get('total_fixes', 0)} fixes")
                
                # Step 4: Apply first fix if available
                if fixes.get('index_recommendations'):
                    fix = fixes['index_recommendations'][0]
                    response = await client.post(
                        f"{API_BASE_URL}/optimizer/apply-fix",
                        json={
                            "optimization_id": opt_id,
                            "fix_type": fix['fix_type'],
                            "fix_sql": fix['sql'],
                            "dry_run": True
                        }
                    )
                    
                    if response.status_code == 200:
                        print_success("Step 4: Applied fix (dry run)")
                    else:
                        print_error(f"Step 4 failed: {response.status_code}")
                else:
                    print_info("Step 4: No fixes to apply")
            else:
                print_error(f"Step 3 failed: {response.status_code}")
            
            # Step 5: Validate performance
            print_info("Step 5: Validating performance (may take 30-60s)...")
            response = await client.post(
                f"{API_BASE_URL}/optimizer/validate-performance",
                json={
                    "optimization_id": opt_id,
                    "iterations": 1
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print_success(f"Step 5: Validated performance (improvement: {result.get('improvement_pct')}%)")
            else:
                print_error(f"Step 5 failed: {response.status_code}")
            
            print_success("\n✓ Integration test completed successfully!")
            
        except Exception as e:
            print_error(f"Integration test failed: {str(e)}")


async def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}TESTING NEW UI FEATURES BACKEND ENDPOINTS{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"{YELLOW}API Base URL: {API_BASE_URL}{RESET}")
    print(f"{YELLOW}Timestamp: {datetime.now().isoformat()}{RESET}")
    
    # Check if backend is running
    print_info("\nChecking if backend is running...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_BASE_URL}/../health")
            if response.status_code == 200:
                print_success("Backend is running!")
            else:
                print_error(f"Backend returned status {response.status_code}")
                return
    except Exception as e:
        print_error(f"Cannot connect to backend: {str(e)}")
        print_error("Please ensure the backend is running on http://localhost:8000")
        return
    
    # Run all tests
    await test_explain_plan()
    await test_generate_fixes()
    await test_apply_fix()
    await test_validate_performance()
    await test_integration()
    
    # Summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    print_success("All endpoint tests completed!")
    print_info("\nNext steps:")
    print_info("1. Review test results above")
    print_info("2. Fix any errors found")
    print_info("3. Proceed with frontend implementation")
    print(f"{BLUE}{'='*80}{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())

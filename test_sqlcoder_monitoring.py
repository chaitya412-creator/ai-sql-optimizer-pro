"""
Test script for SQLCoder monitoring integration
Tests the new endpoint for generating optimized queries using sqlcoder:latest
"""
import asyncio
import httpx
from loguru import logger

BASE_URL = "http://localhost:8000"

async def test_generate_optimized_query():
    """Test the new generate-optimized-query endpoint"""
    
    print("\n" + "="*80)
    print("Testing SQLCoder Monitoring Integration")
    print("="*80 + "\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Check if there are any discovered queries
        print("1. Fetching discovered queries...")
        try:
            response = await client.get(f"{BASE_URL}/api/monitoring/queries")
            
            if response.status_code == 200:
                queries = response.json()
                print(f"   ✓ Found {len(queries)} discovered queries")
                
                if len(queries) == 0:
                    print("\n   ⚠️  No queries found. Please run monitoring first to discover queries.")
                    print("   You can start monitoring from the UI or run:")
                    print("   - POST /api/monitoring/start")
                    print("   - POST /api/monitoring/trigger")
                    return
                
                # Use the first query for testing
                test_query = queries[0]
                query_id = test_query['id']
                
                print(f"\n   Using query ID: {query_id}")
                print(f"   SQL Preview: {test_query['sql_text'][:100]}...")
                print(f"   Avg Execution Time: {test_query['avg_execution_time']:.2f} ms")
                
            else:
                print(f"   ✗ Failed to fetch queries: {response.status_code}")
                print(f"   Response: {response.text}")
                return
                
        except Exception as e:
            print(f"   ✗ Error fetching queries: {e}")
            return
        
        # Step 2: Test the new endpoint
        print(f"\n2. Generating optimized query using sqlcoder:latest for query {query_id}...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/monitoring/queries/{query_id}/generate-optimized-query"
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"   ✓ Successfully generated optimized query!")
                print(f"\n   Success: {result.get('success')}")
                print(f"   Query ID: {result.get('query_id')}")
                
                # Display original SQL
                print(f"\n   📄 Original SQL:")
                print(f"   {'-'*76}")
                original_sql = result.get('original_sql', '')
                for line in original_sql.split('\n')[:5]:  # First 5 lines
                    print(f"   {line}")
                if len(original_sql.split('\n')) > 5:
                    print(f"   ... ({len(original_sql.split('\n')) - 5} more lines)")
                
                # Display optimized SQL
                print(f"\n   ✨ Optimized SQL (sqlcoder:latest):")
                print(f"   {'-'*76}")
                optimized_sql = result.get('optimized_sql', '')
                for line in optimized_sql.split('\n')[:5]:  # First 5 lines
                    print(f"   {line}")
                if len(optimized_sql.split('\n')) > 5:
                    print(f"   ... ({len(optimized_sql.split('\n')) - 5} more lines)")
                
                # Display explanation
                if result.get('explanation'):
                    print(f"\n   📝 Explanation:")
                    print(f"   {'-'*76}")
                    explanation = result.get('explanation', '')
                    for line in explanation.split('\n')[:3]:  # First 3 lines
                        print(f"   {line}")
                    if len(explanation.split('\n')) > 3:
                        print(f"   ... (more)")
                
                # Display estimated improvement
                if result.get('estimated_improvement'):
                    print(f"\n   📊 Estimated Improvement: {result.get('estimated_improvement')}% faster")
                
                # Display recommendations
                if result.get('recommendations'):
                    print(f"\n   💡 Recommendations:")
                    print(f"   {'-'*76}")
                    recommendations = result.get('recommendations', '')
                    for line in recommendations.split('\n')[:3]:  # First 3 lines
                        print(f"   {line}")
                    if len(recommendations.split('\n')) > 3:
                        print(f"   ... (more)")
                
                # Display query metrics
                if result.get('query_metrics'):
                    metrics = result['query_metrics']
                    print(f"\n   📈 Query Metrics:")
                    print(f"   {'-'*76}")
                    print(f"   Avg Execution Time: {metrics.get('avg_execution_time', 0):.2f} ms")
                    print(f"   Total Execution Time: {metrics.get('total_execution_time', 0):.2f} ms")
                    print(f"   Calls: {metrics.get('calls', 0)}")
                
                # Display connection info
                if result.get('connection'):
                    conn = result['connection']
                    print(f"\n   🔌 Connection: {conn.get('name')} ({conn.get('engine')})")
                
                print(f"\n   ✅ Test PASSED - Optimized query generated successfully!")
                
            else:
                print(f"   ✗ Failed to generate optimized query: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ✗ Error generating optimized query: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 3: Test with invalid query ID
        print(f"\n3. Testing error handling with invalid query ID...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/monitoring/queries/99999/generate-optimized-query"
            )
            
            if response.status_code == 404:
                print(f"   ✓ Correctly returned 404 for non-existent query")
            else:
                print(f"   ⚠️  Expected 404, got {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ Error testing invalid query ID: {e}")
    
    print("\n" + "="*80)
    print("Test Complete!")
    print("="*80 + "\n")


async def check_ollama_health():
    """Check if Ollama is running and sqlcoder model is available"""
    
    print("\n" + "="*80)
    print("Checking Ollama Health")
    print("="*80 + "\n")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Check Ollama API
            response = await client.get("http://localhost:11434/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = [model.get("name", "") for model in data.get("models", [])]
                
                print(f"✓ Ollama is running")
                print(f"✓ Found {len(models)} models")
                
                # Check for sqlcoder
                sqlcoder_found = any("sqlcoder" in model for model in models)
                if sqlcoder_found:
                    print(f"✓ sqlcoder model is available")
                else:
                    print(f"✗ sqlcoder model NOT found")
                    print(f"\n  To install sqlcoder:latest, run:")
                    print(f"  ollama pull sqlcoder:latest")
                
                # Check for olmo-3
                olmo_found = any("olmo-3" in model for model in models)
                if olmo_found:
                    print(f"✓ olmo-3 model is available")
                else:
                    print(f"⚠️  olmo-3 model NOT found (used for issue-based corrections)")
                
                print(f"\nAvailable models:")
                for model in models[:10]:  # Show first 10
                    print(f"  - {model}")
                if len(models) > 10:
                    print(f"  ... and {len(models) - 10} more")
                
            else:
                print(f"✗ Ollama API returned status {response.status_code}")
                
        except Exception as e:
            print(f"✗ Ollama is not accessible: {e}")
            print(f"\n  Make sure Ollama is running:")
            print(f"  - Check if Ollama service is started")
            print(f"  - Default URL: http://localhost:11434")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    # Run health check first
    asyncio.run(check_ollama_health())
    
    # Then run the test
    asyncio.run(test_generate_optimized_query())

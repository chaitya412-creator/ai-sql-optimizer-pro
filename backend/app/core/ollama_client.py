"""
Ollama LLM Client for SQL Optimization
Enhanced with sqlcoder:latest model for intelligent SQL optimization
"""
import httpx
import json
from typing import Dict, Any, Optional, List
from loguru import logger
from app.config import settings


class OllamaClient:
    """Client for interacting with Ollama LLM with sqlcoder:latest"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        # Use the configured Ollama model from settings (ensure it's a supported model)
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        # Ensure all calls use the configured model (avoid hard-coded sqlcoder:latest)
        self.request_model = self.model
    
    async def check_health(self) -> Dict[str, Any]:
        """Check if Ollama is accessible and model is available"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if Ollama is running
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = [model.get("name", "") for model in data.get("models", [])]
                    
                    model_available = any(self.model in model for model in models)
                    
                    return {
                        "status": "healthy" if model_available else "model_not_found",
                        "url": self.base_url,
                        "model": self.model,
                        "model_available": model_available,
                        "available_models": models
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "url": self.base_url,
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                "status": "unreachable",
                "url": self.base_url,
                "error": str(e)
            }
    
    async def optimize_query(
        self,
        sql_query: str,
        schema_ddl: str,
        execution_plan: Optional[Dict[str, Any]],
        database_type: str,
        detected_issues: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize SQL query using Ollama sqlcoder:latest model
        
        Args:
            sql_query: The problematic SQL query
            schema_ddl: DDL statements for relevant tables
            execution_plan: Execution plan from EXPLAIN ANALYZE
            database_type: Type of database (postgresql, mysql, etc.)
            detected_issues: Pre-detected issues from plan_analyzer
        
        Returns:
            Dict containing optimized_sql, explanation, and recommendations
        """
        try:
            # Use the configured model for optimization
            model_to_use = self.request_model
            
            # Construct the enhanced prompt with detected issues
            prompt = self._build_sqlcoder_optimization_prompt(
                sql_query, schema_ddl, execution_plan, database_type, detected_issues
            )
            
            logger.info(f"Using model: {model_to_use} for SQL optimization")
            
            # Call Ollama API with sqlcoder
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_to_use,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Low temperature for deterministic SQL
                            "top_p": 0.9,
                            "top_k": 40,
                            "num_predict": 3000,  # Increased for detailed explanations
                            "stop": ["</SQL>", "---END---"]
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get("response", "")
                    
                    # Parse the LLM response
                    parsed = self._parse_sqlcoder_response(llm_response)
                    
                    # Check if parsing was successful
                    if not parsed.get("success", True):
                        # Parsing failed - return error
                        logger.error(f"LLM response parsing failed")
                        return {
                            "success": False,
                            "error": parsed.get("error", "Could not parse LLM response"),
                            "raw_response": llm_response,
                            "parsing_method": parsed.get("parsing_method", "unknown")
                        }
                    
                    return {
                        "success": True,
                        "optimized_sql": parsed["optimized_sql"],
                        "explanation": parsed["explanation"],
                        "recommendations": parsed["recommendations"],
                        "estimated_improvement": parsed.get("estimated_improvement"),
                        "raw_response": llm_response
                    }
                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Ollama API returned status {response.status_code}"
                    }
        
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def explain_plan_natural_language(
        self,
        execution_plan: Dict[str, Any],
        sql_query: str,
        database_type: str
    ) -> Dict[str, Any]:
        """
        Explain execution plan in natural language using Ollama
        
        Args:
            execution_plan: The execution plan to explain
            sql_query: The SQL query
            database_type: Database type
        
        Returns:
            Dict with natural language explanation
        """
        try:
            prompt = self._build_plan_explanation_prompt(
                execution_plan, sql_query, database_type
            )
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.request_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 1500
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    explanation = result.get("response", "")
                    
                    return {
                        "success": True,
                        "explanation": explanation,
                        "summary": self._extract_summary(explanation)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API returned status {response.status_code}"
                    }
        
        except Exception as e:
            logger.error(f"Plan explanation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_fix_recommendations(
        self,
        detected_issues: List[Dict[str, Any]],
        schema_ddl: str,
        database_type: str
    ) -> Dict[str, Any]:
        """
        Generate actionable fix recommendations for detected issues
        
        Args:
            detected_issues: List of detected performance issues
            schema_ddl: Database schema
            database_type: Database type
        
        Returns:
            Dict with categorized recommendations
        """
        try:
            prompt = self._build_fix_recommendations_prompt(
                detected_issues, schema_ddl, database_type
            )
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.request_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 2000
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    recommendations = result.get("response", "")
                    
                    parsed = self._parse_fix_recommendations(recommendations)
                    
                    return {
                        "success": True,
                        "index_recommendations": parsed["indexes"],
                        "query_rewrites": parsed["rewrites"],
                        "configuration_changes": parsed["config"],
                        "maintenance_tasks": parsed["maintenance"]
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API returned status {response.status_code}"
                    }
        
        except Exception as e:
            logger.error(f"Fix recommendation generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_sqlcoder_optimization_prompt(
        self,
        sql_query: str,
        schema_ddl: str,
        execution_plan: Optional[Dict[str, Any]],
        database_type: str,
        detected_issues: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build enhanced optimization prompt for sqlcoder:latest"""
        
        # Format execution plan
        plan_section = ""
        if execution_plan:
            plan_section = f"""
### EXECUTION PLAN ANALYSIS:
```json
{json.dumps(execution_plan, indent=2)}
```

**Critical Performance Indicators:**
- Sequential Scans (Seq Scan) → Missing indexes
- Nested Loop joins on large datasets → Consider Hash/Merge joins
- High cost operations → Optimization targets
- Cardinality misestimates → Statistics issues
- Bitmap Heap Scans → Low index selectivity
"""
        
        # Format detected issues
        issues_section = ""
        if detected_issues and detected_issues.get("issues"):
            issues_list = []
            for issue in detected_issues["issues"][:10]:  # Top 10 issues
                issues_list.append(
                    f"- [{issue['severity'].upper()}] {issue['title']}: {issue['description']}"
                )
            
            issues_section = f"""
### PRE-DETECTED PERFORMANCE ISSUES:
{chr(10).join(issues_list)}

**Issue Summary:**
- Total Issues: {detected_issues.get('total_issues', 0)}
- Critical: {detected_issues.get('critical_issues', 0)}
- High: {detected_issues.get('high_issues', 0)}
- Medium: {detected_issues.get('medium_issues', 0)}
"""
        
        prompt = f"""You are SQLCoder, an expert SQL optimization AI for {database_type.upper()} databases.

### YOUR TASK:
Analyze the query, schema, execution plan, and detected issues to produce an optimized SQL query with comprehensive recommendations.

### DATABASE SCHEMA:
```sql
{schema_ddl}
```

### ORIGINAL QUERY:
```sql
{sql_query}
```
{plan_section}
{issues_section}

### OPTIMIZATION REQUIREMENTS:
1. **Address ALL detected issues** in your optimization
2. **Preserve query semantics** - results must match original
3. **Provide executable SQL** - no placeholders or pseudo-code
4. **Focus on high-impact changes** - indexes, joins, filters
5. **Consider database-specific features** - CTEs, window functions, partitioning
6. **Estimate performance savings** - provide projected CPU, I/O, and latency savings

### OUTPUT FORMAT:
Provide your response in this EXACT format:

--- OPTIMIZED SQL ---
<SQL>
[Your complete, executable optimized SQL query here]
</SQL>

--- EXPLANATION ---
**Issues Identified:**
1. [Issue 1 from plan/detection]
2. [Issue 2 from plan/detection]
...

**Optimization Strategy:**
1. [Change 1 and why it helps]
2. [Change 2 and why it helps]
...

**Expected Performance Impact:**
- Estimated Latency Savings: [X ms or %]
- Estimated CPU Savings: [X% or description]
- Estimated I/O Savings: [X% or description]
- Overall Improvement: [X%] faster

--- RECOMMENDATIONS ---
**Immediate Actions (Apply Now):**
```sql
-- Index creation
CREATE INDEX idx_name ON table(column);

-- Statistics update
ANALYZE table_name;
```

**Query Pattern Improvements:**
- [Recommendation 1]
- [Recommendation 2]

**Configuration Tuning:**
- [Config change 1]
- [Config change 2]

**Long-term Optimizations:**
- [Strategic recommendation 1]
- [Strategic recommendation 2]

---END---

Now provide your optimization:"""
        
        return prompt
    
    def _build_plan_explanation_prompt(
        self,
        execution_plan: Dict[str, Any],
        sql_query: str,
        database_type: str
    ) -> str:
        """Build prompt for natural language plan explanation"""
        
        prompt = f"""You are a database performance expert explaining an execution plan to a developer.

### SQL QUERY:
```sql
{sql_query}
```

### EXECUTION PLAN:
```json
{json.dumps(execution_plan, indent=2)}
```

### YOUR TASK:
Explain this {database_type.upper()} execution plan in clear, non-technical language.

**Focus on:**
1. What the database is doing step-by-step
2. Why certain operations are expensive
3. What data is being accessed and how
4. Where bottlenecks exist
5. Simple analogies to explain complex operations

**Format:**
- Use simple language (avoid jargon where possible)
- Break down into logical steps
- Highlight performance concerns
- Suggest what to look for

Provide your explanation:"""
        
        return prompt
    
    def _build_fix_recommendations_prompt(
        self,
        detected_issues: List[Dict[str, Any]],
        schema_ddl: str,
        database_type: str
    ) -> str:
        """Build prompt for generating fix recommendations"""
        
        issues_text = "\n".join([
            f"{i+1}. [{issue['severity'].upper()}] {issue['title']}\n"
            f"   Description: {issue['description']}\n"
            f"   Affected: {', '.join(issue.get('affected_objects', []))}"
            for i, issue in enumerate(detected_issues[:15])
        ])
        
        prompt = f"""You are a database optimization expert for {database_type.upper()}.

### DETECTED PERFORMANCE ISSUES:
{issues_text}

### DATABASE SCHEMA:
```sql
{schema_ddl}
```

### YOUR TASK:
Generate specific, actionable fix recommendations categorized by type.

**For each recommendation, provide an estimated impact on:**
- **CPU Savings** (e.g., 20%, 50%, 80%)
- **I/O Savings** (e.g., 30%, 60%, 90%)
- **Latency Reduction** (e.g., 10ms, 100ms, 1s)

**Provide:**
1. **Index Recommendations** - Exact CREATE INDEX statements
2. **Query Rewrites** - Specific SQL improvements
3. **Configuration Changes** - Database settings to adjust
4. **Maintenance Tasks** - ANALYZE, VACUUM, etc.

**Format:**
--- INDEXES ---
1. Create index on users(email)
```sql
CREATE INDEX idx_users_email ON users(email);
```
CPU Savings: 40%
I/O Savings: 80%
Latency Savings: 50ms

--- REWRITES ---
1. Replace NOT IN with NOT EXISTS
```sql
SELECT * FROM users WHERE NOT EXISTS (SELECT 1 FROM orders WHERE orders.user_id = users.id);
```
CPU Savings: 20%
I/O Savings: 10%
Latency Savings: 15ms

--- CONFIGURATION ---
1. Increase work_mem
```sql
SET work_mem = '256MB';
```
CPU Savings: 15%
I/O Savings: 50%
Latency Savings: 200ms

--- MAINTENANCE ---
1. Analyze users table
```sql
ANALYZE users;
```
CPU Savings: 10%
I/O Savings: 5%
Latency Savings: 5ms

Provide your recommendations:"""
        
        return prompt
    
    def _parse_sqlcoder_response(self, response: str) -> Dict[str, Any]:
        """
        Parse sqlcoder response into structured components with robust fallback strategies
        
        Parsing strategies (in order of priority):
        1. XML-style tags (<SQL>...</SQL>)
        2. Section markers (--- OPTIMIZED SQL ---)
        3. Markdown code blocks (```sql...```)
        4. Heuristic extraction (find SQL statements)
        5. Best effort extraction (extract anything that looks like SQL)
        6. Return entire response as fallback
        """
        import re
        
        optimized_sql = ""
        explanation = ""
        recommendations = ""
        estimated_improvement = None
        parsing_method = "unknown"
        
        logger.debug(f"Parsing LLM response (length: {len(response)} chars)")
        logger.debug(f"Response preview: {response[:200]}...")
        
        # Strategy 1: Extract SQL from <SQL> tags
        optimized_sql = self._extract_sql_from_tags(response)
        if optimized_sql:
            parsing_method = "xml_tags"
        
        # Strategy 2: Extract from section markers
        if not optimized_sql:
            logger.debug("XML tags not found, trying section markers")
            optimized_sql = self._extract_sql_from_sections(response)
            if optimized_sql:
                parsing_method = "section_markers"
        
        # Strategy 3: Extract from markdown code blocks
        if not optimized_sql:
            logger.debug("Section markers not found, trying code blocks")
            optimized_sql = self._extract_sql_from_code_blocks(response)
            if optimized_sql:
                parsing_method = "code_blocks"
        
        # Strategy 4: Heuristic extraction (find SQL statements)
        if not optimized_sql:
            logger.debug("Code blocks not found, trying heuristic extraction")
            optimized_sql = self._extract_sql_heuristic(response)
            if optimized_sql:
                parsing_method = "heuristic"
        
        # Strategy 5: Best effort extraction (more aggressive)
        if not optimized_sql:
            logger.debug("Heuristic failed, trying best effort extraction")
            optimized_sql = self._extract_sql_best_effort(response)
            if optimized_sql:
                parsing_method = "best_effort"
        
        # Strategy 6: Last resort - use entire response if it looks like SQL
        if not optimized_sql:
            logger.warning("All parsing strategies failed, checking if entire response is SQL")
            cleaned_response = self._clean_sql(response)
            if self._validate_sql_basic(cleaned_response):
                optimized_sql = cleaned_response
                parsing_method = "full_response"
            else:
                # Absolute fallback - extract any SQL-like content or return original query
                logger.error("Could not extract valid SQL from LLM response")
                # Try to find ANY SQL keyword and extract surrounding context
                import re
                sql_pattern = r'(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE)\s+.*?(?:;|\n\n|\Z)'
                matches = re.findall(sql_pattern, response, re.DOTALL | re.IGNORECASE)
                if matches:
                    # Use the longest match
                    optimized_sql = max(matches, key=len).strip()
                    parsing_method = "emergency_extraction"
                    logger.info(f"Emergency extraction found SQL (length: {len(optimized_sql)})")
                else:
                    # Last resort: return the entire response as-is
                    optimized_sql = response.strip()
                    parsing_method = "raw_response"
                    logger.warning("Returning raw LLM response as SQL")
        
        # Clean up the extracted SQL
        optimized_sql = self._clean_sql(optimized_sql)
        
        # Validate basic SQL syntax
        is_valid = self._validate_sql_basic(optimized_sql)
        
        # If validation fails, return error instead of invalid SQL
        if not is_valid:
            logger.error(f"LLM response parsing failed - could not extract valid SQL")
            logger.error(f"Parsing method attempted: {parsing_method}")
            logger.error(f"Extracted content (first 200 chars): {optimized_sql[:200]}")
            logger.error(f"Raw LLM response (first 500 chars): {response[:500]}")
            
            return {
                "optimized_sql": "",
                "explanation": "",
                "recommendations": "",
                "estimated_improvement": None,
                "parsing_method": parsing_method,
                "is_valid_sql": False,
                "success": False,
                "error": "Could not parse LLM response into valid SQL. The LLM may not have provided a properly formatted optimization.",
                "raw_response": response
            }
        
        # Extract explanation and recommendations with flexible parsing
        explanation, recommendations = self._extract_explanation_and_recommendations(response)
        
        # Extract estimated improvement and savings
        estimated_improvement = None
        cpu_savings = None
        io_savings = None
        latency_savings = None
        
        if explanation:
            # Overall improvement
            match = re.search(r'Overall Improvement:\s*(\d+)%?', explanation, re.IGNORECASE)
            if not match:
                match = re.search(r'(\d+)%?\s*faster', explanation, re.IGNORECASE)
            if match:
                estimated_improvement = int(match.group(1))
            
            # CPU Savings
            match = re.search(r'Estimated CPU Savings:\s*(.*?)(?:\n|$)', explanation, re.IGNORECASE)
            if match:
                cpu_savings = match.group(1).strip()
            
            # I/O Savings
            match = re.search(r'Estimated I/O Savings:\s*(.*?)(?:\n|$)', explanation, re.IGNORECASE)
            if match:
                io_savings = match.group(1).strip()
                
            # Latency Savings
            match = re.search(r'Estimated Latency Savings:\s*(.*?)(?:\n|$)', explanation, re.IGNORECASE)
            if match:
                latency_savings = match.group(1).strip()
        
        # Log parsing result
        logger.info(f"Parsing complete - Method: {parsing_method}, Valid: {is_valid}, SQL length: {len(optimized_sql)}")
        
        return {
            "optimized_sql": optimized_sql,
            "explanation": explanation or "No explanation provided",
            "recommendations": recommendations or "No specific recommendations provided",
            "estimated_improvement": estimated_improvement,
            "cpu_savings": cpu_savings,
            "io_savings": io_savings,
            "latency_savings": latency_savings,
            "parsing_method": parsing_method,
            "is_valid_sql": is_valid,
            "success": True,
            "raw_response": response  # Include raw response for debugging
        }
    
    def _extract_sql_from_tags(self, response: str) -> str:
        """Extract SQL from <SQL>...</SQL> tags"""
        import re
        
        # Try to find SQL tags
        match = re.search(r'<SQL>\s*(.*?)\s*</SQL>', response, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1).strip()
            logger.debug(f"Found SQL in XML tags (length: {len(sql)})")
            return sql
        
        return ""
    
    def _extract_sql_from_sections(self, response: str) -> str:
        """Extract SQL from section markers"""
        # Split by markers
        parts = response.split("--- OPTIMIZED SQL ---")
        if len(parts) > 1:
            remaining = parts[1]
            
            # Find the end of SQL section (next marker or end)
            sql_parts = remaining.split("--- EXPLANATION ---")
            if len(sql_parts) > 1:
                sql = sql_parts[0].strip()
            else:
                # Try other markers
                for marker in ["--- RECOMMENDATIONS ---", "---END---", "---"]:
                    if marker in remaining:
                        sql = remaining.split(marker)[0].strip()
                        break
                else:
                    sql = remaining.strip()
            
            # Remove any remaining tags
            sql = sql.replace("<SQL>", "").replace("</SQL>", "").strip()
            
            if sql:
                logger.debug(f"Found SQL in section markers (length: {len(sql)})")
                return sql
        
        return ""
    
    def _extract_sql_from_code_blocks(self, response: str) -> str:
        """Extract SQL from markdown code blocks"""
        import re
        
        # Try to find SQL code blocks
        patterns = [
            r'```sql\s*(.*?)\s*```',  # ```sql ... ```
            r'```\s*(SELECT|WITH|UPDATE|DELETE|INSERT).*?```',  # ``` SELECT ... ```
            r'`(SELECT|WITH|UPDATE|DELETE|INSERT).*?`',  # `SELECT ... `
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip() if match.lastindex else match.group(0).strip()
                # Remove backticks
                sql = sql.replace('```sql', '').replace('```', '').replace('`', '').strip()
                if sql:
                    logger.debug(f"Found SQL in code blocks (length: {len(sql)})")
                    return sql
        
        return ""
    
    def _extract_sql_heuristic(self, response: str) -> str:
        """Extract SQL using heuristic patterns"""
        import re
        
        # Look for SQL statements (SELECT, WITH, UPDATE, DELETE, INSERT)
        sql_keywords = ['SELECT', 'WITH', 'UPDATE', 'DELETE', 'INSERT']
        
        for keyword in sql_keywords:
            # Find keyword at start of line or after whitespace
            pattern = rf'(?:^|\n)\s*({keyword}\b.*?)(?:\n\n|---|\Z)'
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                # Check if it looks like SQL (has common SQL keywords)
                if any(kw in sql.upper() for kw in ['FROM', 'WHERE', 'JOIN', 'SET', 'INTO', 'VALUES']):
                    logger.debug(f"Found SQL using heuristic (keyword: {keyword}, length: {len(sql)})")
                    return sql
        
        return ""
    
    def _extract_sql_best_effort(self, response: str) -> str:
        """
        Best effort SQL extraction - more aggressive approach
        Tries to find anything that looks remotely like SQL
        """
        import re
        
        # Strategy 1: Find the longest continuous block that contains SQL keywords
        sql_keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY', 
                       'INSERT', 'UPDATE', 'DELETE', 'WITH', 'AS', 'ON', 'AND', 'OR']
        
        lines = response.split('\n')
        best_block = ""
        current_block = []
        sql_keyword_count = 0
        
        for line in lines:
            line_upper = line.upper()
            # Check if line contains SQL keywords
            line_keywords = sum(1 for kw in sql_keywords if kw in line_upper)
            
            if line_keywords > 0 or (current_block and not line.strip().startswith('---')):
                current_block.append(line)
                sql_keyword_count += line_keywords
            else:
                # End of potential SQL block
                if sql_keyword_count >= 3:  # At least 3 SQL keywords
                    block_text = '\n'.join(current_block)
                    if len(block_text) > len(best_block):
                        best_block = block_text
                current_block = []
                sql_keyword_count = 0
        
        # Check final block
        if sql_keyword_count >= 3:
            block_text = '\n'.join(current_block)
            if len(block_text) > len(best_block):
                best_block = block_text
        
        if best_block:
            logger.debug(f"Found SQL using best effort (length: {len(best_block)})")
            return best_block.strip()
        
        # Strategy 2: Find any line starting with SELECT, WITH, etc.
        for keyword in ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE']:
            pattern = rf'({keyword}\b.*?)(?:\n\s*\n|\Z)'
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                if len(sql) > 20:  # At least 20 characters
                    logger.debug(f"Found SQL using best effort keyword search (keyword: {keyword})")
                    return sql
        
        return ""
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and format extracted SQL"""
        if not sql:
            return ""
        
        # Remove markdown code blocks
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        # Remove backticks
        sql = sql.replace("`", "")
        
        # Remove XML tags if any remain
        sql = sql.replace("<SQL>", "").replace("</SQL>", "")
        
        # Remove leading/trailing whitespace from each line
        lines = [line.rstrip() for line in sql.split('\n')]
        sql = '\n'.join(lines)
        
        # Remove excessive blank lines (more than 2 consecutive)
        import re
        sql = re.sub(r'\n{3,}', '\n\n', sql)
        
        return sql.strip()
    
    def _validate_sql_basic(self, sql: str) -> bool:
        """
        Basic SQL validation - check if it looks like valid SQL
        Returns False if:
        - Too short
        - Only contains comments
        - Contains error messages
        - Doesn't have SQL keywords
        """
        if not sql or len(sql) < 10:
            logger.debug("SQL validation failed: too short or empty")
            return False
        
        # Remove comments and whitespace to check actual content
        lines = sql.split('\n')
        non_comment_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('--')]
        
        # If only comments remain, it's not valid SQL
        if not non_comment_lines:
            logger.debug("SQL validation failed: only comments, no actual SQL")
            return False
        
        # Join non-comment lines to check for SQL keywords
        actual_sql = ' '.join(non_comment_lines)
        sql_upper = actual_sql.upper()
        
        # Check for SQL keywords
        sql_keywords = ['SELECT', 'WITH', 'UPDATE', 'DELETE', 'INSERT', 'CREATE', 'ALTER', 'DROP']
        
        # Must start with a SQL keyword
        has_sql_keyword = any(sql_upper.strip().startswith(kw) for kw in sql_keywords)
        if not has_sql_keyword:
            logger.debug(f"SQL validation failed: doesn't start with SQL keyword. Starts with: {sql_upper[:50]}")
            return False
        
        # Check for error indicators in the actual SQL (not just comments)
        error_indicators = [
            'optimization failed',
            'could not parse',
            'error:',
            'failed to',
            'unable to',
            'cannot parse',
            'parsing error'
        ]
        
        sql_lower = actual_sql.lower()
        for indicator in error_indicators:
            if indicator in sql_lower:
                logger.debug(f"SQL validation failed: contains error indicator '{indicator}'")
                return False
        
        # Check if it's just a comment about failure
        if sql.strip().startswith('--') and any(indicator in sql.lower() for indicator in error_indicators):
            logger.debug("SQL validation failed: starts with error comment")
            return False
        
        # Must have some SQL structure keywords (FROM, WHERE, SET, VALUES, etc.)
        structure_keywords = ['FROM', 'WHERE', 'JOIN', 'SET', 'VALUES', 'INTO', 'GROUP BY', 'ORDER BY']
        has_structure = any(kw in sql_upper for kw in structure_keywords)
        
        if not has_structure:
            logger.debug("SQL validation failed: missing SQL structure keywords")
            return False
        
        logger.debug("SQL validation passed")
        return True
    
    def _extract_explanation_and_recommendations(self, response: str) -> tuple:
        """Extract explanation and recommendations with flexible parsing"""
        explanation = ""
        recommendations = ""
        
        # Try to find explanation section
        if "--- EXPLANATION ---" in response:
            parts = response.split("--- EXPLANATION ---")
            if len(parts) > 1:
                remaining = parts[1]
                
                # Find recommendations section
                if "--- RECOMMENDATIONS ---" in remaining:
                    exp_parts = remaining.split("--- RECOMMENDATIONS ---")
                    explanation = exp_parts[0].strip()
                    recommendations = exp_parts[1].split("---END---")[0].strip()
                else:
                    # No recommendations section, take everything after explanation
                    explanation = remaining.split("---END---")[0].strip()
        
        # Alternative: Look for common explanation patterns
        if not explanation:
            import re
            
            # Look for "Issues Identified:" or "Optimization Strategy:"
            patterns = [
                r'(?:Issues Identified|Optimization Strategy|Expected Performance Impact):(.*?)(?:---|$)',
                r'(?:Explanation|Analysis):\s*(.*?)(?:---|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    explanation = match.group(1).strip()
                    break
        
        # Alternative: Look for recommendations patterns
        if not recommendations:
            import re
            
            patterns = [
                r'(?:Immediate Actions|Recommendations|Query Pattern Improvements):(.*?)(?:---|$)',
                r'(?:Configuration Tuning|Long-term Optimizations):(.*?)(?:---|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    recommendations = match.group(1).strip()
                    break
        
        return explanation, recommendations
    
    def _parse_fix_recommendations(self, response: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse fix recommendations into categories with metadata"""
        
        result = {
            "indexes": [],
            "rewrites": [],
            "config": [],
            "maintenance": []
        }
        
        # Helper to extract savings from a block of text
        def extract_savings(text):
            savings = {}
            cpu = re.search(r'CPU Savings:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
            io = re.search(r'I/O Savings:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
            latency = re.search(r'Latency Savings:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
            
            if cpu: savings["estimated_cpu_savings"] = cpu.group(1).strip()
            if io: savings["estimated_io_savings"] = io.group(1).strip()
            if latency: savings["estimated_latency_savings"] = latency.group(1).strip()
            return savings

        # Extract indexes
        if "--- INDEXES ---" in response:
            idx_section = response.split("--- INDEXES ---")[1].split("---")[0]
            # Split by individual recommendations (usually starting with - or 1.)
            recs = re.split(r'\n(?=\d+\.|\-)', idx_section)
            for rec in recs:
                if "CREATE INDEX" in rec.upper():
                    sql_match = re.search(r'CREATE\s+INDEX.*?;', rec, re.IGNORECASE | re.DOTALL)
                    if sql_match:
                        sql = sql_match.group(0).strip()
                        desc_match = re.search(r'(?:^|\n)(?:-|\d+\.)\s*(.*?)(?:\n|```|$)', rec, re.DOTALL)
                        desc = desc_match.group(1).strip() if desc_match else "Create missing index"
                        
                        fix = {
                            "fix_type": "index_creation",
                            "sql": sql,
                            "description": desc,
                            "estimated_impact": "high" if "high" in rec.lower() else "medium",
                            "affected_objects": [], # Could extract from SQL
                            "safety_level": "safe"
                        }
                        fix.update(extract_savings(rec))
                        result["indexes"].append(fix)
        
        # Extract rewrites
        if "--- REWRITES ---" in response:
            rewrite_section = response.split("--- REWRITES ---")[1].split("---")[0]
            recs = re.split(r'\n(?=\d+\.|\-)', rewrite_section)
            for rec in recs:
                if "SELECT" in rec.upper() or "WITH" in rec.upper():
                    sql_match = re.search(r'```sql\s*(.*?)\s*```', rec, re.IGNORECASE | re.DOTALL)
                    if sql_match:
                        sql = sql_match.group(1).strip()
                        desc_match = re.search(r'(?:^|\n)(?:-|\d+\.)\s*(.*?)(?:\n|```|$)', rec, re.DOTALL)
                        desc = desc_match.group(1).strip() if desc_match else "Rewrite query for better performance"
                        
                        fix = {
                            "fix_type": "query_rewrite",
                            "sql": sql,
                            "description": desc,
                            "estimated_impact": "medium",
                            "affected_objects": [],
                            "safety_level": "safe"
                        }
                        fix.update(extract_savings(rec))
                        result["rewrites"].append(fix)
        
        # Extract configuration
        if "--- CONFIGURATION ---" in response:
            config_section = response.split("--- CONFIGURATION ---")[1].split("---")[0]
            recs = re.split(r'\n(?=\d+\.|\-)', config_section)
            for rec in recs:
                if "SET" in rec.upper() or "ALTER SYSTEM" in rec.upper():
                    sql_match = re.search(r'(?:SET|ALTER SYSTEM).*?;', rec, re.IGNORECASE | re.DOTALL)
                    if sql_match:
                        sql = sql_match.group(0).strip()
                        desc_match = re.search(r'(?:^|\n)(?:-|\d+\.)\s*(.*?)(?:\n|```|$)', rec, re.DOTALL)
                        desc = desc_match.group(1).strip() if desc_match else "Tune database configuration"
                        
                        fix = {
                            "fix_type": "configuration_change",
                            "sql": sql,
                            "description": desc,
                            "estimated_impact": "medium",
                            "affected_objects": [],
                            "safety_level": "caution"
                        }
                        fix.update(extract_savings(rec))
                        result["config"].append(fix)
        
        # Extract maintenance
        if "--- MAINTENANCE ---" in response:
            maint_section = response.split("--- MAINTENANCE ---")[1].split("---")[0]
            recs = re.split(r'\n(?=\d+\.|\-)', maint_section)
            for rec in recs:
                if any(cmd in rec.upper() for cmd in ["ANALYZE", "VACUUM", "REINDEX"]):
                    sql_match = re.search(r'(?:ANALYZE|VACUUM|REINDEX).*?;', rec, re.IGNORECASE | re.DOTALL)
                    if sql_match:
                        sql = sql_match.group(0).strip()
                        desc_match = re.search(r'(?:^|\n)(?:-|\d+\.)\s*(.*?)(?:\n|```|$)', rec, re.DOTALL)
                        desc = desc_match.group(1).strip() if desc_match else "Database maintenance task"
                        
                        fix = {
                            "fix_type": "maintenance",
                            "sql": sql,
                            "description": desc,
                            "estimated_impact": "medium",
                            "affected_objects": [],
                            "safety_level": "safe"
                        }
                        fix.update(extract_savings(rec))
                        result["maintenance"].append(fix)
        
        return result
    
    def _extract_summary(self, explanation: str) -> str:
        """Extract a brief summary from explanation"""
        # Take first 2-3 sentences
        sentences = explanation.split(". ")
        summary = ". ".join(sentences[:3])
        if not summary.endswith("."):
            summary += "."
        return summary

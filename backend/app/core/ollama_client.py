"""
Ollama LLM Client for SQL Optimization
Enhanced with sqlcoder:latest model for intelligent SQL optimization
"""
import httpx
import json
import re
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
    
    async def check_health(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Check if Ollama is accessible and a specific model is available"""
        try:
            model_to_check = model_name if model_name is not None else self.model
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if Ollama is running
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = [model.get("name", "") for model in data.get("models", [])]
                    
                    model_available = any(model_to_check in model for model in models)
                    
                    return {
                        "status": "healthy" if model_available else "model_not_found",
                        "url": self.base_url,
                        "model_checked": model_to_check,
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
    
    async def generate_corrected_code(
        self,
        original_sql: str,
        issue_details: Dict[str, Any],
        recommendations: List[str],
        database_type: str,
        schema_ddl: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate corrected SQL code based on issue recommendations using olmo-3:latest
        
        Args:
            original_sql: The original problematic SQL query
            issue_details: Details about the detected issue
            recommendations: List of recommendations to fix the issue
            database_type: Type of database (postgresql, mysql, etc.)
            schema_ddl: Optional schema DDL for context
        
        Returns:
            Dict containing corrected_sql, explanation, and changes_made
        """
        try:
            # Use the code generation model (olmo-3:latest)
            code_gen_model = settings.OLLAMA_CODE_GENERATION_MODEL
            
            logger.info(f"Using model: {code_gen_model} for corrected code generation")
            
            # Build the prompt for code generation
            prompt = self._build_corrected_code_prompt(
                original_sql, issue_details, recommendations, database_type, schema_ddl
            )

            async def _call_ollama(model_name: str) -> Dict[str, Any]:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.1,  # Low temperature for precise code generation
                                "top_p": 0.9,
                                "top_k": 40,
                                "num_predict": 2000,
                                # Override any model-default stop tokens that may prematurely stop generation
                                # (some models use '---' style stop sequences, which conflicts with our section markers)
                                "stop": ["---END---"],
                            }
                        }
                    )

                if response.status_code != 200:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": f"Ollama API returned status {response.status_code}"
                    }

                try:
                    result = response.json()
                except Exception:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": "Ollama API returned non-JSON response"
                    }

                return {
                    "success": True,
                    "status_code": response.status_code,
                    "raw": result,
                    "llm_response": result.get("response", "")
                }

            def _parse_or_error(llm_text: str) -> Dict[str, Any]:
                if not (llm_text or "").strip():
                    return {
                        "success": False,
                        "error": "Empty response from LLM"
                    }
                parsed = self._parse_corrected_code_response(llm_text)
                if not parsed.get("success", True):
                    return {
                        "success": False,
                        "error": parsed.get("error", "Could not parse LLM response")
                    }
                return {
                    "success": True,
                    "parsed": parsed
                }

            model_candidates = [
                code_gen_model,
                self.request_model,
                # Practical fallbacks (commonly available locally)
                "codellama:latest",
                "llama3:instruct",
                "llama3:latest",
            ]

            tried: List[str] = []
            last_error: str = ""
            last_raw_response: str = ""

            for model_name in [m for m in model_candidates if m and m not in tried]:
                tried.append(model_name)
                logger.info(f"Attempting corrected code generation with model: {model_name}")

                call_result = await _call_ollama(model_name)
                if not call_result.get("success"):
                    last_error = call_result.get("error", "Ollama request failed")
                    continue

                llm_response = call_result.get("llm_response", "")
                last_raw_response = llm_response

                parsed_result = _parse_or_error(llm_response)
                if parsed_result.get("success"):
                    parsed = parsed_result["parsed"]
                    return {
                        "success": True,
                        "corrected_sql": parsed["corrected_sql"],
                        "explanation": parsed["explanation"],
                        "changes_made": parsed["changes_made"],
                        "raw_response": llm_response,
                        "used_model": model_name,
                        "tried_models": tried,
                    }

                last_error = parsed_result.get("error", "Could not parse LLM response")
                logger.warning(
                    f"Corrected-code response unusable from '{model_name}' ({last_error}); trying next model"
                )

            logger.error("Failed to generate corrected code from all candidate models")
            return {
                "success": False,
                "error": last_error or "Failed to generate corrected code",
                "raw_response": last_raw_response,
                "tried_models": tried,
            }
        
        except Exception as e:
            logger.error(f"Corrected code generation failed: {e}")
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

            # sqlcoder:latest frequently returns an empty response for this prompt.
            # Try a few models in order and accept the first non-empty response.
            models_to_try = []
            if self.request_model:
                models_to_try.append(self.request_model)
            # Prefer the code-generation model (usually more instruction-following)
            if settings.OLLAMA_CODE_GENERATION_MODEL and settings.OLLAMA_CODE_GENERATION_MODEL not in models_to_try:
                models_to_try.append(settings.OLLAMA_CODE_GENERATION_MODEL)
            # Common fallbacks (only used if installed)
            for m in ["llama3:instruct", "llama3.1:latest"]:
                if m not in models_to_try:
                    models_to_try.append(m)

            last_error = None
            tried = []

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for model_name in models_to_try:
                    tried.append(model_name)
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.2,
                                "num_predict": 2000,
                            },
                        },
                    )

                    if response.status_code != 200:
                        last_error = f"API returned status {response.status_code}"
                        continue

                    result = response.json()
                    recommendations = result.get("response", "") or ""

                    # If the model returned nothing at all, try the next model.
                    if not recommendations.strip():
                        continue

                    parsed = self._parse_fix_recommendations(recommendations)

                    return {
                        "success": True,
                        "index_recommendations": parsed["indexes"],
                        "query_rewrites": parsed["rewrites"],
                        "configuration_changes": parsed["config"],
                        "maintenance_tasks": parsed["maintenance"],
                        "raw_response": recommendations,
                        "model": model_name,
                        "tried_models": tried,
                    }

            return {
                "success": False,
                "error": last_error or "Ollama returned an empty response",
                "tried_models": tried,
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
                elif "DROP INDEX" in rec.upper():
                    sql_match = re.search(r'DROP\s+INDEX.*?;', rec, re.IGNORECASE | re.DOTALL)
                    if sql_match:
                        sql = sql_match.group(0).strip()
                        desc_match = re.search(r'(?:^|\n)(?:-|\d+\.)\s*(.*?)(?:\n|```|$)', rec, re.DOTALL)
                        desc = desc_match.group(1).strip() if desc_match else "Drop unused index"

                        fix = {
                            "fix_type": "index_drop",
                            "sql": sql,
                            "description": desc,
                            "estimated_impact": "high" if "high" in rec.lower() else "medium",
                            "affected_objects": [],
                            "safety_level": "caution",
                        }
                        fix.update(extract_savings(rec))
                        result["indexes"].append(fix)

        # Fallback: some models ignore the section markers.
        # If we didn't capture any indexes above, scan the whole response for CREATE/DROP INDEX.
        if not result["indexes"]:
            index_statements = re.findall(
                r"(?:CREATE\s+(?:UNIQUE\s+)?INDEX(?:\s+CONCURRENTLY)?|DROP\s+INDEX(?:\s+CONCURRENTLY)?(?:\s+IF\s+EXISTS)?)\s+[\s\S]*?(?:;|$)",
                response,
                flags=re.IGNORECASE,
            )
            for stmt in index_statements:
                sql = stmt.strip()
                if not sql:
                    continue
                if not sql.endswith(";"):
                    sql = sql + ";"

                fix_type = "index_creation" if sql.upper().startswith("CREATE") else "index_drop"
                safety = "safe" if fix_type == "index_creation" else "caution"
                result["indexes"].append(
                    {
                        "fix_type": fix_type,
                        "sql": sql,
                        "description": "Index recommendation",
                        "estimated_impact": "medium",
                        "affected_objects": [],
                        "safety_level": safety,
                    }
                )
        
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
    
    def _build_corrected_code_prompt(
        self,
        original_sql: str,
        issue_details: Dict[str, Any],
        recommendations: List[str],
        database_type: str,
        schema_ddl: Optional[str] = None
    ) -> str:
        """Build prompt for generating corrected code using olmo-3:latest"""
        
        schema_section = ""
        if schema_ddl:
            schema_section = f"""
### DATABASE SCHEMA:
```sql
{schema_ddl}
```
"""
        
        recommendations_text = "\n".join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations)])
        
        prompt = f"""You are an expert SQL developer specializing in {database_type.upper()} database optimization.

### YOUR TASK:
Generate corrected SQL code that addresses the detected performance issue and implements the provided recommendations.

### DETECTED ISSUE:
**Type:** {issue_details.get('issue_type', 'Unknown')}
**Severity:** {issue_details.get('severity', 'Unknown')}
**Title:** {issue_details.get('title', 'Performance Issue')}
**Description:** {issue_details.get('description', 'No description provided')}

### ORIGINAL SQL QUERY:
```sql
{original_sql}
```
{schema_section}
### RECOMMENDATIONS TO IMPLEMENT:
{recommendations_text}

### REQUIREMENTS:
1. **Implement ALL recommendations** listed above
2. **Preserve query semantics** - results must match the original query
3. **Provide executable SQL** - no placeholders, comments only for clarity
4. **Optimize for performance** - apply best practices for {database_type}
5. **Add brief inline comments** explaining key changes

### OUTPUT FORMAT:
Provide your response in this EXACT format (IMPORTANT: do NOT use markdown fences like ``` and do NOT start lines with '---'):

CORRECTED_SQL:
[Your complete, executable corrected SQL query here with inline comments]

EXPLANATION:
[Brief explanation of the changes and why they help]

CHANGES_MADE:
- [Change 1]
- [Change 2]

IMPLEMENTATION_NOTES:
- [Any important notes / testing tips]

END

Now provide your corrected code:"""
        
        return prompt
    
    def _parse_corrected_code_response(self, response: str) -> Dict[str, Any]:
        """Parse corrected code response from olmo-3:latest"""
        import re
        
        corrected_sql = ""
        explanation = ""
        changes_made = []
        parsing_method = "unknown"
        
        logger.debug(f"Parsing corrected code response (length: {len(response)} chars)")

        # Strategy 0: Parse explicit plain-text markers (preferred)
        if "CORRECTED_SQL:" in response:
            parsing_method = "plain_markers"
            try:
                sql_match = re.search(
                    r"CORRECTED_SQL:\s*(.*?)(?:\n\s*EXPLANATION:|\n\s*CHANGES_MADE:|\n\s*IMPLEMENTATION_NOTES:|\n\s*END\s*$)",
                    response,
                    re.DOTALL | re.IGNORECASE,
                )
                if sql_match:
                    corrected_sql = sql_match.group(1).strip()

                exp_match = re.search(
                    r"EXPLANATION:\s*(.*?)(?:\n\s*CHANGES_MADE:|\n\s*IMPLEMENTATION_NOTES:|\n\s*END\s*$)",
                    response,
                    re.DOTALL | re.IGNORECASE,
                )
                if exp_match:
                    explanation = exp_match.group(1).strip()

                changes_match = re.search(
                    r"CHANGES_MADE:\s*(.*?)(?:\n\s*IMPLEMENTATION_NOTES:|\n\s*END\s*$)",
                    response,
                    re.DOTALL | re.IGNORECASE,
                )
                if changes_match:
                    changes_block = changes_match.group(1).strip()
                    for line in changes_block.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        line = re.sub(r"^[-*\d\.\)]+\s*", "", line)
                        if line:
                            changes_made.append(line)
            except Exception:
                # Fall through to other strategies
                parsing_method = "plain_markers_failed"
        
        # Strategy 1: Extract from section markers
        if "--- CORRECTED SQL ---" in response:
            parts = response.split("--- CORRECTED SQL ---")
            if len(parts) > 1:
                remaining = parts[1]
                
                # Find the end of SQL section
                if "--- EXPLANATION ---" in remaining:
                    sql_parts = remaining.split("--- EXPLANATION ---")
                    corrected_sql = sql_parts[0].strip()
                    
                    # Extract explanation
                    exp_remaining = sql_parts[1]
                    if "--- IMPLEMENTATION NOTES ---" in exp_remaining:
                        explanation = exp_remaining.split("--- IMPLEMENTATION NOTES ---")[0].strip()
                    else:
                        explanation = exp_remaining.split("---END---")[0].strip()
                    
                    parsing_method = "section_markers"
        
        # Strategy 2: Extract from code blocks if section markers failed
        if not corrected_sql:
            logger.debug("Section markers not found, trying code blocks")
            corrected_sql = self._extract_sql_from_code_blocks(response)
            if corrected_sql:
                parsing_method = "code_blocks"
                # Try to extract explanation from remaining text
                if "**Changes Made:**" in response:
                    exp_match = re.search(r'\*\*Changes Made:\*\*(.*?)(?:---|$)', response, re.DOTALL | re.IGNORECASE)
                    if exp_match:
                        explanation = exp_match.group(1).strip()
        
        # Strategy 3: Heuristic extraction
        if not corrected_sql:
            logger.debug("Code blocks not found, trying heuristic extraction")
            corrected_sql = self._extract_sql_heuristic(response)
            if corrected_sql:
                parsing_method = "heuristic"
        
        # Clean the SQL
        corrected_sql = self._clean_sql(corrected_sql)
        
        # Validate
        is_valid = self._validate_sql_basic(corrected_sql)
        
        if not is_valid:
            logger.error(f"Failed to parse valid corrected SQL from response")
            return {
                "corrected_sql": "",
                "explanation": "",
                "changes_made": [],
                "success": False,
                "error": "Could not parse valid corrected SQL from LLM response",
                "raw_response": response
            }
        
        # Extract changes made from explanation
        if explanation:
            # Look for numbered or bulleted list of changes
            change_patterns = [
                r'\d+\.\s*([^\n]+)',  # Numbered list
                r'[-•]\s*([^\n]+)',   # Bulleted list
            ]
            
            for pattern in change_patterns:
                matches = re.findall(pattern, explanation)
                if matches:
                    changes_made = [match.strip() for match in matches if match.strip()]
                    break
        
        logger.info(f"Corrected code parsing complete - Method: {parsing_method}, Valid: {is_valid}")
        
        return {
            "corrected_sql": corrected_sql,
            "explanation": explanation or "No explanation provided",
            "changes_made": changes_made,
            "success": True,
            "raw_response": response
        }
    
    def _extract_summary(self, explanation: str) -> str:
        """Extract a brief summary from explanation"""
        # Take first 2-3 sentences
        sentences = explanation.split(". ")
        summary = ". ".join(sentences[:3])
        if not summary.endswith("."):
            summary += "."
        return summary

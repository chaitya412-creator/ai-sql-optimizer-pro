import asyncio

import httpx

from app.config import settings
from app.core.ollama_client import OllamaClient
from app.models.database import Connection, Query, QueryIssue, SessionLocal


async def main() -> None:
    db = SessionLocal()
    try:
        issue_id = 260
        issue = db.query(QueryIssue).filter(QueryIssue.id == issue_id).first()
        print("issue", bool(issue), "issue_id", issue_id)
        if not issue:
            return

        query = db.query(Query).filter(Query.id == issue.query_id).first() if issue.query_id else None
        connection = (
            db.query(Connection).filter(Connection.id == issue.connection_id).first()
            if issue.connection_id
            else None
        )

        print("query", bool(query), "query_id", issue.query_id)
        print("connection", bool(connection), "connection_id", issue.connection_id)
        print("recs_type", type(issue.recommendations).__name__, "recs_len", len(issue.recommendations))
        print("ollama_base_url", settings.OLLAMA_BASE_URL)
        print("code_gen_model", settings.OLLAMA_CODE_GENERATION_MODEL)
        print("primary_model", settings.OLLAMA_MODEL)

        issue_details = {
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "title": issue.title,
            "description": issue.description,
            "affected_objects": issue.affected_objects,
            "metrics": issue.metrics,
        }

        client = OllamaClient()
        prompt = client._build_corrected_code_prompt(
            original_sql=(query.sql_text if query else ""),
            issue_details=issue_details,
            recommendations=(issue.recommendations if isinstance(issue.recommendations, list) else []),
            database_type=(connection.engine if connection else "postgresql"),
            schema_ddl=None,
        )

        print("prompt_len", len(prompt))

        async with httpx.AsyncClient(timeout=120.0) as http:
            for model in [settings.OLLAMA_CODE_GENERATION_MODEL, settings.OLLAMA_MODEL]:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 800, "stop": ["---END---"]},
                }

                r = await http.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload)
                print("MODEL", model, "HTTP", r.status_code)

                try:
                    j = r.json()
                except Exception:
                    print("NON_JSON", r.text[:500])
                    continue

                resp = j.get("response", "")
                print(
                    "RESP_LEN",
                    len(resp),
                    "DONE",
                    j.get("done"),
                    "DONE_REASON",
                    j.get("done_reason"),
                    "ERROR",
                    j.get("error"),
                )
                print("RESP_HEAD", (resp[:220].replace("\n", "\\n") if resp else ""))
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

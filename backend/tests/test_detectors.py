import datetime
from app.core.plan_analyzer import PlanAnalyzer


def test_cardinality_detector_detects_mismatch():
    # Simulate a PostgreSQL EXPLAIN ANALYZE plan with large cardinality mismatch
    plan = [
        {
            "Plan": {
                "Node Type": "Seq Scan",
                "Relation Name": "users",
                "Plan Rows": 1000,
                "Actual Rows": 100000
            }
        }
    ]

    result = PlanAnalyzer.analyze_plan(plan=plan, engine="postgresql", sql_query="SELECT * FROM users")
    issues = result.get("issues", [])

    assert any(i["issue_type"] == "wrong_cardinality" for i in issues), "Cardinality mismatch should be detected"


def test_statistics_detector_detects_stale_stats():
    # Simulate table stats with last_analyze > 30 days ago
    old_date = (datetime.datetime.utcnow() - datetime.timedelta(days=40)).isoformat()
    table_stats = {
        "users": {
            "last_analyze": old_date,
            "seq_scan": 10,
            "idx_scan": 1
        }
    }

    result = PlanAnalyzer.analyze_plan(plan=None, engine="postgresql", sql_query="SELECT * FROM users", table_stats=table_stats)
    issues = result.get("issues", [])

    assert any(i["issue_type"] == "stale_statistics" for i in issues), "Stale statistics should be detected"
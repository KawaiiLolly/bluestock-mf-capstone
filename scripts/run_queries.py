"""
run_queries.py
==============

Reads queries.sql, runs each of the 10 queries against
bluestock_mf.db, prints results to console, and saves each
result as a CSV to reports/query_results/.

Run:
    python scripts/run_queries.py
"""

import re
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text


# Paths
BASE_DIR  = Path(__file__).resolve().parent.parent
DB_PATH   = BASE_DIR / "data" / "db" / "bluestock_mf.db"
SQL_PATH  = BASE_DIR / "sql" / "queries.sql"
OUT_DIR   = BASE_DIR / "reports" / "query_results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def parse_queries(sql_text):
    """
    Split queries.sql on '-- Q<N>.' headers.
    Returns list of (id, title, sql) tuples.
    """
    pattern = re.compile(r"--\s*(Q\d+)\.\s*(.+)")
    blocks  = []
    current_id    = None
    current_title = None
    current_lines = []

    for line in sql_text.splitlines():
        match = pattern.match(line.strip())
        if match:
            if current_id and current_lines:
                sql = "\n".join(current_lines).strip().rstrip(";")
                blocks.append((current_id, current_title, sql))
                current_lines = []
            current_id    = match.group(1)
            current_title = match.group(2).strip()
        elif current_id:
            if not line.strip().startswith("--"):
                current_lines.append(line)

    if current_id and current_lines:
        sql = "\n".join(current_lines).strip().rstrip(";")
        blocks.append((current_id, current_title, sql))

    return blocks


def main():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Run: python scripts/db_loader.py  first.")
        return

    engine  = create_engine(f"sqlite:///{DB_PATH}")
    queries = parse_queries(SQL_PATH.read_text(encoding="utf-8"))

    print("=" * 60)
    print(f"  Running {len(queries)} queries against bluestock_mf.db")
    print("=" * 60)

    summary = []

    for qid, title, sql in queries:
        print(f"\n{'─'*60}")
        print(f"  {qid}. {title}")
        print(f"{'─'*60}")

        try:
            with engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)

            print(df.to_string(index=False))
            print(f"\n  → {len(df)} rows returned")

            # Save result CSV
            safe_title = re.sub(r"[^a-z0-9]+", "_", title.lower())[:40]
            filename   = f"{qid.lower()}_{safe_title}.csv"
            df.to_csv(OUT_DIR / filename, index=False)
            print(f"  → Saved: reports/query_results/{filename}")

            summary.append({"query": qid, "title": title, "rows": len(df), "status": "OK"})

        except Exception as e:
            print(f"  ERROR: {e}")
            summary.append({"query": qid, "title": title, "rows": 0, "status": f"ERROR: {e}"})

    # Print summary table
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'─'*60}")
    for s in summary:
        status_icon = "✓" if s["status"] == "OK" else "✗"
        print(f"  {status_icon} {s['query']:<5} {s['title']:<38} {s['rows']:>5} rows")
    print("=" * 60)


if __name__ == "__main__":
    main()

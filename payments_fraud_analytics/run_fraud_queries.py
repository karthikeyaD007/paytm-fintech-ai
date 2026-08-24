"""
Executes every query in fraud_queries.sql against paytm_payments.db and
writes the results (as committed evidence of "queries with output") to
fraud_queries_output.txt.

Run:
    python run_fraud_queries.py
"""

import os
import re
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "paytm_payments.db")
SQL_PATH = os.path.join(HERE, "fraud_queries.sql")
OUT_PATH = os.path.join(HERE, "fraud_queries_output.txt")


def split_statements(sql_text):
    # Split on ';' at statement end; each chunk keeps its leading comment
    # block (SQLite's parser treats '--' lines as whitespace, so a chunk
    # like "-- 1. TITLE\nSELECT ..." executes fine as a single statement).
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]
    return statements


def main():
    with open(SQL_PATH) as f:
        sql_text = f.read()

    statements = split_statements(sql_text)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    lines = []
    for i, stmt in enumerate(statements, start=1):
        # pull the last comment block right before the SELECT as a label
        header_match = re.search(r"--\s*(\d[^\n]*)\n", stmt)
        label = header_match.group(1).strip() if header_match else f"Query {i}"

        cur.execute(stmt)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()

        lines.append("=" * 90)
        lines.append(f"QUERY {i}: {label}")
        lines.append("=" * 90)
        lines.append(" | ".join(cols))
        lines.append("-" * 90)
        for row in rows[:30]:
            lines.append(" | ".join(str(v) for v in row))
        if len(rows) > 30:
            lines.append(f"... ({len(rows) - 30} more rows, {len(rows)} total)")
        else:
            lines.append(f"({len(rows)} total rows)")
        lines.append("")

    conn.close()

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Executed {len(statements)} queries. Output written to {OUT_PATH}")


if __name__ == "__main__":
    main()

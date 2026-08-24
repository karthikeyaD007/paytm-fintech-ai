"""
Recreates paytm_payments.db (SQLite) from merchants.csv, users.csv, ledger.csv.

Run from the payments_fraud_analytics/ directory:
    python create_database.py
"""

import os
import sqlite3
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "paytm_payments.db")

SCHEMA = """
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS merchants;

CREATE TABLE merchants (
    merchant_id   INTEGER PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    category      TEXT NOT NULL,
    region        TEXT NOT NULL
);

CREATE TABLE users (
    user_id     INTEGER PRIMARY KEY,
    signup_date TEXT NOT NULL
);

CREATE TABLE transactions (
    transaction_id   TEXT PRIMARY KEY,
    user_id          INTEGER NOT NULL,
    merchant_id      INTEGER NOT NULL,
    transaction_time TEXT NOT NULL,
    amount_inr       REAL NOT NULL,
    payment_method   TEXT NOT NULL,
    status           TEXT NOT NULL,
    risk_score       INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);
"""


def main():
    merchants = pd.read_csv(os.path.join(HERE, "merchants.csv"))
    users = pd.read_csv(os.path.join(HERE, "users.csv"))
    ledger = pd.read_csv(os.path.join(HERE, "ledger.csv"))

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)

    merchants.to_sql("merchants", conn, if_exists="append", index=False)
    users.to_sql("users", conn, if_exists="append", index=False)
    ledger.rename(columns={}).to_sql("transactions", conn, if_exists="append", index=False)

    conn.commit()

    cur = conn.cursor()
    for table in ("merchants", "users", "transactions"):
        count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count} rows")

    conn.close()
    print(f"Database written to {DB_PATH}")


if __name__ == "__main__":
    main()

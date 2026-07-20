"""
storage.py

Simple SQLite-backed persistence for user assessment history.
"""
import sqlite3
import json
from typing import List, Dict

DB_PATH = "data.db"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    total REAL NOT NULL,
    breakdown TEXT NOT NULL
);
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_SQL)
    conn.commit()
    conn.close()


def save_history_entry(timestamp: str, total: float, breakdown: Dict):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO history (timestamp, total, breakdown) VALUES (?, ?, ?)",
                (timestamp, float(total), json.dumps(breakdown)))
    conn.commit()
    conn.close()


def load_history(limit: int = 500) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT timestamp, total, breakdown FROM history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    out = []
    for ts, total, breakdown_json in rows:
        try:
            breakdown = json.loads(breakdown_json)
        except Exception:
            breakdown = {}
        out.append({"timestamp": ts, "total": total, "breakdown": breakdown})
    return out

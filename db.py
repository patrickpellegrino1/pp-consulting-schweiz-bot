import sqlite3
from datetime import datetime
from typing import Dict, Any

DB_PATH = "pp_consulting.db"

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            name TEXT,
            company TEXT,
            industry TEXT,
            goal TEXT,
            status TEXT,
            budget TEXT,
            timeline TEXT,
            contact TEXT,
            notes TEXT,
            raw_json TEXT
        )
    """)
    con.commit()
    con.close()

def save_lead(data: Dict[str, Any], raw_json: str) -> int:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO leads (created_at, name, company, industry, goal, status, budget, timeline, contact, notes, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        data.get("name"),
        data.get("company"),
        data.get("industry"),
        data.get("goal"),
        data.get("status"),
        data.get("budget"),
        data.get("timeline"),
        data.get("contact"),
        data.get("notes"),
        raw_json
    ))
    con.commit()
    lid = cur.lastrowid
    con.close()
    return lid
Commit new file
[ Commit message ]
[ Commit new file ]
Add db.py

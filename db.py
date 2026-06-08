import os
import sqlite3
from datetime import date, datetime
import streamlit as st

# ── DB 설정 및 기존 함수들 ──────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "data", "petgpt.db")

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ── 기존 스키마에 투약 관리 테이블 통합 ───────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, auth_kind TEXT NOT NULL DEFAULT 'local', external_id TEXT, kakao_id TEXT UNIQUE, nickname TEXT, created_at TEXT DEFAULT (datetime('now')), UNIQUE (auth_kind, external_id));
CREATE TABLE IF NOT EXISTS pets (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, species TEXT, age INTEGER, weight REAL, neutered INTEGER DEFAULT 0, mer INTEGER, created_at TEXT DEFAULT (datetime('now')), FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS schedules (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, pet_id INTEGER, care_type TEXT NOT NULL, last_done TEXT NOT NULL, cycle_days INTEGER DEFAULT 0, next_due TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE SET NULL);
CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, pet_id INTEGER, visit_date TEXT NOT NULL, hospital TEXT, visit_type TEXT, weight REAL, cost INTEGER DEFAULT 0, diagnosis TEXT, prescription TEXT, memo TEXT, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE SET NULL);
CREATE TABLE IF NOT EXISTS medications (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, pet_id INTEGER, med_name TEXT NOT NULL, dosage TEXT, dosage_time TEXT, start_date TEXT, cycle_days INTEGER, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE SET NULL);
CREATE TABLE IF NOT EXISTS medication_history (id INTEGER PRIMARY KEY AUTOINCREMENT, med_id INTEGER, check_date TEXT NOT NULL, FOREIGN KEY(med_id) REFERENCES medications(id) ON DELETE CASCADE);
"""

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        conn.execute("INSERT OR IGNORE INTO users (id, auth_kind, external_id, nickname) VALUES (1, 'guest', 'guest', '게스트')")

def current_user_id():
    return st.session_state.get("user_id", 1)

def _to_iso(d):
    return d.isoformat() if isinstance(d, (date, datetime)) else str(d)

# ── [중요] 기존 팀원들의 함수들은 이 아래에 반드시 있어야 합니다! ──
# 현재 파일에서 get_pets, get_schedules, get_records 등을 찾아서 이 밑에 복사하세요.
# 만약 없다면, 이전에 사용하던 백업 파일에서 복사해 오셔야 합니다.

# ── 투약 관리 함수 (딱 한 번만 정의) ────────────────────────────────
def add_medication(pet_id, med_name, dosage, dosage_time, start_date, cycle_days):
    with get_conn() as conn:
        conn.execute("INSERT INTO medications (user_id, pet_id, med_name, dosage, dosage_time, start_date, cycle_days) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                     (current_user_id(), pet_id, med_name, dosage, dosage_time, str(start_date), cycle_days))

def get_medications(pet_id=None):
    with get_conn() as conn:
        query = "SELECT m.*, p.name as pet_name FROM medications m LEFT JOIN pets p ON m.pet_id = p.id WHERE m.user_id = ?"
        params = [current_user_id()]
        if pet_id: query += " AND m.pet_id = ?"; params.append(pet_id)
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def complete_medication(med_id, check_date):
    with get_conn() as conn:
        conn.execute("INSERT INTO medication_history (med_id, check_date) VALUES (?, ?)", (med_id, str(check_date)))

def get_medication_history(med_id=None):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM medication_history ORDER BY check_date DESC").fetchall()
    return [dict(r) for r in rows]

init_db()

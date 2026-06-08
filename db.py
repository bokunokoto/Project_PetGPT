"""SQLite 데이터 접근 계층.

페이지들은 이 모듈의 함수만 호출하면 되고, SQL 을 직접 다루지 않는다.
나중에 카카오 로그인을 붙일 때는 current_user_id() 만 바꿔주면 된다.
"""
import os
import sqlite3
from datetime import date, datetime

import streamlit as st

# ── DB 파일 위치 ────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "data", "petgpt.db")


# ── 연결 ───────────────────────────────────────────────────────────
def get_conn():
    """Streamlit 의 멀티스레드 환경에서 안전하게 동작하도록 옵션을 준다."""
    # data/ 폴더가 없으면 먼저 만든다.
    # (Streamlit Cloud 등 폴더가 보장되지 않는 환경 대비 안전 장치)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # 결과를 dict 처럼 row["name"] 으로 꺼낼 수 있게
    conn.row_factory = sqlite3.Row
    # 외래키 제약 활성화 (SQLite 는 기본 꺼져 있음)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── 스키마 초기화 ───────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    auth_kind   TEXT NOT NULL DEFAULT 'local',  -- 'local' (가짜 로그인) | 'kakao' | 'guest'
    external_id TEXT,                            -- local: 닉네임 / kakao: 카카오 user id
    kakao_id    TEXT UNIQUE,                     -- (호환용) 카카오 user id; external_id 와 중복돼도 OK
    nickname    TEXT,
    created_at  TEXT DEFAULT (datetime('now')),
    UNIQUE (auth_kind, external_id)
);

CREATE TABLE IF NOT EXISTS pets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    name        TEXT NOT NULL,
    species     TEXT,                        -- '강아지' / '고양이'
    age         INTEGER,
    weight      REAL,
    neutered    INTEGER DEFAULT 0,           -- bool 대용 (0/1)
    mer         INTEGER,                     -- 최근 계산된 하루 권장 칼로리
    created_at  TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS schedules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    pet_id      INTEGER,                     -- 반려동물이 안 골라져 있을 수도 있어 NULL 허용
    care_type   TEXT NOT NULL,               -- '예방접종' 등
    last_done   TEXT NOT NULL,               -- ISO 날짜 문자열
    cycle_days  INTEGER DEFAULT 0,           -- 0 이면 1회성
    next_due    TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pet_id)  REFERENCES pets(id)  ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS records (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    pet_id       INTEGER,
    visit_date   TEXT NOT NULL,
    hospital     TEXT,
    visit_type   TEXT,                       -- '일반 진료' 등
    weight       REAL,
    cost         INTEGER DEFAULT 0,
    diagnosis    TEXT,
    prescription TEXT,
    memo         TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pet_id)  REFERENCES pets(id)  ON DELETE SET NULL
);
"""


def init_db():
    """앱 시작 시 한 번 호출. 테이블이 없으면 만들고, 익명 사용자도 보장한다."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        # 익명 사용자(id=1) 가 없으면 만든다.
        # 로그인 안 하고 들어온 방문자가 이 사용자 소유로 데이터를 쌓는다.
        conn.execute(
            """INSERT OR IGNORE INTO users (id, auth_kind, external_id, nickname)
               VALUES (1, 'guest', 'guest', '게스트')"""
        )


def current_user_id():
    """현재 로그인된 사용자 ID. 로그인 안 했으면 게스트(1) 반환.

    세션 키는 auth.py 에서 채워준다.
    """
    return st.session_state.get("user_id", 1)


def get_or_create_user(kind: str, external_id: str, nickname: str) -> int:
    """auth_kind + external_id 로 사용자를 찾고, 없으면 만든다.

    가짜 로그인:  kind='local',  external_id=<닉네임>
    카카오 로그인: kind='kakao', external_id=<카카오 user id>

    페이지 코드가 이 함수만 알면 되도록, 인증 종류별 분기는 여기 안에 가둔다.
    """
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE auth_kind = ? AND external_id = ?",
            (kind, external_id),
        ).fetchone()
        if row:
            # 닉네임이 바뀌었을 수 있으니 가볍게 갱신
            conn.execute("UPDATE users SET nickname = ? WHERE id = ?",
                         (nickname, row["id"]))
            return row["id"]

        cur = conn.execute(
            """INSERT INTO users (auth_kind, external_id, kakao_id, nickname)
               VALUES (?, ?, ?, ?)""",
            (kind, external_id,
             external_id if kind == "kakao" else None,
             nickname),
        )
        return cur.lastrowid


# ── pets ───────────────────────────────────────────────────────────
def get_pets():
    """현재 사용자의 반려동물 목록을 dict 리스트로 반환."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM pets WHERE user_id = ? ORDER BY created_at",
            (current_user_id(),),
        ).fetchall()
    return [dict(r) for r in rows]


def upsert_pet(name, species, age, weight, neutered, mer):
    """같은 이름의 반려동물이 있으면 갱신, 없으면 추가."""
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM pets WHERE user_id = ? AND name = ?",
            (current_user_id(), name),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE pets
                   SET species=?, age=?, weight=?, neutered=?, mer=?
                   WHERE id=?""",
                (species, age, weight, int(neutered), mer, existing["id"]),
            )
            return existing["id"]
        else:
            cur = conn.execute(
                """INSERT INTO pets (user_id, name, species, age, weight, neutered, mer)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (current_user_id(), name, species, age, weight, int(neutered), mer),
            )
            return cur.lastrowid


def delete_pet(pet_id):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM pets WHERE id = ? AND user_id = ?",
            (pet_id, current_user_id()),
        )


# ── schedules ──────────────────────────────────────────────────────
def _to_iso(d):
    """date 객체든 문자열이든 ISO 문자열로 통일."""
    return d.isoformat() if isinstance(d, (date, datetime)) else str(d)


def get_schedules():
    """다가오는 순서로 정렬된 일정 목록. 반려동물 이름도 JOIN 으로 같이 가져온다."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT s.*, p.name AS pet_name
               FROM schedules s
               LEFT JOIN pets p ON p.id = s.pet_id
               WHERE s.user_id = ?
               ORDER BY s.next_due""",
            (current_user_id(),),
        ).fetchall()
    return [dict(r) for r in rows]


def add_schedule(pet_id, care_type, last_done, cycle_days, next_due):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO schedules
               (user_id, pet_id, care_type, last_done, cycle_days, next_due)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (current_user_id(), pet_id, care_type,
             _to_iso(last_done), cycle_days, _to_iso(next_due)),
        )


def complete_schedule(schedule_id, today, cycle_days):
    """완료 처리: 주기가 있으면 다음 날짜로 갱신, 없으면 삭제."""
    from datetime import timedelta
    with get_conn() as conn:
        if cycle_days:
            new_next = today + timedelta(days=cycle_days)
            conn.execute(
                "UPDATE schedules SET last_done=?, next_due=? WHERE id=? AND user_id=?",
                (_to_iso(today), _to_iso(new_next), schedule_id, current_user_id()),
            )
        else:
            conn.execute(
                "DELETE FROM schedules WHERE id=? AND user_id=?",
                (schedule_id, current_user_id()),
            )


# ── records ────────────────────────────────────────────────────────
def get_records(pet_id=None):
    """진료 기록을 최신순으로. pet_id 주면 그 반려동물 것만."""
    sql = """SELECT r.*, p.name AS pet_name
             FROM records r
             LEFT JOIN pets p ON p.id = r.pet_id
             WHERE r.user_id = ?"""
    params = [current_user_id()]
    if pet_id is not None:
        sql += " AND r.pet_id = ?"
        params.append(pet_id)
    sql += " ORDER BY r.visit_date DESC, r.id DESC"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def add_record(pet_id, visit_date, hospital, visit_type, weight, cost,
               diagnosis, prescription, memo):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO records
               (user_id, pet_id, visit_date, hospital, visit_type,
                weight, cost, diagnosis, prescription, memo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (current_user_id(), pet_id, _to_iso(visit_date),
             hospital, visit_type, weight, cost,
             diagnosis, prescription, memo),
        )


def delete_record(record_id):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM records WHERE id=? AND user_id=?",
            (record_id, current_user_id()),
        )
        import sqlite3
from datetime import date

def init_medication_db():
    """투약 관리 관련 테이블이 없을 경우 생성합니다."""
    conn = sqlite3.connect("pet_care.db")  # 기존 프로젝트 DB 파일명에 맞게 수정하세요.
    cursor = conn.cursor()
    
    # 1. 투약 일정 기본 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            med_name TEXT NOT NULL,
            dosage TEXT,
            dosage_time TEXT, -- 예: "08:00", "아침 식후"
            start_date TEXT,
            cycle_days INTEGER -- 1: 매일, 7: 일주일마다, 0: 1회성
        )
    """)
    
    # 2. 투약 완료 히스토리 테이블 (복용 준수율 통계용)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medication_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            med_id INTEGER,
            check_date TEXT NOT NULL, -- 복용 완료한 날짜 (YYYY-MM-DD)
            FOREIGN KEY(med_id) REFERENCES medications(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def add_medication(pet_id, med_name, dosage, dosage_time, start_date, cycle_days):
    """새로운 투약 일정을 등록합니다."""
    conn = sqlite3.connect("pet_care.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO medications (pet_id, med_name, dosage, dosage_time, start_date, cycle_days)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (pet_id, med_name, dosage, dosage_time, str(start_date), cycle_days))
    conn.commit()
    conn.close()

def get_medications(pet_id=None):
    """등록된 투약 일정 목록을 가져옵니다."""
    conn = sqlite3.connect("pet_care.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 반려동물 이름까지 함께 가져오기 위해 JOIN 사용 (기존 pets 테이블 구조에 맞춤)
    query = """
        SELECT m.*, p.name as pet_name 
        FROM medications m
        LEFT JOIN pets p ON m.pet_id = p.id
    """
    if pet_id:
        query += " WHERE m.pet_id = ?"
        cursor.execute(query, (pet_id,))
    else:
        cursor.execute(query)
        
    rows = cursor.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def complete_medication(med_id, check_date):
    """오늘 약을 먹었다고 체크하면 히스토리에 기록합니다."""
    conn = sqlite3.connect("pet_care.db")
    cursor = conn.cursor()
    # 중복 체크 방지 (같은 약을 같은 날 두 번 체크하지 않도록)
    cursor.execute("""
        SELECT id FROM medication_history WHERE med_id = ? AND check_date = ?
    """, (med_id, str(check_date)))
    
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO medication_history (med_id, check_date)
            VALUES (?, ?)
        """, (med_id, str(check_date)))
        conn.commit()
    conn.close()

def get_medication_history(med_id=None):
    """투약 기록 히스토리를 가져옵니다."""
    conn = sqlite3.connect("pet_care.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if med_id:
        cursor.execute("SELECT * FROM medication_history WHERE med_id = ? ORDER BY check_date DESC", (med_id,))
    else:
        cursor.execute("SELECT * FROM medication_history ORDER BY check_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
    import sqlite3
from datetime import date

def init_medication_db():
    """투약 관리 관련 테이블이 없을 경우 생성합니다."""
    conn = sqlite3.connect("pet_care.db")
    cursor = conn.cursor()
    
    # 1. 투약 일정 기본 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            med_name TEXT NOT NULL,
            dosage TEXT,
            dosage_time TEXT,
            start_date TEXT,
            cycle_days INTEGER
        )
    """)
    
    # 2. 투약 완료 히스토리 테이블 (복용 준수율 통계용)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medication_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            med_id INTEGER,
            check_date TEXT NOT NULL,
            FOREIGN KEY(med_id) REFERENCES medications(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def add_medication(pet_id, med_name, dosage, dosage_time, start_date, cycle_days):
    """새로운 투약 일정을 등록합니다."""
    conn = sqlite3.connect("pet_care.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO medications (pet_id, med_name, dosage, dosage_time, start_date, cycle_days)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (pet_id, med_name, dosage, dosage_time, str(start_date), cycle_days))
    conn.commit()
    conn.close()

def get_medications(pet_id=None):
    """등록된 투약 일정 목록을 가져옵니다."""
    conn = sqlite3.connect("pet_care.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 반려동물 이름까지 함께 가져오기 위해 JOIN 사용
    query = """
        SELECT m.*, p.name as pet_name 
        FROM medications m
        LEFT JOIN pets p ON m.pet_id = p.id
    """
    if pet_id:
        query += " WHERE m.pet_id = ?"
        cursor.execute(query, (pet_id,))
    else:
        cursor.execute(query)
        
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def complete_medication(med_id, check_date):
    """오늘 약을 먹었다고 체크하면 히스토리에 기록합니다."""
    conn = sqlite3.connect("pet_care.db")
    cursor = conn.cursor()
    
    # 중복 체크 방지
    cursor.execute("""
        SELECT id FROM medication_history WHERE med_id = ? AND check_date = ?
    """, (med_id, str(check_date)))
    
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO medication_history (med_id, check_date)
            VALUES (?, ?)
        """, (med_id, str(check_date)))
        conn.commit()
    conn.close()

def get_medication_history(med_id=None):
    """투약 기록 히스토리를 가져옵니다."""
    conn = sqlite3.connect("pet_care.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if med_id:
        cursor.execute("SELECT * FROM medication_history WHERE med_id = ? ORDER BY check_date DESC", (med_id,))
    else:
        cursor.execute("SELECT * FROM medication_history ORDER BY check_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 모듈 import 시 자동 초기화 ─────────────────────────────────────
# 어떤 페이지로 직접 진입하든(예: /health) 테이블이 보장되도록,
# db.py 가 처음 import 되는 시점에 한 번 init_db() 를 호출한다.
# init_db() 내부에서 CREATE TABLE IF NOT EXISTS 를 쓰므로 중복 호출도 안전.
init_db()

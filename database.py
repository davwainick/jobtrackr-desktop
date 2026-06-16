"""SQLite database manager for JobTrackr."""

import sqlite3
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

def _get_db_path() -> str:
    """Return the path to the SQLite database file in user's data directory."""
    if os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif os.sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
    app_dir = os.path.join(base, "JobTrackr")
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "jobtrackr.db")


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    # Naive UTC timestamp (no offset suffix) to keep the stored format
    # identical to existing rows so lexical ORDER BY stays consistent.
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    id               TEXT PRIMARY KEY,
    company_name     TEXT NOT NULL,
    product_platform TEXT,
    tier             TEXT,
    status           TEXT,
    hq_location      TEXT,
    remote_posture   TEXT,
    company_size     TEXT,
    funding_stage    TEXT,
    open_role        INTEGER DEFAULT 0,
    why_you_fit      TEXT,
    website_url      TEXT,
    careers_url      TEXT,
    linkedin_url     TEXT,
    last_checked     TEXT,
    next_action      TEXT,
    due_date         TEXT,
    notes            TEXT,
    created_at       TEXT,
    updated_at       TEXT
);

CREATE TABLE IF NOT EXISTS job_postings (
    id                        TEXT PRIMARY KEY,
    company_id                TEXT REFERENCES companies(id) ON DELETE SET NULL,
    job_title                 TEXT NOT NULL,
    role_type                 TEXT,
    date_found                TEXT,
    location                  TEXT,
    salary_range              TEXT,
    job_post_url              TEXT,
    required_technical_skills TEXT,
    platform_tool_mentioned   TEXT,
    preferred_skills          TEXT,
    soft_skills_emphasized    TEXT,
    interesting_keywords      TEXT,
    do_you_qualify            TEXT,
    gaps_identified           TEXT,
    apply_status              TEXT,
    notes                     TEXT,
    created_at                TEXT,
    updated_at                TEXT
);

CREATE TABLE IF NOT EXISTS contacts (
    id                    TEXT PRIMARY KEY,
    company_id            TEXT REFERENCES companies(id) ON DELETE SET NULL,
    full_name             TEXT NOT NULL,
    title                 TEXT,
    contact_type          TEXT,
    priority              TEXT,
    linkedin_url          TEXT,
    email                 TEXT,
    connection_degree     TEXT,
    warm_intro_available  INTEGER DEFAULT 0,
    how_you_know_them     TEXT,
    date_connected        TEXT,
    last_touchpoint       TEXT,
    notes_intel           TEXT,
    next_action           TEXT,
    due_date              TEXT,
    created_at            TEXT,
    updated_at            TEXT
);

CREATE TABLE IF NOT EXISTS outreach_log (
    id                    TEXT PRIMARY KEY,
    contact_id            TEXT REFERENCES contacts(id) ON DELETE SET NULL,
    company_id            TEXT REFERENCES companies(id) ON DELETE SET NULL,
    subject_purpose       TEXT NOT NULL,
    date_sent             TEXT,
    channel               TEXT,
    message_type          TEXT,
    personalization_hook  TEXT,
    response_received     INTEGER DEFAULT 0,
    response_date         TEXT,
    response_summary      TEXT,
    follow_up_due         TEXT,
    follow_up_sent        INTEGER DEFAULT 0,
    outcome               TEXT,
    notes                 TEXT,
    created_at            TEXT,
    updated_at            TEXT
);

CREATE TABLE IF NOT EXISTS job_seeker_profile (
    id                 TEXT PRIMARY KEY,
    target_role        TEXT,
    target_salary_min  INTEGER,
    target_salary_max  INTEGER,
    target_location    TEXT,
    relocation_date    TEXT,
    work_authorization TEXT,
    summary            TEXT,
    created_at         TEXT,
    updated_at         TEXT
);

CREATE TABLE IF NOT EXISTS strengths (
    id            TEXT PRIMARY KEY,
    profile_id    TEXT NOT NULL REFERENCES job_seeker_profile(id) ON DELETE CASCADE,
    strength      TEXT NOT NULL,
    talking_point TEXT,
    sort_order    INTEGER DEFAULT 0,
    created_at    TEXT
);

CREATE TABLE IF NOT EXISTS gaps (
    id          TEXT PRIMARY KEY,
    profile_id  TEXT NOT NULL REFERENCES job_seeker_profile(id) ON DELETE CASCADE,
    objection   TEXT NOT NULL,
    rebuttal    TEXT,
    mitigation  TEXT,
    sort_order  INTEGER DEFAULT 0,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


class Database:
    """Manages the SQLite connection and all CRUD operations."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _get_db_path()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ── Generic helpers ──────────────────────────────────────────────

    def _dict_from_row(self, row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
        if row is None:
            return None
        return dict(row)

    def _dicts_from_rows(self, rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
        return [dict(r) for r in rows]

    # ── Companies ────────────────────────────────────────────────────

    def get_companies(self, search: str = "", status_filter: str = "") -> list[dict[str, Any]]:
        sql = "SELECT * FROM companies WHERE 1=1"
        params: list[Any] = []
        if search:
            sql += " AND (company_name LIKE ? OR hq_location LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        if status_filter:
            sql += " AND status = ?"
            params.append(status_filter)
        sql += " ORDER BY updated_at DESC"
        return self._dicts_from_rows(self.conn.execute(sql, params).fetchall())

    def get_company(self, company_id: str) -> Optional[dict[str, Any]]:
        return self._dict_from_row(
            self.conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
        )

    def create_company(self, data: dict[str, Any]) -> str:
        rid = new_id()
        ts = now_iso()
        data = {k: v for k, v in data.items() if v != ""}
        self.conn.execute(
            """INSERT INTO companies (id, company_name, product_platform, tier, status,
               hq_location, remote_posture, company_size, funding_stage, open_role,
               why_you_fit, website_url, careers_url, linkedin_url, last_checked,
               next_action, due_date, notes, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rid, data.get("company_name"), data.get("product_platform"),
             data.get("tier"), data.get("status"), data.get("hq_location"),
             data.get("remote_posture"), data.get("company_size"),
             data.get("funding_stage"), 1 if data.get("open_role") else 0,
             data.get("why_you_fit"), data.get("website_url"),
             data.get("careers_url"), data.get("linkedin_url"),
             data.get("last_checked"), data.get("next_action"),
             data.get("due_date"), data.get("notes"), ts, ts),
        )
        self.conn.commit()
        return rid

    def update_company(self, company_id: str, data: dict[str, Any]) -> None:
        data["updated_at"] = now_iso()
        data["open_role"] = 1 if data.get("open_role") else 0
        cols = ", ".join(f"{k} = ?" for k in data if k != "id")
        vals = [v if v != "" else None for k, v in data.items() if k != "id"]
        vals.append(company_id)
        self.conn.execute(f"UPDATE companies SET {cols} WHERE id = ?", vals)
        self.conn.commit()

    def delete_companies(self, ids: list[str]) -> None:
        placeholders = ",".join("?" * len(ids))
        self.conn.execute(f"DELETE FROM companies WHERE id IN ({placeholders})", ids)
        self.conn.commit()

    def get_company_names(self) -> list[dict[str, str]]:
        rows = self.conn.execute("SELECT id, company_name FROM companies ORDER BY company_name").fetchall()
        return self._dicts_from_rows(rows)

    # ── Job Postings ─────────────────────────────────────────────────

    def get_job_postings(self, search: str = "", status_filter: str = "") -> list[dict[str, Any]]:
        sql = """SELECT jp.*, c.company_name
                 FROM job_postings jp
                 LEFT JOIN companies c ON jp.company_id = c.id
                 WHERE 1=1"""
        params: list[Any] = []
        if search:
            sql += " AND (jp.job_title LIKE ? OR jp.location LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        if status_filter:
            sql += " AND jp.apply_status = ?"
            params.append(status_filter)
        sql += " ORDER BY jp.updated_at DESC"
        return self._dicts_from_rows(self.conn.execute(sql, params).fetchall())

    def get_job_posting(self, post_id: str) -> Optional[dict[str, Any]]:
        return self._dict_from_row(
            self.conn.execute(
                """SELECT jp.*, c.company_name FROM job_postings jp
                   LEFT JOIN companies c ON jp.company_id = c.id
                   WHERE jp.id = ?""", (post_id,)
            ).fetchone()
        )

    def create_job_posting(self, data: dict[str, Any]) -> str:
        rid = new_id()
        ts = now_iso()
        data = {k: (v if v != "" else None) for k, v in data.items()}
        self.conn.execute(
            """INSERT INTO job_postings (id, company_id, job_title, role_type, date_found,
               location, salary_range, job_post_url, required_technical_skills,
               platform_tool_mentioned, preferred_skills, soft_skills_emphasized,
               interesting_keywords, do_you_qualify, gaps_identified, apply_status,
               notes, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rid, data.get("company_id"), data.get("job_title"), data.get("role_type"),
             data.get("date_found"), data.get("location"), data.get("salary_range"),
             data.get("job_post_url"), data.get("required_technical_skills"),
             data.get("platform_tool_mentioned"), data.get("preferred_skills"),
             data.get("soft_skills_emphasized"), data.get("interesting_keywords"),
             data.get("do_you_qualify"), data.get("gaps_identified"),
             data.get("apply_status"), data.get("notes"), ts, ts),
        )
        self.conn.commit()
        return rid

    def update_job_posting(self, post_id: str, data: dict[str, Any]) -> None:
        data["updated_at"] = now_iso()
        cols = ", ".join(f"{k} = ?" for k in data if k != "id")
        vals = [v if v != "" else None for k, v in data.items() if k != "id"]
        vals.append(post_id)
        self.conn.execute(f"UPDATE job_postings SET {cols} WHERE id = ?", vals)
        self.conn.commit()

    def delete_job_postings(self, ids: list[str]) -> None:
        placeholders = ",".join("?" * len(ids))
        self.conn.execute(f"DELETE FROM job_postings WHERE id IN ({placeholders})", ids)
        self.conn.commit()

    def get_job_postings_for_company(self, company_id: str) -> list[dict[str, Any]]:
        return self._dicts_from_rows(
            self.conn.execute(
                "SELECT * FROM job_postings WHERE company_id = ? ORDER BY created_at DESC",
                (company_id,),
            ).fetchall()
        )

    # ── Contacts ─────────────────────────────────────────────────────

    def get_contacts(self, search: str = "", status_filter: str = "") -> list[dict[str, Any]]:
        sql = """SELECT ct.*, c.company_name
                 FROM contacts ct
                 LEFT JOIN companies c ON ct.company_id = c.id
                 WHERE 1=1"""
        params: list[Any] = []
        if search:
            sql += " AND (ct.full_name LIKE ? OR ct.title LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        if status_filter:
            sql += " AND ct.priority = ?"
            params.append(status_filter)
        sql += " ORDER BY ct.updated_at DESC"
        return self._dicts_from_rows(self.conn.execute(sql, params).fetchall())

    def get_contact(self, contact_id: str) -> Optional[dict[str, Any]]:
        return self._dict_from_row(
            self.conn.execute(
                """SELECT ct.*, c.company_name FROM contacts ct
                   LEFT JOIN companies c ON ct.company_id = c.id
                   WHERE ct.id = ?""", (contact_id,)
            ).fetchone()
        )

    def create_contact(self, data: dict[str, Any]) -> str:
        rid = new_id()
        ts = now_iso()
        data = {k: (v if v != "" else None) for k, v in data.items()}
        self.conn.execute(
            """INSERT INTO contacts (id, company_id, full_name, title, contact_type,
               priority, linkedin_url, email, connection_degree, warm_intro_available,
               how_you_know_them, date_connected, last_touchpoint, notes_intel,
               next_action, due_date, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rid, data.get("company_id"), data.get("full_name"), data.get("title"),
             data.get("contact_type"), data.get("priority"), data.get("linkedin_url"),
             data.get("email"), data.get("connection_degree"),
             1 if data.get("warm_intro_available") else 0,
             data.get("how_you_know_them"), data.get("date_connected"),
             data.get("last_touchpoint"), data.get("notes_intel"),
             data.get("next_action"), data.get("due_date"), ts, ts),
        )
        self.conn.commit()
        return rid

    def update_contact(self, contact_id: str, data: dict[str, Any]) -> None:
        data["updated_at"] = now_iso()
        data["warm_intro_available"] = 1 if data.get("warm_intro_available") else 0
        cols = ", ".join(f"{k} = ?" for k in data if k != "id")
        vals = [v if v != "" else None for k, v in data.items() if k != "id"]
        vals.append(contact_id)
        self.conn.execute(f"UPDATE contacts SET {cols} WHERE id = ?", vals)
        self.conn.commit()

    def delete_contacts(self, ids: list[str]) -> None:
        placeholders = ",".join("?" * len(ids))
        self.conn.execute(f"DELETE FROM contacts WHERE id IN ({placeholders})", ids)
        self.conn.commit()

    def get_contact_names(self) -> list[dict[str, str]]:
        rows = self.conn.execute("SELECT id, full_name FROM contacts ORDER BY full_name").fetchall()
        return self._dicts_from_rows(rows)

    def get_contacts_for_company(self, company_id: str) -> list[dict[str, Any]]:
        return self._dicts_from_rows(
            self.conn.execute(
                "SELECT * FROM contacts WHERE company_id = ? ORDER BY created_at DESC",
                (company_id,),
            ).fetchall()
        )

    # ── Outreach Log ─────────────────────────────────────────────────

    def get_outreach(self, search: str = "", status_filter: str = "") -> list[dict[str, Any]]:
        sql = """SELECT o.*, ct.full_name AS contact_name, c.company_name
                 FROM outreach_log o
                 LEFT JOIN contacts ct ON o.contact_id = ct.id
                 LEFT JOIN companies c ON o.company_id = c.id
                 WHERE 1=1"""
        params: list[Any] = []
        if search:
            sql += " AND o.subject_purpose LIKE ?"
            params.append(f"%{search}%")
        if status_filter:
            sql += " AND o.outcome = ?"
            params.append(status_filter)
        sql += " ORDER BY o.updated_at DESC"
        return self._dicts_from_rows(self.conn.execute(sql, params).fetchall())

    def get_outreach_entry(self, entry_id: str) -> Optional[dict[str, Any]]:
        return self._dict_from_row(
            self.conn.execute(
                """SELECT o.*, ct.full_name AS contact_name, c.company_name
                   FROM outreach_log o
                   LEFT JOIN contacts ct ON o.contact_id = ct.id
                   LEFT JOIN companies c ON o.company_id = c.id
                   WHERE o.id = ?""", (entry_id,)
            ).fetchone()
        )

    def create_outreach(self, data: dict[str, Any]) -> str:
        rid = new_id()
        ts = now_iso()
        data = {k: (v if v != "" else None) for k, v in data.items()}
        self.conn.execute(
            """INSERT INTO outreach_log (id, contact_id, company_id, subject_purpose,
               date_sent, channel, message_type, personalization_hook,
               response_received, response_date, response_summary,
               follow_up_due, follow_up_sent, outcome, notes, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rid, data.get("contact_id"), data.get("company_id"),
             data.get("subject_purpose"), data.get("date_sent"), data.get("channel"),
             data.get("message_type"), data.get("personalization_hook"),
             1 if data.get("response_received") else 0, data.get("response_date"),
             data.get("response_summary"), data.get("follow_up_due"),
             1 if data.get("follow_up_sent") else 0,
             data.get("outcome"), data.get("notes"), ts, ts),
        )
        self.conn.commit()
        return rid

    def update_outreach(self, entry_id: str, data: dict[str, Any]) -> None:
        data["updated_at"] = now_iso()
        data["response_received"] = 1 if data.get("response_received") else 0
        data["follow_up_sent"] = 1 if data.get("follow_up_sent") else 0
        cols = ", ".join(f"{k} = ?" for k in data if k != "id")
        vals = [v if v != "" else None for k, v in data.items() if k != "id"]
        vals.append(entry_id)
        self.conn.execute(f"UPDATE outreach_log SET {cols} WHERE id = ?", vals)
        self.conn.commit()

    def delete_outreach(self, ids: list[str]) -> None:
        placeholders = ",".join("?" * len(ids))
        self.conn.execute(f"DELETE FROM outreach_log WHERE id IN ({placeholders})", ids)
        self.conn.commit()

    def get_outreach_for_contact(self, contact_id: str) -> list[dict[str, Any]]:
        return self._dicts_from_rows(
            self.conn.execute(
                """SELECT o.*, c.company_name FROM outreach_log o
                   LEFT JOIN companies c ON o.company_id = c.id
                   WHERE o.contact_id = ? ORDER BY o.created_at DESC""",
                (contact_id,),
            ).fetchall()
        )

    # ── Job Seeker Profile & Gap Analysis ────────────────────────────

    def get_or_create_profile(self) -> dict[str, Any]:
        row = self.conn.execute("SELECT * FROM job_seeker_profile LIMIT 1").fetchone()
        if row:
            return dict(row)
        rid = new_id()
        ts = now_iso()
        self.conn.execute(
            "INSERT INTO job_seeker_profile (id, created_at, updated_at) VALUES (?, ?, ?)",
            (rid, ts, ts),
        )
        self.conn.commit()
        return dict(self.conn.execute("SELECT * FROM job_seeker_profile WHERE id = ?", (rid,)).fetchone())

    def update_profile(self, profile_id: str, data: dict[str, Any]) -> None:
        data["updated_at"] = now_iso()
        cols = ", ".join(f"{k} = ?" for k in data if k != "id")
        vals = [v if v != "" else None for k, v in data.items() if k != "id"]
        vals.append(profile_id)
        self.conn.execute(f"UPDATE job_seeker_profile SET {cols} WHERE id = ?", vals)
        self.conn.commit()

    def get_strengths(self, profile_id: str) -> list[dict[str, Any]]:
        return self._dicts_from_rows(
            self.conn.execute(
                "SELECT * FROM strengths WHERE profile_id = ? ORDER BY sort_order", (profile_id,)
            ).fetchall()
        )

    def create_strength(self, profile_id: str, strength: str = "", talking_point: str = "", sort_order: int = 0) -> str:
        rid = new_id()
        self.conn.execute(
            "INSERT INTO strengths (id, profile_id, strength, talking_point, sort_order, created_at) VALUES (?,?,?,?,?,?)",
            (rid, profile_id, strength, talking_point, sort_order, now_iso()),
        )
        self.conn.commit()
        return rid

    def update_strength(self, strength_id: str, data: dict[str, Any]) -> None:
        cols = ", ".join(f"{k} = ?" for k in data)
        vals = list(data.values()) + [strength_id]
        self.conn.execute(f"UPDATE strengths SET {cols} WHERE id = ?", vals)
        self.conn.commit()

    def delete_strength(self, strength_id: str) -> None:
        self.conn.execute("DELETE FROM strengths WHERE id = ?", (strength_id,))
        self.conn.commit()

    def get_gaps(self, profile_id: str) -> list[dict[str, Any]]:
        return self._dicts_from_rows(
            self.conn.execute(
                "SELECT * FROM gaps WHERE profile_id = ? ORDER BY sort_order", (profile_id,)
            ).fetchall()
        )

    def create_gap(self, profile_id: str, objection: str = "", rebuttal: str = "", mitigation: str = "", sort_order: int = 0) -> str:
        rid = new_id()
        self.conn.execute(
            "INSERT INTO gaps (id, profile_id, objection, rebuttal, mitigation, sort_order, created_at) VALUES (?,?,?,?,?,?,?)",
            (rid, profile_id, objection, rebuttal, mitigation, sort_order, now_iso()),
        )
        self.conn.commit()
        return rid

    def update_gap(self, gap_id: str, data: dict[str, Any]) -> None:
        cols = ", ".join(f"{k} = ?" for k in data)
        vals = list(data.values()) + [gap_id]
        self.conn.execute(f"UPDATE gaps SET {cols} WHERE id = ?", vals)
        self.conn.commit()

    def delete_gap(self, gap_id: str) -> None:
        self.conn.execute("DELETE FROM gaps WHERE id = ?", (gap_id,))
        self.conn.commit()

    # ── Dashboard Queries ────────────────────────────────────────────

    def get_counts(self) -> dict[str, int]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-01")
        return {
            "companies": self.conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0],
            "job_postings": self.conn.execute("SELECT COUNT(*) FROM job_postings").fetchone()[0],
            "contacts": self.conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0],
            "outreach_month": self.conn.execute(
                "SELECT COUNT(*) FROM outreach_log WHERE date_sent >= ?", (today,)
            ).fetchone()[0],
        }

    def get_due_items(self) -> list[dict[str, Any]]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        items: list[dict[str, Any]] = []
        for row in self.conn.execute(
            "SELECT id, company_name AS name, next_action AS action, due_date FROM companies WHERE due_date <= ? AND due_date IS NOT NULL",
            (today,),
        ).fetchall():
            d = dict(row)
            d["type"] = "Company"
            items.append(d)
        for row in self.conn.execute(
            "SELECT id, full_name AS name, next_action AS action, due_date FROM contacts WHERE due_date <= ? AND due_date IS NOT NULL",
            (today,),
        ).fetchall():
            d = dict(row)
            d["type"] = "Contact"
            items.append(d)
        for row in self.conn.execute(
            "SELECT id, subject_purpose AS name, 'Send follow-up' AS action, follow_up_due AS due_date FROM outreach_log WHERE follow_up_due <= ? AND follow_up_sent = 0 AND follow_up_due IS NOT NULL",
            (today,),
        ).fetchall():
            d = dict(row)
            d["type"] = "Outreach"
            items.append(d)
        return sorted(items, key=lambda x: x.get("due_date") or "")

    def get_recent_activity(self, limit: int = 10) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in self.conn.execute(
            "SELECT id, company_name AS name, status, updated_at FROM companies ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall():
            d = dict(row)
            d["type"] = "Company"
            items.append(d)
        for row in self.conn.execute(
            "SELECT id, job_title AS name, apply_status AS status, updated_at FROM job_postings ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall():
            d = dict(row)
            d["type"] = "Job Posting"
            items.append(d)
        items.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
        return items[:limit]

    # ── Settings ─────────────────────────────────────────────────────

    def get_setting(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
        self.conn.commit()

    # ── Bulk table access for export ─────────────────────────────────

    def get_all_rows(self, table: str) -> list[dict[str, Any]]:
        valid_tables = {"companies", "job_postings", "contacts", "outreach_log"}
        if table not in valid_tables:
            return []
        return self._dicts_from_rows(
            self.conn.execute(f"SELECT * FROM {table} ORDER BY created_at DESC").fetchall()
        )

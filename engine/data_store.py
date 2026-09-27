"""Persistence for student profiles, progress, and feedback.

SkillUpStore (SQLite) and SupabaseStore expose the same methods, so the app can
use Supabase when it's configured and fall back to a local SQLite file otherwise.
Profiles belong to an owner_id (the sign-in provider's stable user id), never to
an email address, since unverified sign-ups can claim any email.
"""

import sqlite3
from datetime import datetime, timezone

STUDENT_COLUMNS = "id,name,target_role,skills,owner_email,created_at"
FEEDBACK_COLUMNS = "created_at,user_email,area,page,skill,details,expected,issue_url"


class SkillUpStore:
    def __init__(self, path="skillupindia.db"):
        self.path = path
        with self._connect() as c:
            c.execute("CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,target_role TEXT,skills TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            c.execute("CREATE TABLE IF NOT EXISTS progress(student_id INTEGER,skill TEXT,status TEXT,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(student_id,skill))")
            c.execute("CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY AUTOINCREMENT,area TEXT,page TEXT,skill TEXT,details TEXT,expected TEXT,issue_url TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            # Columns added after the first release; existing local databases get them in place.
            self._add_column(c, "students", "owner_id", "TEXT")
            self._add_column(c, "students", "owner_email", "TEXT")
            self._add_column(c, "feedback", "user_email", "TEXT")

    def _connect(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    @staticmethod
    def _add_column(c, table, column, kind):
        if column not in [row["name"] for row in c.execute(f"PRAGMA table_info({table})")]:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {kind}")

    def add_student(self, owner_id, owner_email, name, role, skills):
        with self._connect() as c:
            return c.execute(
                "INSERT INTO students(owner_id,owner_email,name,target_role,skills) VALUES(?,?,?,?,?)",
                (owner_id, owner_email, name, role, ", ".join(skills)),
            ).lastrowid

    def students(self, owner_id=None):
        """Profiles owned by owner_id, or every profile when owner_id is None (admin view)."""
        with self._connect() as c:
            if owner_id is None:
                rows = c.execute(f"SELECT {STUDENT_COLUMNS} FROM students ORDER BY id DESC")
            else:
                rows = c.execute(f"SELECT {STUDENT_COLUMNS} FROM students WHERE owner_id=? ORDER BY id DESC", (owner_id,))
            return [dict(r) for r in rows]

    def set_progress(self, student_id, skill, status):
        with self._connect() as c:
            c.execute(
                "INSERT INTO progress(student_id,skill,status) VALUES(?,?,?) "
                "ON CONFLICT(student_id,skill) DO UPDATE SET status=excluded.status,updated_at=CURRENT_TIMESTAMP",
                (student_id, skill, status),
            )

    def get_progress(self, student_id):
        with self._connect() as c:
            return [(r["skill"], r["status"]) for r in c.execute("SELECT skill,status FROM progress WHERE student_id=?", (student_id,))]

    def add_feedback(self, area, page, skill, details, expected, issue_url, user_email):
        with self._connect() as c:
            return c.execute(
                "INSERT INTO feedback(area,page,skill,details,expected,issue_url,user_email) VALUES(?,?,?,?,?,?,?)",
                (area, page, skill, details, expected, issue_url, user_email),
            ).lastrowid

    def feedback(self):
        with self._connect() as c:
            return [dict(r) for r in c.execute(f"SELECT {FEEDBACK_COLUMNS} FROM feedback ORDER BY id DESC")]


class SupabaseStore:
    """Supabase tables through PostgREST, using the service-role key from the server.

    The tables have row-level security enabled with no policies (see
    supabase/schema.sql), so only this server-side key can read or write them.
    """

    def __init__(self, url, service_role_key):
        from postgrest import SyncPostgrestClient

        headers = {"apikey": service_role_key, "Accept": "application/json", "Content-Type": "application/json"}
        # Legacy service_role keys are JWTs and also go in Authorization; the newer
        # sb_secret_ keys are not JWTs and must only be sent as the apikey header.
        if service_role_key.startswith("eyJ"):
            headers["Authorization"] = f"Bearer {service_role_key}"
        self.db = SyncPostgrestClient(f"{url.rstrip('/')}/rest/v1", headers=headers, timeout=10)

    def add_student(self, owner_id, owner_email, name, role, skills):
        rows = self.db.from_("students").insert({
            "owner_id": owner_id, "owner_email": owner_email, "name": name,
            "target_role": role, "skills": ", ".join(skills),
        }).execute().data
        return rows[0]["id"]

    def students(self, owner_id=None):
        query = self.db.from_("students").select(STUDENT_COLUMNS)
        if owner_id is not None:
            query = query.eq("owner_id", owner_id)
        return query.order("id", desc=True).execute().data

    def set_progress(self, student_id, skill, status):
        self.db.from_("progress").upsert(
            {"student_id": student_id, "skill": skill, "status": status,
             "updated_at": datetime.now(timezone.utc).isoformat()},
            on_conflict="student_id,skill",
        ).execute()

    def get_progress(self, student_id):
        rows = self.db.from_("progress").select("skill,status").eq("student_id", student_id).execute().data
        return [(r["skill"], r["status"]) for r in rows]

    def add_feedback(self, area, page, skill, details, expected, issue_url, user_email):
        rows = self.db.from_("feedback").insert({
            "area": area, "page": page, "skill": skill, "details": details,
            "expected": expected, "issue_url": issue_url, "user_email": user_email,
        }).execute().data
        return rows[0]["id"]

    def feedback(self):
        return self.db.from_("feedback").select(FEEDBACK_COLUMNS).order("id", desc=True).execute().data

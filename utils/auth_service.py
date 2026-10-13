import os
import sqlite3
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "auth.db")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db():
    """Initialize SQLite database for user auth and session persistence."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                company TEXT,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.commit()

        now_str = _utcnow().isoformat()

        # Seed default demo user if not present
        cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@competitor.ai",))
        if not cursor.fetchone():
            demo_salt = secrets.token_hex(16)
            demo_hash = _hash_password("password123", demo_salt)
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, full_name, company, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "demo-user-id",
                "demo@competitor.ai",
                f"{demo_salt}${demo_hash}",
                "Demo Intelligence Analyst",
                "Alpha Ventures",
                now_str
            ))

        # Seed admin user
        cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@competitor.ai",))
        if not cursor.fetchone():
            admin_salt = secrets.token_hex(16)
            admin_hash = _hash_password("admin123", admin_salt)
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, full_name, company, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "admin-user-id",
                "admin@competitor.ai",
                f"{admin_salt}${admin_hash}",
                "Strategic Intelligence Lead",
                "Competitor AI Global",
                now_str
            ))

        # Ensure test user exists for backward compatibility
        cursor.execute("SELECT id FROM users WHERE id = ?", ("test",))
        if not cursor.fetchone():
            test_salt = secrets.token_hex(16)
            test_hash = _hash_password("testpass", test_salt)
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, full_name, company, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "test",
                "test@competitor.ai",
                f"{test_salt}${test_hash}",
                "Test Engineer",
                "Quality Labs",
                now_str
            ))

        conn.commit()


def _hash_password(password: str, salt: str) -> str:
    """PBKDF2 HMAC SHA-256 password hashing with 100,000 iterations."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()


def verify_password(plain_password: str, stored_hash_str: str) -> bool:
    try:
        salt, expected_hash = stored_hash_str.split("$", 1)
        computed = _hash_password(plain_password, salt)
        return hmac.compare_digest(computed, expected_hash)
    except Exception:
        return False


def register_user(email: str, password: str, full_name: str, company: str = "") -> Tuple[Dict[str, Any], str]:
    """Register a new user and generate a session token."""
    email_clean = email.strip().lower()
    if not email_clean or "@" not in email_clean:
        raise ValueError("A valid email address is required")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    if not full_name.strip():
        raise ValueError("Full name is required")

    init_auth_db()

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
        if cursor.fetchone():
            raise ValueError("An account with this email already exists. Please log in.")

        user_id = str(uuid.uuid4())
        salt = secrets.token_hex(16)
        pwd_hash = _hash_password(password, salt)
        now_dt = _utcnow()
        now_str = now_dt.isoformat()
        expires_at = (now_dt + timedelta(days=14)).isoformat()

        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, company, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, email_clean, f"{salt}${pwd_hash}", full_name.strip(), company.strip(), now_str))

        token = secrets.token_urlsafe(32)
        cursor.execute("""
            INSERT INTO sessions (token, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, (token, user_id, now_str, expires_at))

        conn.commit()

        user_data = {
            "id": user_id,
            "email": email_clean,
            "full_name": full_name.strip(),
            "company": company.strip(),
            "created_at": now_str
        }
        return user_data, token


def login_user(email: str, password: str) -> Tuple[Dict[str, Any], str]:
    """Authenticate an existing user and create a session token."""
    email_clean = email.strip().lower()
    init_auth_db()

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email_clean,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Invalid email or password")

        if not verify_password(password, row["password_hash"]):
            raise ValueError("Invalid email or password")

        user_id = row["id"]
        token = secrets.token_urlsafe(32)
        now_dt = _utcnow()
        now_str = now_dt.isoformat()
        expires_at = (now_dt + timedelta(days=14)).isoformat()

        cursor.execute("""
            INSERT INTO sessions (token, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, (token, user_id, now_str, expires_at))
        conn.commit()

        user_data = {
            "id": user_id,
            "email": row["email"],
            "full_name": row["full_name"],
            "company": row["company"] or "",
            "created_at": row["created_at"]
        }
        return user_data, token


def verify_session(token: str) -> Optional[Dict[str, Any]]:
    """Validate session token and return user dictionary if active."""
    if not token:
        return None
    init_auth_db()

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.expires_at, u.id, u.email, u.full_name, u.company, u.created_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """, (token,))
        row = cursor.fetchone()
        if not row:
            return None

        # Check expiration
        expires_str = row["expires_at"]
        try:
            expires_dt = datetime.fromisoformat(expires_str)
            # Ensure timezone awareness for comparison
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=timezone.utc)
            if _utcnow() > expires_dt:
                cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
                return None
        except Exception:
            pass

        return {
            "id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"],
            "company": row["company"] or "",
            "created_at": row["created_at"]
        }


def delete_session(token: str) -> bool:
    """Invalidate and remove session token."""
    if not token:
        return True
    init_auth_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        return True


def user_exists_by_id(user_id: str) -> bool:
    """Check if user_id exists in SQLite auth database."""
    if not user_id:
        return False
    init_auth_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone() is not None

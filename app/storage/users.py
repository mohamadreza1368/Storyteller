import os
import json
import uuid
import secrets
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.storage.database import db

class User(BaseModel):
    id: str = Field(default_factory=lambda: f"usr_{uuid.uuid4().hex[:10]}")
    username: str
    email: str
    password_hash: str
    salt: str
    full_name: str
    role: str = "user"  # "admin" or "user"
    status: str = "active"  # "active" or "suspended"
    avatar_url: Optional[str] = None
    bio: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None
    favorite_books: List[str] = Field(default_factory=list)
    favorite_movies: List[str] = Field(default_factory=list)
    cultural_taste: Dict[str, Any] = Field(default_factory=dict)

class UserPublic(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    status: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = ""
    created_at: str
    last_login: Optional[str] = None
    novels_count: int = 0
    favorite_books: List[str] = Field(default_factory=list)
    favorite_movies: List[str] = Field(default_factory=list)
    cultural_taste: Dict[str, Any] = Field(default_factory=dict)

class UserManager:
    def __init__(self):
        self._migrate_json_if_needed()
        self._ensure_initial_admin()

    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Cryptographically secure PBKDF2-HMAC-SHA256 password hashing with 600,000 iterations."""
        if not salt:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=600000
        ).hex()
        return pwd_hash, salt

    def _verify_password(self, password: str, salt: str, expected_hash: str) -> bool:
        """Constant-time password comparison to resist timing attacks."""
        # Check standard 600,000 iterations
        computed_hash, _ = self._hash_password(password, salt)
        if hmac.compare_digest(computed_hash, expected_hash):
            return True
        # Compatibility check for legacy 100,000 iterations
        legacy_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100000
        ).hex()
        return hmac.compare_digest(legacy_hash, expected_hash)

    def _migrate_json_if_needed(self):
        """Seamlessly migrates legacy users.json and sessions.json to SQLite on first startup."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        users_file = os.path.join(base, "data", "users.json")
        sessions_file = os.path.join(base, "data", "sessions.json")

        if os.path.exists(users_file):
            try:
                with open(users_file, "r", encoding="utf-8") as f:
                    users_data = json.load(f)
                with db.get_connection() as conn:
                    for u in users_data.values():
                        conn.execute("""
                            INSERT OR IGNORE INTO users 
                            (id, username, email, password_hash, salt, full_name, role, status, avatar_url, bio, created_at, last_login)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            u.get("id"),
                            u.get("username"),
                            u.get("email"),
                            u.get("password_hash"),
                            u.get("salt"),
                            u.get("full_name", ""),
                            u.get("role", "user"),
                            u.get("status", "active"),
                            u.get("avatar_url"),
                            u.get("bio", ""),
                            u.get("created_at") or datetime.now(timezone.utc).isoformat(),
                            u.get("last_login")
                        ))
            except Exception:
                pass

        if os.path.exists(sessions_file):
            try:
                with open(sessions_file, "r", encoding="utf-8") as f:
                    sessions_data = json.load(f)
                with db.get_connection() as conn:
                    now = datetime.now(timezone.utc).isoformat()
                    for token, user_id in sessions_data.items():
                        conn.execute("""
                            INSERT OR IGNORE INTO sessions (token, user_id, created_at, expires_at)
                            VALUES (?, ?, ?, ?)
                        """, (token, user_id, now, None))
            except Exception:
                pass

    def _ensure_initial_admin(self):
        """Creates the initial admin account if no admin accounts exist."""
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cursor.fetchone()[0]
            if admin_count == 0:
                initial_pwd = os.environ.get("STORYTELLER_ADMIN_PASSWORD") or os.environ.get("ADMIN_INITIAL_PASSWORD")
                if not initial_pwd:
                    initial_pwd = secrets.token_urlsafe(12)
                    logger.info(f"Initialized platform administrator. Initial admin password: {initial_pwd}")
                else:
                    logger.info("Initialized platform administrator using configured environment password.")

                pwd_hash, salt = self._hash_password(initial_pwd)
                admin_id = "usr_admin001"
                now = datetime.now(timezone.utc).isoformat()
                conn.execute("""
                    INSERT OR IGNORE INTO users 
                    (id, username, email, password_hash, salt, full_name, role, status, avatar_url, bio, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    admin_id,
                    "admin",
                    "admin@storyteller.ai",
                    pwd_hash,
                    salt,
                    "Platform Administrator",
                    "admin",
                    "active",
                    None,
                    "System superuser managing AI models, API keys, and authors.",
                    now
                ))

    def _dict_to_user(self, d: dict) -> User:
        """Helper to unpack JSON fields into structured list and dict attributes."""
        raw = dict(d)
        if "favorite_books_json" in raw:
            try:
                raw["favorite_books"] = json.loads(raw["favorite_books_json"] or "[]")
            except Exception:
                raw["favorite_books"] = []
        if "favorite_movies_json" in raw:
            try:
                raw["favorite_movies"] = json.loads(raw["favorite_movies_json"] or "[]")
            except Exception:
                raw["favorite_movies"] = []
        if "cultural_taste_json" in raw:
            try:
                raw["cultural_taste"] = json.loads(raw["cultural_taste_json"] or "{}")
            except Exception:
                raw["cultural_taste"] = {}
        return User.model_validate(raw)

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: str,
        role: str = "user",
        favorite_books: Optional[List[str]] = None,
        favorite_movies: Optional[List[str]] = None,
        cultural_taste: Optional[Dict[str, Any]] = None
    ) -> Optional[User]:
        email_clean = email.strip().lower()
        username_clean = username.strip().lower()

        with db.get_connection() as conn:
            # Check unique constraints
            c = conn.execute("SELECT id FROM users WHERE lower(email) = ?", (email_clean,))
            if c.fetchone():
                raise ValueError("An account with this email address already exists.")
            
            c = conn.execute("SELECT id FROM users WHERE lower(username) = ?", (username_clean,))
            if c.fetchone():
                raise ValueError("This username is already taken.")

            pwd_hash, salt = self._hash_password(password)
            user_id = f"usr_{uuid.uuid4().hex[:10]}"
            now = datetime.now(timezone.utc).isoformat()
            full_name_clean = full_name.strip() or username_clean

            books_list = [b.strip() for b in (favorite_books or []) if b and b.strip()][:5]
            movies_list = [m.strip() for m in (favorite_movies or []) if m and m.strip()][:5]
            taste_dict = cultural_taste or {}

            conn.execute("""
                INSERT INTO users 
                (id, username, email, password_hash, salt, full_name, role, status, bio, created_at,
                 favorite_books_json, favorite_movies_json, cultural_taste_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                username_clean,
                email_clean,
                pwd_hash,
                salt,
                full_name_clean,
                role,
                "active",
                "",
                now,
                json.dumps(books_list, ensure_ascii=False),
                json.dumps(movies_list, ensure_ascii=False),
                json.dumps(taste_dict, ensure_ascii=False)
            ))

            return User(
                id=user_id,
                username=username_clean,
                email=email_clean,
                password_hash=pwd_hash,
                salt=salt,
                full_name=full_name_clean,
                role=role,
                status="active",
                created_at=now,
                favorite_books=books_list,
                favorite_movies=movies_list,
                cultural_taste=taste_dict
            )

    def authenticate(self, email_or_username: str, password: str) -> Optional[tuple[User, str]]:
        query = email_or_username.strip().lower()
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM users 
                WHERE lower(email) = ? OR lower(username) = ?
            """, (query, query))
            row = cursor.fetchone()
            if not row:
                return None

            user_dict = dict(row)
            if user_dict.get("status") == "suspended":
                raise ValueError("Your account has been suspended. Please contact the platform administrator.")

            if not self._verify_password(password, user_dict["salt"], user_dict["password_hash"]):
                return None

            now = datetime.now(timezone.utc).isoformat()
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user_dict["id"]))

            token = secrets.token_urlsafe(32)
            conn.execute("""
                INSERT INTO sessions (token, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            """, (token, user_dict["id"], now, None))

            user_dict["last_login"] = now
            return self._dict_to_user(user_dict), token

    def get_user_by_token(self, token: str) -> Optional[User]:
        if not token:
            return None
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT u.* FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.token = ?
            """, (token,))
            row = cursor.fetchone()
            if row:
                return self._dict_to_user(dict(row))
        return None

    def revoke_token(self, token: str):
        if not token:
            return
        with db.get_connection() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return self._dict_to_user(dict(row))
        return None

    def list_users(self) -> List[User]:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users ORDER BY created_at ASC")
            return [self._dict_to_user(dict(row)) for row in cursor.fetchall()]

    def update_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        bio: Optional[str] = None,
        new_password: Optional[str] = None,
        favorite_books: Optional[List[str]] = None,
        favorite_movies: Optional[List[str]] = None,
        cultural_taste: Optional[Dict[str, Any]] = None
    ) -> Optional[User]:
        u = self.get_user_by_id(user_id)
        if not u:
            return None

        update_fields = []
        params = []
        if full_name is not None:
            update_fields.append("full_name = ?")
            params.append(full_name.strip())
        if bio is not None:
            update_fields.append("bio = ?")
            params.append(bio.strip())
        if new_password:
            pwd_hash, salt = self._hash_password(new_password)
            update_fields.append("password_hash = ?")
            params.append(pwd_hash)
            update_fields.append("salt = ?")
            params.append(salt)
        if favorite_books is not None:
            books_list = [b.strip() for b in favorite_books if b and b.strip()][:5]
            update_fields.append("favorite_books_json = ?")
            params.append(json.dumps(books_list, ensure_ascii=False))
        if favorite_movies is not None:
            movies_list = [m.strip() for m in favorite_movies if m and m.strip()][:5]
            update_fields.append("favorite_movies_json = ?")
            params.append(json.dumps(movies_list, ensure_ascii=False))
        if cultural_taste is not None:
            update_fields.append("cultural_taste_json = ?")
            params.append(json.dumps(cultural_taste, ensure_ascii=False))

        if update_fields:
            params.append(user_id)
            with db.get_connection() as conn:
                conn.execute(f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?", tuple(params))

        return self.get_user_by_id(user_id)

    def update_status(self, user_id: str, status: str) -> Optional[User]:
        with db.get_connection() as conn:
            conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
        return self.get_user_by_id(user_id)

    def reset_password(self, user_id: str, new_password: str) -> Optional[User]:
        return self.update_profile(user_id, new_password=new_password)

    def delete_user(self, user_id: str) -> bool:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False

            if row["role"] == "admin":
                c = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
                if c.fetchone()[0] <= 1:
                    raise ValueError("Cannot delete the only administrator account.")

            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return True

user_manager = UserManager()

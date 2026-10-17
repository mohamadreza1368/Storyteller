import os
import json
import uuid
import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

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

class UserManager:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Default to data/ directory relative to project root
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(base, "data")
        else:
            self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.sessions_file = os.path.join(self.data_dir, "sessions.json")
        self._ensure_initial_admin()

    def _hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        if not salt:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100000
        ).hex()
        return pwd_hash, salt

    def _load_users(self) -> Dict[str, dict]:
        if not os.path.exists(self.users_file):
            return {}
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_users(self, users: Dict[str, dict]):
        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

    def _load_sessions(self) -> Dict[str, str]:
        """Maps token -> user_id"""
        if not os.path.exists(self.sessions_file):
            return {}
        try:
            with open(self.sessions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_sessions(self, sessions: Dict[str, str]):
        with open(self.sessions_file, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)

    def _ensure_initial_admin(self):
        """Creates the default admin account if no users exist."""
        users = self._load_users()
        admin_exists = any(u.get("role") == "admin" for u in users.values())
        if not admin_exists:
            pwd_hash, salt = self._hash_password("admin123")
            admin_user = User(
                id="usr_admin001",
                username="admin",
                email="admin@storyteller.ai",
                password_hash=pwd_hash,
                salt=salt,
                full_name="Platform Administrator",
                role="admin",
                status="active",
                bio="System superuser managing AI models, API keys, and authors."
            )
            users[admin_user.id] = admin_user.model_dump()
            self._save_users(users)

    def create_user(self, email: str, username: str, password: str, full_name: str, role: str = "user") -> Optional[User]:
        users = self._load_users()
        email_clean = email.strip().lower()
        username_clean = username.strip().lower()

        # Check existing
        for u in users.values():
            if u.get("email", "").lower() == email_clean:
                raise ValueError("An account with this email address already exists.")
            if u.get("username", "").lower() == username_clean:
                raise ValueError("This username is already taken.")

        pwd_hash, salt = self._hash_password(password)
        new_user = User(
            username=username_clean,
            email=email_clean,
            password_hash=pwd_hash,
            salt=salt,
            full_name=full_name.strip() or username_clean,
            role=role,
            status="active"
        )
        users[new_user.id] = new_user.model_dump()
        self._save_users(users)
        return new_user

    def authenticate(self, email_or_username: str, password: str) -> Optional[tuple[User, str]]:
        users = self._load_users()
        query = email_or_username.strip().lower()
        matched = None
        for u in users.values():
            if u.get("email", "").lower() == query or u.get("username", "").lower() == query:
                matched = u
                break
        
        if not matched:
            return None
        
        if matched.get("status") == "suspended":
            raise ValueError("Your account has been suspended. Please contact the platform administrator.")

        pwd_hash, _ = self._hash_password(password, matched["salt"])
        if pwd_hash != matched["password_hash"]:
            return None

        # Record login time
        matched["last_login"] = datetime.now(timezone.utc).isoformat()
        users[matched["id"]] = matched
        self._save_users(users)

        # Issue session token
        token = secrets.token_urlsafe(32)
        sessions = self._load_sessions()
        sessions[token] = matched["id"]
        self._save_sessions(sessions)

        return User.model_validate(matched), token

    def get_user_by_token(self, token: str) -> Optional[User]:
        if not token:
            return None
        sessions = self._load_sessions()
        user_id = sessions.get(token)
        if not user_id:
            return None
        return self.get_user_by_id(user_id)

    def revoke_token(self, token: str):
        sessions = self._load_sessions()
        if token in sessions:
            del sessions[token]
            self._save_sessions(sessions)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        users = self._load_users()
        data = users.get(user_id)
        if data:
            return User.model_validate(data)
        return None

    def list_users(self) -> List[User]:
        users = self._load_users()
        return [User.model_validate(u) for u in users.values()]

    def update_profile(self, user_id: str, full_name: Optional[str] = None, bio: Optional[str] = None, new_password: Optional[str] = None) -> Optional[User]:
        users = self._load_users()
        if user_id not in users:
            return None
        u = users[user_id]
        if full_name is not None:
            u["full_name"] = full_name.strip()
        if bio is not None:
            u["bio"] = bio.strip()
        if new_password:
            pwd_hash, salt = self._hash_password(new_password)
            u["password_hash"] = pwd_hash
            u["salt"] = salt
        users[user_id] = u
        self._save_users(users)
        return User.model_validate(u)

    def update_status(self, user_id: str, status: str) -> Optional[User]:
        users = self._load_users()
        if user_id not in users:
            return None
        u = users[user_id]
        u["status"] = status
        users[user_id] = u
        self._save_users(users)
        return User.model_validate(u)

    def reset_password(self, user_id: str, new_password: str) -> Optional[User]:
        return self.update_profile(user_id, new_password=new_password)

    def delete_user(self, user_id: str) -> bool:
        users = self._load_users()
        if user_id not in users:
            return False
        # Do not allow deleting the main admin
        if users[user_id].get("role") == "admin" and len([u for u in users.values() if u.get("role") == "admin"]) <= 1:
            raise ValueError("Cannot delete the only administrator account.")
        del users[user_id]
        self._save_users(users)

        # Clear any active sessions
        sessions = self._load_sessions()
        sessions = {tok: uid for tok, uid in sessions.items() if uid != user_id}
        self._save_sessions(sessions)
        return True

user_manager = UserManager()

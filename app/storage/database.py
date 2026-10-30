import os
import sqlite3
import json
import logging
from typing import Optional, Generator
from contextlib import contextmanager
from app.config import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = settings.db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provides a managed SQLite connection configured for concurrency, integrity, and safety."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initializes relational schema with strict types, constraints, and indexes."""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    status TEXT NOT NULL DEFAULT 'active',
                    avatar_url TEXT,
                    bio TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    favorite_books_json TEXT DEFAULT '[]',
                    favorite_movies_json TEXT DEFAULT '[]',
                    cultural_taste_json TEXT DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

                CREATE TABLE IF NOT EXISTS novels (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    working_title TEXT,
                    premise TEXT,
                    logline TEXT,
                    synopsis TEXT,
                    hook TEXT,
                    genre TEXT,
                    theme TEXT,
                    tone TEXT,
                    prose_style TEXT,
                    perspective TEXT,
                    ending_style TEXT,
                    city TEXT,
                    country TEXT,
                    era TEXT,
                    story_time_span TEXT,
                    total_episodes INTEGER NOT NULL DEFAULT 4,
                    words_per_episode INTEGER NOT NULL DEFAULT 1800,
                    auto_continue INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'Draft',
                    created_at_utc TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL,
                    owner_id TEXT REFERENCES users(id) ON DELETE SET NULL,
                    owner_name TEXT,
                    blueprint_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_novels_owner_id ON novels(owner_id);
                CREATE INDEX IF NOT EXISTS idx_novels_updated_at ON novels(updated_at_utc DESC);

                CREATE TABLE IF NOT EXISTS story_matrix (
                    novel_id TEXT PRIMARY KEY REFERENCES novels(id) ON DELETE CASCADE,
                    matrix_json TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS story_memory (
                    novel_id TEXT PRIMARY KEY REFERENCES novels(id) ON DELETE CASCADE,
                    memory_json TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS episodes (
                    novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                    episode_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT,
                    content TEXT NOT NULL,
                    word_count INTEGER NOT NULL DEFAULT 0,
                    pov_character TEXT,
                    image_url TEXT,
                    created_at_utc TEXT NOT NULL,
                    scenes_json TEXT,
                    PRIMARY KEY (novel_id, episode_number)
                );
                CREATE INDEX IF NOT EXISTS idx_episodes_novel ON episodes(novel_id, episode_number);

                CREATE TABLE IF NOT EXISTS episode_images (
                    novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                    episode_number INTEGER NOT NULL,
                    image_data BLOB NOT NULL,
                    mime_type TEXT NOT NULL DEFAULT 'image/jpeg',
                    created_at_utc TEXT NOT NULL,
                    PRIMARY KEY (novel_id, episode_number)
                );

                CREATE TABLE IF NOT EXISTS generation_progress (
                    novel_id TEXT PRIMARY KEY REFERENCES novels(id) ON DELETE CASCADE,
                    status TEXT NOT NULL,
                    current_step TEXT NOT NULL,
                    step_number INTEGER NOT NULL DEFAULT 0,
                    total_steps INTEGER NOT NULL DEFAULT 6,
                    percentage INTEGER NOT NULL DEFAULT 0,
                    current_episode INTEGER NOT NULL DEFAULT 0,
                    total_episodes INTEGER NOT NULL DEFAULT 4,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    progress_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL
                );
            """)

            # Automatic column migration for existing user databases
            try:
                conn.execute("ALTER TABLE episodes ADD COLUMN scenes_json TEXT;")
            except sqlite3.OperationalError:
                pass

            for col_name, col_type, default_val in [
                ("favorite_books_json", "TEXT", "'[]'"),
                ("favorite_movies_json", "TEXT", "'[]'"),
                ("cultural_taste_json", "TEXT", "'{}'")
            ]:
                try:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type} DEFAULT {default_val};")
                except sqlite3.OperationalError:
                    pass

db = Database()

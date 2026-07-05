"""SQLite database connection manager and schema DDL."""

import sqlite3
import os
from pathlib import Path
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_SQL = """
-- Table: research_sessions
CREATE TABLE IF NOT EXISTS research_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    topic TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    paper_count INTEGER DEFAULT 0,
    summary TEXT DEFAULT '',
    error_message TEXT DEFAULT '',
    api_task_id TEXT DEFAULT ''
);

-- Table: working_memory_entries
CREATE TABLE IF NOT EXISTS working_memory_entries (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    node_name TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    input_preview TEXT DEFAULT '',
    output_preview TEXT DEFAULT '',
    input_token_count INTEGER DEFAULT 0,
    output_token_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES research_sessions(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_wme_session ON working_memory_entries(session_id, step_number);

-- Table: paper_analyses (knowledge persists independently of session lifecycle)
CREATE TABLE IF NOT EXISTS paper_analyses (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    paper_title TEXT NOT NULL,
    paper_url TEXT DEFAULT '',
    problem TEXT DEFAULT '',
    method TEXT DEFAULT '',
    dataset TEXT DEFAULT '',
    metric TEXT DEFAULT '',
    results TEXT DEFAULT '{}',
    limitation TEXT DEFAULT '',
    contribution TEXT DEFAULT '',
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pa_session ON paper_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_pa_title ON paper_analyses(paper_title);

-- FTS5 virtual table for full-text search on paper analyses
CREATE VIRTUAL TABLE IF NOT EXISTS paper_analyses_fts USING fts5(
    paper_title, problem, method, dataset, limitation, contribution,
    content='paper_analyses',
    content_rowid='rowid'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS pa_ai AFTER INSERT ON paper_analyses BEGIN
    INSERT INTO paper_analyses_fts(rowid, paper_title, problem, method, dataset, limitation, contribution)
    VALUES (new.rowid, new.paper_title, new.problem, new.method, new.dataset, new.limitation, new.contribution);
END;

CREATE TRIGGER IF NOT EXISTS pa_ad AFTER DELETE ON paper_analyses BEGIN
    INSERT INTO paper_analyses_fts(paper_analyses_fts, rowid, paper_title, problem, method, dataset, limitation, contribution)
    VALUES ('delete', old.rowid, old.paper_title, old.problem, old.method, old.dataset, old.limitation, old.contribution);
END;

CREATE TRIGGER IF NOT EXISTS pa_au AFTER UPDATE ON paper_analyses BEGIN
    INSERT INTO paper_analyses_fts(paper_analyses_fts, rowid, paper_title, problem, method, dataset, limitation, contribution)
    VALUES ('delete', old.rowid, old.paper_title, old.problem, old.method, old.dataset, old.limitation, old.contribution);
    INSERT INTO paper_analyses_fts(rowid, paper_title, problem, method, dataset, limitation, contribution)
    VALUES (new.rowid, new.paper_title, new.problem, new.method, new.dataset, new.limitation, new.contribution);
END;

-- Table: llm_cache
CREATE TABLE IF NOT EXISTS llm_cache (
    id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    system_prompt TEXT DEFAULT '',
    user_prompt TEXT DEFAULT '',
    response_text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    hit_count INTEGER DEFAULT 1,
    last_accessed TIMESTAMP NOT NULL,
    UNIQUE(model_name, prompt_hash)
);
CREATE INDEX IF NOT EXISTS idx_cache_lookup ON llm_cache(model_name, prompt_hash);

-- Table: user_preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
"""


class Database:
    """Manages the SQLite connection and schema lifecycle."""

    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = self._connect()
        return self._conn

    def _connect(self) -> sqlite3.Connection:
        # Resolve path relative to the backend directory if not absolute
        path = Path(self.db_path)
        if not path.is_absolute():
            # If running from backend/, db_path is relative
            path = Path.cwd() / path

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        logger.info(f"Connected to SQLite database: {path}")
        return conn

    def init_schema(self) -> None:
        """Create all tables if they don't exist."""
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()
        logger.info("Database schema initialized.")

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed.")

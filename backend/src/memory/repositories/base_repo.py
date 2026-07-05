"""Generic CRUD base repository."""

import sqlite3
from typing import Optional, List, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseRepo:
    """Base repository with common SQLite CRUD operations."""

    def __init__(self, db: "Database"):  # type: ignore[name-defined] # noqa: F821
        self.db = db

    @property
    def conn(self) -> sqlite3.Connection:
        return self.db.conn

    def insert(self, table: str, data: Dict[str, Any]) -> str:
        """Insert a row and return the id."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.conn.execute(sql, list(data.values()))
        self.conn.commit()
        return data.get("id", "")

    def get_by_id(self, table: str, id_value: str, id_column: str = "id") -> Optional[sqlite3.Row]:
        """Get a single row by its id column."""
        sql = f"SELECT * FROM {table} WHERE {id_column} = ?"
        return self.conn.execute(sql, (id_value,)).fetchone()

    def list_all(
        self,
        table: str,
        order_by: str = "created_at DESC",
        limit: int = 50,
        offset: int = 0,
        where: str = "",
        params: tuple = (),
    ) -> List[sqlite3.Row]:
        """List rows with optional filtering."""
        sql = f"SELECT * FROM {table}"
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        sql += f" LIMIT ? OFFSET ?"
        all_params = params + (limit, offset)
        return self.conn.execute(sql, all_params).fetchall()

    def update(self, table: str, id_value: str, data: Dict[str, Any], id_column: str = "id") -> bool:
        """Update a row by id. Returns True if a row was affected."""
        set_clause = ", ".join(f"{k} = ?" for k in data)
        values = list(data.values()) + [id_value]
        sql = f"UPDATE {table} SET {set_clause} WHERE {id_column} = ?"
        cursor = self.conn.execute(sql, values)
        self.conn.commit()
        return cursor.rowcount > 0

    def delete(self, table: str, id_value: str, id_column: str = "id") -> bool:
        """Delete a row by id. Returns True if a row was affected."""
        sql = f"DELETE FROM {table} WHERE {id_column} = ?"
        cursor = self.conn.execute(sql, (id_value,))
        self.conn.commit()
        return cursor.rowcount > 0

    def count(self, table: str, where: str = "", params: tuple = ()) -> int:
        """Count rows with optional filtering."""
        sql = f"SELECT COUNT(*) FROM {table}"
        if where:
            sql += f" WHERE {where}"
        row = self.conn.execute(sql, params).fetchone()
        return row[0] if row else 0

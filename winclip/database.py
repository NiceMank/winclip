"""Gestion du stockage local SQLite pour WinClip."""
import json
import sqlite3
import time
from typing import Any, Optional
from .config import DB_PATH, MAX_HISTORY_ITEMS


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    is_pinned INTEGER DEFAULT 0,
                    thumbnail_path TEXT,
                    metadata_json TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_updated_at ON clips(updated_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_pinned ON clips(is_pinned)")
            conn.commit()

    def add_clip(self, content: str, content_type: str, metadata: dict, thumbnail_path: Optional[str] = None) -> int:
        """Ajoute un élément ou le remonte au sommet s'il existe déjà."""
        now = time.time()
        meta_str = json.dumps(metadata)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Vérifier si un clip identique existe déjà
            cursor.execute("SELECT id, is_pinned FROM clips WHERE content = ?", (content,))
            row = cursor.fetchone()

            if row:
                clip_id = row["id"]
                # Mettre à jour l'horodatage pour remonter au début
                cursor.execute("""
                    UPDATE clips
                    SET updated_at = ?, metadata_json = ?, thumbnail_path = COALESCE(?, thumbnail_path)
                    WHERE id = ?
                """, (now, meta_str, thumbnail_path, clip_id))
            else:
                cursor.execute("""
                    INSERT INTO clips (content, content_type, is_pinned, thumbnail_path, metadata_json, created_at, updated_at)
                    VALUES (?, ?, 0, ?, ?, ?, ?)
                """, (content, content_type, thumbnail_path, meta_str, now, now))
                clip_id = cursor.lastrowid

            conn.commit()

        self.cleanup_old_items()
        return clip_id

    def get_clips(self, search: Optional[str] = None, only_pinned: bool = False, limit: int = 100) -> list[dict]:
        """Récupère les éléments filtrés par recherche ou favoris."""
        query = "SELECT * FROM clips WHERE 1=1"
        params: list[Any] = []

        if only_pinned:
            query += " AND is_pinned = 1"

        if search:
            query += " AND content LIKE ?"
            params.append(f"%{search}%")

        query += " ORDER BY is_pinned DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for r in rows:
                item = dict(r)
                item["metadata"] = json.loads(item["metadata_json"]) if item["metadata_json"] else {}
                results.append(item)
            return results

    def toggle_pin(self, clip_id: int) -> bool:
        """Inverse l'état épinglé d'un élément."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_pinned FROM clips WHERE id = ?", (clip_id,))
            row = cursor.fetchone()
            if not row:
                return False

            new_state = 0 if row["is_pinned"] else 1
            cursor.execute("UPDATE clips SET is_pinned = ? WHERE id = ?", (new_state, clip_id))
            conn.commit()
            return bool(new_state)

    def delete_clip(self, clip_id: int):
        """Supprime un élément spécifique."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
            conn.commit()

    def clear_all(self, keep_pinned: bool = True):
        """Efface l'historique (conserve par défaut les favoris épinglés)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if keep_pinned:
                cursor.execute("DELETE FROM clips WHERE is_pinned = 0")
            else:
                cursor.execute("DELETE FROM clips")
            conn.commit()

    def cleanup_old_items(self, max_items: int = MAX_HISTORY_ITEMS):
        """Supprime les éléments non-épinglés les plus anciens au-delà de max_items."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Compter les éléments non-épinglés
            cursor.execute("SELECT COUNT(*) as cnt FROM clips WHERE is_pinned = 0")
            count = cursor.fetchone()["cnt"]

            if count > max_items:
                to_delete = count - max_items
                cursor.execute("""
                    DELETE FROM clips WHERE id IN (
                        SELECT id FROM clips WHERE is_pinned = 0 ORDER BY updated_at ASC LIMIT ?
                    )
                """, (to_delete,))
                conn.commit()

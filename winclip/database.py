"""Gestion du stockage local SQLite pour WinClip.

Améliorations v2 :
  - la taille d'historique suit les préférences utilisateur ;
  - les fichiers d'images sont supprimés avec leur clip (plus d'orphelins) ;
  - statistiques (taille base, dossier images) pour la fenêtre de paramètres.
"""
import json
import os
import sqlite3
import time
from typing import Any, Optional

from .config import DB_PATH, IMAGES_DIR, MAX_HISTORY_ITEMS


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Connexion & schéma
    # ------------------------------------------------------------------
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
        self._migrate_legacy_schema()

    def _migrate_legacy_schema(self):
        """Migration douce pour les bases créées par une version antérieure."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(clips)")
                columns = {row["name"] for row in cursor.fetchall()}
                if "content_type" not in columns:
                    cursor.execute("ALTER TABLE clips ADD COLUMN content_type TEXT DEFAULT 'text'")
                    conn.commit()
        except sqlite3.Error:
            pass

    # ------------------------------------------------------------------
    # Écriture
    # ------------------------------------------------------------------
    def add_clip(self, content: str, content_type: str, metadata: dict,
                 thumbnail_path: Optional[str] = None) -> int:
        """Ajoute un élément ou le remonte au sommet s'il existe déjà."""
        now = time.time()
        meta_str = json.dumps(metadata, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, is_pinned FROM clips WHERE content = ?", (content,))
            row = cursor.fetchone()

            if row:
                clip_id = row["id"]
                cursor.execute("""
                    UPDATE clips
                    SET updated_at = ?, metadata_json = ?,
                        thumbnail_path = COALESCE(?, thumbnail_path)
                    WHERE id = ?
                """, (now, meta_str, thumbnail_path, clip_id))
            else:
                cursor.execute("""
                    INSERT INTO clips (content, content_type, is_pinned,
                                       thumbnail_path, metadata_json,
                                       created_at, updated_at)
                    VALUES (?, ?, 0, ?, ?, ?, ?)
                """, (content, content_type, thumbnail_path, meta_str, now, now))
                clip_id = cursor.lastrowid

            conn.commit()

        self.cleanup_old_items()
        return clip_id

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------
    def get_clips(self, search: Optional[str] = None, only_pinned: bool = False,
                  limit: Optional[int] = None) -> list[dict]:
        """Récupère les éléments filtrés par recherche ou épinglés."""
        if limit is None:
            limit = self._max_history()

        query = "SELECT * FROM clips WHERE 1=1"
        params: list[Any] = []

        if only_pinned:
            query += " AND is_pinned = 1"

        if search:
            # Recherche insensible à la casse dans le contenu ET les métadonnées
            query += " AND (content LIKE ? OR metadata_json LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like])

        query += " ORDER BY is_pinned DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for r in rows:
                item = dict(r)
                item["metadata"] = (
                    json.loads(item["metadata_json"]) if item["metadata_json"] else {}
                )
                results.append(item)
            return results

    def get_clip(self, clip_id: int) -> Optional[dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
            row = cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            item["metadata"] = (
                json.loads(item["metadata_json"]) if item["metadata_json"] else {}
            )
            return item

    def count_clips(self) -> dict:
        """Renvoie {'total': n, 'pinned': n}."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS c FROM clips")
            total = cursor.fetchone()["c"]
            cursor.execute("SELECT COUNT(*) AS c FROM clips WHERE is_pinned = 1")
            pinned = cursor.fetchone()["c"]
        return {"total": total, "pinned": pinned}

    # ------------------------------------------------------------------
    # Modifications
    # ------------------------------------------------------------------
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
        """Supprime un élément et son fichier image associé."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT content, content_type, thumbnail_path FROM clips WHERE id = ?",
                (clip_id,),
            )
            row = cursor.fetchone()
            cursor.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
            conn.commit()
        if row:
            self._remove_image_files(row["content_type"], row["content"], row["thumbnail_path"])

    def clear_all(self, keep_pinned: bool = True):
        """Efface l'historique (conserve par défaut les éléments épinglés)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            where = "WHERE is_pinned = 0" if keep_pinned else ""
            cursor.execute(
                f"SELECT content, content_type, thumbnail_path FROM clips {where}"
            )
            rows = cursor.fetchall()
            cursor.execute(f"DELETE FROM clips {where}")
            conn.commit()
        for row in rows:
            self._remove_image_files(row["content_type"], row["content"], row["thumbnail_path"])

    def cleanup_old_items(self, max_items: Optional[int] = None):
        """Supprime les éléments non épinglés les plus anciens au-delà de la limite."""
        if max_items is None:
            max_items = self._max_history()

        rows: list = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS cnt FROM clips WHERE is_pinned = 0")
            count = cursor.fetchone()["cnt"]

            if count > max_items:
                to_delete = count - max_items
                cursor.execute("""
                    SELECT content, content_type, thumbnail_path FROM clips
                    WHERE is_pinned = 0 ORDER BY updated_at ASC LIMIT ?
                """, (to_delete,))
                rows = cursor.fetchall()
                cursor.execute("""
                    DELETE FROM clips WHERE id IN (
                        SELECT id FROM clips WHERE is_pinned = 0
                        ORDER BY updated_at ASC LIMIT ?
                    )
                """, (to_delete,))
                conn.commit()
        for row in rows:
            self._remove_image_files(row["content_type"], row["content"], row["thumbnail_path"])

    # ------------------------------------------------------------------
    # Utilitaires internes
    # ------------------------------------------------------------------
    @staticmethod
    def _max_history() -> int:
        """Lit la taille d'historique depuis les préférences (repli : constante)."""
        try:
            from .settings import settings
            return int(settings.get("history_size", MAX_HISTORY_ITEMS))
        except Exception:
            return MAX_HISTORY_ITEMS

    @staticmethod
    def _remove_image_files(content_type: str, content: str,
                            thumbnail_path: Optional[str]):
        """Supprime les fichiers image d'un clip (uniquement dans IMAGES_DIR)."""
        if content_type != "image":
            return
        for candidate in {content, thumbnail_path}:
            if not candidate:
                continue
            try:
                p = os.path.realpath(candidate)
                # Garde-fou : ne supprimer que dans le dossier d'images WinClip
                if p.startswith(os.path.realpath(str(IMAGES_DIR))) and os.path.isfile(p):
                    os.unlink(p)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Statistiques (fenêtre de paramètres)
    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        db_size = 0
        try:
            db_size = os.path.getsize(self.db_path)
        except OSError:
            pass

        images_size = 0
        images_count = 0
        try:
            for entry in os.scandir(IMAGES_DIR):
                if entry.is_file():
                    images_size += entry.stat().st_size
                    images_count += 1
        except OSError:
            pass

        counts = self.count_clips()
        return {
            "clips": counts["total"],
            "pinned": counts["pinned"],
            "db_bytes": db_size,
            "images_bytes": images_size,
            "images_count": images_count,
        }


def format_bytes(num: float) -> str:
    """Formatage lisible d'une taille en octets (Ko / Mo / Go)."""
    for unit in ("o", "Ko", "Mo", "Go"):
        if abs(num) < 1024.0:
            if unit == "o":
                return f"{int(num)} {unit}"
            return f"{num:3.1f} {unit}".replace(".", ",")
        num /= 1024.0
    return f"{num:.1f} To".replace(".", ",")

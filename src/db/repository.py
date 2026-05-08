from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from src.db.schema import init_db


class Repository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        init_db(db_path)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def upsert_item(self, canonical_name: str, display_name: str) -> int:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO items(canonical_name, display_name)
                VALUES(?, ?)
                ON CONFLICT(canonical_name) DO UPDATE SET display_name=excluded.display_name
                """,
                (canonical_name, display_name),
            )
            row = conn.execute(
                "SELECT ingredient_id FROM items WHERE canonical_name = ?",
                (canonical_name,),
            ).fetchone()
            return int(row["ingredient_id"])

    def add_lot(
        self,
        ingredient_id: int,
        quantity: float,
        unit: str,
        source: str,
        acquired_at: str,
        expires_on: str | None,
        confidence: float | None,
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO inventory_lots(
                    ingredient_id, quantity, unit, source, acquired_at, expires_on, confidence
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (ingredient_id, quantity, unit, source, acquired_at, expires_on, confidence),
            )
            return int(cur.lastrowid)

    def add_event(
        self,
        event_type: str,
        ingredient_id: int,
        quantity_delta: float,
        lot_id: int | None = None,
        reason: str | None = None,
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO events(event_type, ingredient_id, lot_id, quantity_delta, reason, created_at)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (event_type, ingredient_id, lot_id, quantity_delta, reason, datetime.utcnow().isoformat()),
            )
            return int(cur.lastrowid)

    def set_shelf_life_rule(self, ingredient_id: int, default_days: int, source: str = "local") -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO shelf_life_rules(ingredient_id, default_days, source, updated_at)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(ingredient_id) DO UPDATE SET
                    default_days=excluded.default_days,
                    source=excluded.source,
                    updated_at=excluded.updated_at
                """,
                (ingredient_id, default_days, source, datetime.utcnow().isoformat()),
            )

    def get_shelf_life_days(self, ingredient_id: int) -> int | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT default_days FROM shelf_life_rules WHERE ingredient_id=?",
                (ingredient_id,),
            ).fetchone()
            return int(row["default_days"]) if row else None

    def list_inventory_view(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    i.ingredient_id,
                    i.display_name,
                    SUM(l.quantity) AS total_quantity,
                    l.unit,
                    MIN(l.expires_on) AS earliest_expires_on
                FROM inventory_lots l
                JOIN items i ON i.ingredient_id = l.ingredient_id
                WHERE l.is_active = 1 AND l.quantity > 0
                GROUP BY i.ingredient_id, i.display_name, l.unit
                ORDER BY earliest_expires_on IS NULL, earliest_expires_on ASC
                """
            ).fetchall()
            return [dict(r) for r in rows]

    def consume_inventory(self, ingredient_id: int, quantity: float, reason: str = "cooked") -> float:
        remaining = quantity
        with self.connection() as conn:
            lots = conn.execute(
                """
                SELECT lot_id, quantity
                FROM inventory_lots
                WHERE ingredient_id=? AND is_active=1 AND quantity>0
                ORDER BY expires_on IS NULL, expires_on ASC, acquired_at ASC
                """,
                (ingredient_id,),
            ).fetchall()
            for lot in lots:
                if remaining <= 0:
                    break
                take = min(float(lot["quantity"]), remaining)
                new_qty = float(lot["quantity"]) - take
                conn.execute(
                    "UPDATE inventory_lots SET quantity=?, is_active=? WHERE lot_id=?",
                    (new_qty, 0 if new_qty <= 0 else 1, int(lot["lot_id"])),
                )
                conn.execute(
                    """
                    INSERT INTO events(event_type, ingredient_id, lot_id, quantity_delta, reason, created_at)
                    VALUES(?, ?, ?, ?, ?, ?)
                    """,
                    ("consume", ingredient_id, int(lot["lot_id"]), -take, reason, datetime.utcnow().isoformat()),
                )
                remaining -= take
        return max(0.0, remaining)

    def get_item_by_name(self, canonical_name: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT ingredient_id, canonical_name, display_name FROM items WHERE canonical_name=?",
                (canonical_name,),
            ).fetchone()
            return dict(row) if row else None

    def get_all_items(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT ingredient_id, canonical_name, display_name FROM items ORDER BY display_name ASC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_item_by_id(self, ingredient_id: int) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT ingredient_id, canonical_name, display_name FROM items WHERE ingredient_id=?",
                (ingredient_id,),
            ).fetchone()
            return dict(row) if row else None

    def cache_get(self, key: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT payload_json
                FROM api_cache
                WHERE cache_key = ? AND expires_at > ?
                """,
                (key, datetime.utcnow().isoformat()),
            ).fetchone()
            return json.loads(row["payload_json"]) if row else None

    def cache_set(self, key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        now = datetime.utcnow()
        expires_at = datetime.fromtimestamp(now.timestamp() + ttl_seconds)
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO api_cache(cache_key, payload_json, expires_at, created_at)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    expires_at=excluded.expires_at,
                    created_at=excluded.created_at
                """,
                (key, json.dumps(payload, ensure_ascii=False), expires_at.isoformat(), now.isoformat()),
            )

    def get_image_cache(self, image_hash: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT payload_json FROM image_cache WHERE image_hash=?",
                (image_hash,),
            ).fetchone()
            return json.loads(row["payload_json"]) if row else None

    def set_image_cache(self, image_hash: str, payload: dict[str, Any]) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO image_cache(image_hash, payload_json, created_at)
                VALUES(?, ?, ?)
                ON CONFLICT(image_hash) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    created_at=excluded.created_at
                """,
                (image_hash, json.dumps(payload, ensure_ascii=False), datetime.utcnow().isoformat()),
            )

from __future__ import annotations

import sqlite3


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS items (
    ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory_lots (
    lot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,
    quantity REAL NOT NULL CHECK (quantity >= 0),
    unit TEXT NOT NULL DEFAULT 'item',
    source TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    expires_on TEXT,
    confidence REAL,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (ingredient_id) REFERENCES items(ingredient_id)
);

CREATE TABLE IF NOT EXISTS shelf_life_rules (
    ingredient_id INTEGER PRIMARY KEY,
    default_days INTEGER NOT NULL CHECK (default_days > 0),
    source TEXT NOT NULL DEFAULT 'local',
    updated_at TEXT NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES items(ingredient_id)
);

CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    ingredient_id INTEGER NOT NULL,
    lot_id INTEGER,
    quantity_delta REAL NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES items(ingredient_id),
    FOREIGN KEY (lot_id) REFERENCES inventory_lots(lot_id)
);

CREATE TABLE IF NOT EXISTS image_cache (
    image_hash TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS api_cache (
    cache_key TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()

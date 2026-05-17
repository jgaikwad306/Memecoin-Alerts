from __future__ import annotations

import json
import os
import sqlite3

from .models import RugCheckReport, TokenPair
from .utils import utc_now_iso


SCHEMA = """
CREATE TABLE IF NOT EXISTS tokens_seen (
    id INTEGER PRIMARY KEY,
    chain_id TEXT,
    token_address TEXT UNIQUE,
    pair_address TEXT,
    name TEXT,
    symbol TEXT,
    first_seen_at TEXT,
    last_checked_at TEXT,
    dex_url TEXT,
    rugcheck_url TEXT,
    rugcheck_score REAL,
    liquidity_usd REAL,
    volume_5m_usd REAL,
    market_cap_usd REAL,
    pair_age_minutes REAL,
    alerted INTEGER DEFAULT 0,
    raw_dex_json TEXT,
    raw_rugcheck_json TEXT
);
"""


def connect(sqlite_path: str) -> sqlite3.Connection:
    directory = os.path.dirname(sqlite_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(SCHEMA)
    conn.commit()


def has_seen_token(conn: sqlite3.Connection, token_address: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM tokens_seen WHERE token_address = ? LIMIT 1",
        (token_address,),
    ).fetchone()
    return row is not None


def save_seen_token(conn: sqlite3.Connection, pair: TokenPair) -> None:
    now = utc_now_iso()
    conn.execute(
        """
        INSERT OR IGNORE INTO tokens_seen (
            chain_id, token_address, pair_address, name, symbol,
            first_seen_at, last_checked_at, dex_url, liquidity_usd,
            volume_5m_usd, market_cap_usd, pair_age_minutes, raw_dex_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pair.chain_id,
            pair.token_address,
            pair.pair_address,
            pair.name,
            pair.symbol,
            now,
            now,
            pair.dex_url,
            pair.liquidity_usd,
            pair.volume_5m_usd,
            pair.market_cap_usd,
            pair.pair_age_minutes,
            json.dumps(pair.raw),
        ),
    )
    conn.commit()


def update_token_with_rugcheck(
    conn: sqlite3.Connection, token_address: str, report: RugCheckReport
) -> None:
    conn.execute(
        """
        UPDATE tokens_seen
        SET last_checked_at = ?,
            rugcheck_url = ?,
            rugcheck_score = ?,
            raw_rugcheck_json = ?
        WHERE token_address = ?
        """,
        (
            utc_now_iso(),
            report.url,
            report.score,
            json.dumps(report.raw),
            token_address,
        ),
    )
    conn.commit()


def mark_alerted(conn: sqlite3.Connection, token_address: str) -> None:
    conn.execute(
        "UPDATE tokens_seen SET alerted = 1, last_checked_at = ? WHERE token_address = ?",
        (utc_now_iso(), token_address),
    )
    conn.commit()

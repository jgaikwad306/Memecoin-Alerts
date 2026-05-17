from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Protocol

from .models import RugCheckReport, TokenPair
from .utils import utc_now_iso


SQLITE_SCHEMA = """
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


POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS tokens_seen (
    id BIGSERIAL PRIMARY KEY,
    chain_id TEXT,
    token_address TEXT UNIQUE,
    pair_address TEXT,
    name TEXT,
    symbol TEXT,
    first_seen_at TEXT,
    last_checked_at TEXT,
    dex_url TEXT,
    rugcheck_url TEXT,
    rugcheck_score DOUBLE PRECISION,
    liquidity_usd DOUBLE PRECISION,
    volume_5m_usd DOUBLE PRECISION,
    market_cap_usd DOUBLE PRECISION,
    pair_age_minutes DOUBLE PRECISION,
    alerted INTEGER DEFAULT 0,
    raw_dex_json TEXT,
    raw_rugcheck_json TEXT
);
"""


class CursorLike(Protocol):
    def fetchone(self) -> Any:
        ...


class ConnectionLike(Protocol):
    backend: str

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> CursorLike:
        ...

    def commit(self) -> None:
        ...

    def close(self) -> None:
        ...

    def __enter__(self) -> ConnectionLike:
        ...

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        ...


@dataclass
class Database:
    raw: Any
    backend: str

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> CursorLike:
        if self.backend == "postgres":
            query = query.replace("?", "%s")
        return self.raw.execute(query, params)

    def commit(self) -> None:
        self.raw.commit()

    def close(self) -> None:
        self.raw.close()

    def __enter__(self) -> Database:
        self.raw.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.raw.__exit__(exc_type, exc, tb)


def connect(database_url: str = "", sqlite_path: str = "data/bot.sqlite3") -> Database:
    if database_url:
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "DATABASE_URL is set, but psycopg is not installed. "
                "Run: pip install -r requirements.txt"
            ) from exc

        return Database(psycopg.connect(database_url), "postgres")

    directory = os.path.dirname(sqlite_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    return Database(conn, "sqlite")


def init_db(conn: ConnectionLike) -> None:
    schema = POSTGRES_SCHEMA if conn.backend == "postgres" else SQLITE_SCHEMA
    conn.execute(schema)
    conn.commit()


def has_seen_token(conn: ConnectionLike, token_address: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM tokens_seen WHERE token_address = ? LIMIT 1",
        (token_address,),
    ).fetchone()
    return row is not None


def save_seen_token(conn: ConnectionLike, pair: TokenPair) -> None:
    now = utc_now_iso()
    insert_prefix = "INSERT OR IGNORE" if conn.backend == "sqlite" else "INSERT"
    conflict_suffix = "" if conn.backend == "sqlite" else " ON CONFLICT (token_address) DO NOTHING"
    conn.execute(
        f"""
        {insert_prefix} INTO tokens_seen (
            chain_id, token_address, pair_address, name, symbol,
            first_seen_at, last_checked_at, dex_url, liquidity_usd,
            volume_5m_usd, market_cap_usd, pair_age_minutes, raw_dex_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        {conflict_suffix}
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
    conn: ConnectionLike, token_address: str, report: RugCheckReport
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


def mark_alerted(conn: ConnectionLike, token_address: str) -> None:
    conn.execute(
        "UPDATE tokens_seen SET alerted = 1, last_checked_at = ? WHERE token_address = ?",
        (utc_now_iso(), token_address),
    )
    conn.commit()

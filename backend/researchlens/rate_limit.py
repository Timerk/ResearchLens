"""Daily quotas for paid live answers, persisted so restarts do not reset them.

Visitors are counted by a keyed hash of their network address and the UTC day. Raw
addresses are never stored, and a visitor's hashes on different days cannot be linked.
"""

import hashlib
import hmac
import ipaddress
import secrets
import sqlite3
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Literal, Protocol

GLOBAL = "*"


@dataclass(frozen=True)
class QuotaDecision:
    allowed: bool
    reason: Literal["ok", "visitor_limit", "daily_limit"]
    visitor_remaining: int
    global_remaining: int


class QuotaStore(Protocol):
    def secret(self) -> bytes: ...

    def counts(self, day: str, visitor: str) -> tuple[int, int]: ...

    def consume(
        self, day: str, visitor: str, visitor_limit: int, global_limit: int
    ) -> QuotaDecision: ...


def _decide(used: int, total: int, visitor_limit: int, global_limit: int) -> QuotaDecision:
    if used >= visitor_limit:
        reason = "visitor_limit"
    elif total >= global_limit:
        reason = "daily_limit"
    else:
        return QuotaDecision(True, "ok", visitor_limit - used - 1, max(global_limit - total - 1, 0))
    return QuotaDecision(False, reason, max(visitor_limit - used, 0), max(global_limit - total, 0))


class MemoryQuotaStore:
    """Process-local store for tests and local development."""

    def __init__(self) -> None:
        self._secret = secrets.token_bytes(32)
        self._counts: dict[tuple[str, str], int] = {}
        self._lock = threading.Lock()

    def secret(self) -> bytes:
        return self._secret

    def counts(self, day: str, visitor: str) -> tuple[int, int]:
        with self._lock:
            return self._counts.get((day, visitor), 0), self._counts.get((day, GLOBAL), 0)

    def consume(self, day: str, visitor: str, visitor_limit: int, global_limit: int):
        with self._lock:
            used = self._counts.get((day, visitor), 0)
            total = self._counts.get((day, GLOBAL), 0)
            decision = _decide(used, total, visitor_limit, global_limit)
            if decision.allowed:
                self._counts[(day, visitor)] = used + 1
                self._counts[(day, GLOBAL)] = total + 1
            return decision


class SQLiteQuotaStore:
    """Small persistent store. Each check-and-increment runs in one write transaction."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS usage ("
                "day TEXT NOT NULL, scope TEXT NOT NULL, count INTEGER NOT NULL, "
                "PRIMARY KEY (day, scope))"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS meta (name TEXT PRIMARY KEY, value BLOB NOT NULL)"
            )
            connection.execute(
                "INSERT OR IGNORE INTO meta (name, value) VALUES ('secret', ?)",
                (secrets.token_bytes(32),),
            )
            self._secret = connection.execute(
                "SELECT value FROM meta WHERE name = 'secret'"
            ).fetchone()[0]

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            yield connection
        finally:
            connection.close()

    def secret(self) -> bytes:
        return self._secret

    def counts(self, day: str, visitor: str) -> tuple[int, int]:
        with self._lock, self._connect() as connection:
            rows = dict(
                connection.execute(
                    "SELECT scope, count FROM usage WHERE day = ? AND scope IN (?, ?)",
                    (day, visitor, GLOBAL),
                ).fetchall()
            )
        return rows.get(visitor, 0), rows.get(GLOBAL, 0)

    def consume(self, day: str, visitor: str, visitor_limit: int, global_limit: int):
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                rows = dict(
                    connection.execute(
                        "SELECT scope, count FROM usage WHERE day = ? AND scope IN (?, ?)",
                        (day, visitor, GLOBAL),
                    ).fetchall()
                )
                decision = _decide(
                    rows.get(visitor, 0), rows.get(GLOBAL, 0), visitor_limit, global_limit
                )
                if decision.allowed:
                    connection.executemany(
                        "INSERT INTO usage (day, scope, count) VALUES (?, ?, 1) "
                        "ON CONFLICT (day, scope) DO UPDATE SET count = count + 1",
                        ((day, visitor), (day, GLOBAL)),
                    )
                # Keep only the current and previous day.
                cutoff = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
                connection.execute("DELETE FROM usage WHERE day < ?", (cutoff,))
                connection.execute("COMMIT")
            except BaseException:
                connection.execute("ROLLBACK")
                raise
        return decision


def network_key(address: str) -> str:
    """Group IPv6 clients by /64 so rotating interface IDs does not multiply the quota."""
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        return address
    if isinstance(parsed, ipaddress.IPv6Address):
        if parsed.ipv4_mapped is not None:
            return str(parsed.ipv4_mapped)
        return str(ipaddress.ip_network(f"{parsed}/64", strict=False))
    return str(parsed)


def client_address(forwarded_for: str | None, peer: str | None, proxy_hops: int) -> str:
    """Return the address the outermost trusted proxy saw.

    With N trusted proxies in front of the app, the last N X-Forwarded-For entries were
    written by them; the entry N from the end is the client. Earlier entries are
    client-controlled and ignored.
    """
    chain = [part.strip() for part in (forwarded_for or "").split(",") if part.strip()]
    if proxy_hops < 1 or not chain:
        return peer or "unknown"
    candidate = chain[-proxy_hops] if len(chain) >= proxy_hops else chain[0]
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return peer or "unknown"
    return candidate


def utc_today() -> str:
    return datetime.now(UTC).date().isoformat()


def seconds_until_utc_midnight(now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    tomorrow = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), UTC)
    return max(int((tomorrow - now).total_seconds()), 1)


class LiveAnswerQuota:
    def __init__(
        self,
        store: QuotaStore,
        visitor_limit: int,
        global_limit: int,
        today: Callable[[], str] = utc_today,
    ) -> None:
        self.store = store
        self.visitor_limit = visitor_limit
        self.global_limit = global_limit
        self.today = today

    def _visitor(self, address: str, day: str) -> str:
        message = f"{day}|{network_key(address)}".encode()
        return hmac.new(self.store.secret(), message, hashlib.sha256).hexdigest()[:32]

    def consume(self, address: str) -> QuotaDecision:
        day = self.today()
        return self.store.consume(
            day, self._visitor(address, day), self.visitor_limit, self.global_limit
        )

    def remaining(self, address: str) -> tuple[int, int]:
        day = self.today()
        used, total = self.store.counts(day, self._visitor(address, day))
        return max(self.visitor_limit - used, 0), max(self.global_limit - total, 0)

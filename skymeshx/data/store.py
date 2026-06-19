"""
TelemetryStore — in-memory ring buffer for telemetry history.

Keeps last N snapshots per drone. Useful for:
  - plotting in UI
  - anomaly detection
  - experiment analysis

Usage:
    store = TelemetryStore(max_history=1000)
    store.push("D1", telemetry.snapshot())
    recent = store.get("D1", last_n=100)
    all_data = store.export_json("D1")
"""

import json
import threading
from collections import deque
from typing import Dict, List, Optional


class TelemetryStore:
    def __init__(self, max_history: int = 2000, db_path: Optional[str] = None):
        self._max = max_history
        self._data: Dict[str, deque] = {}
        self._lock = threading.Lock()
        self._db_path = db_path
        self._db_conn = None
        if db_path:
            self._init_db(db_path)

    def _init_db(self, path: str):
        import sqlite3

        self._db_conn = sqlite3.connect(path, check_same_thread=False)
        self._db_conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                drone_id TEXT NOT NULL,
                ts       REAL NOT NULL,
                snapshot TEXT NOT NULL
            )
        """)
        self._db_conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_drone_ts ON telemetry(drone_id, ts)"
        )
        self._db_conn.commit()

    def push(self, drone_id: str, snapshot: dict):
        with self._lock:
            if drone_id not in self._data:
                self._data[drone_id] = deque(maxlen=self._max)
            self._data[drone_id].append(snapshot)
        if self._db_conn:
            import json as _json

            try:
                self._db_conn.execute(
                    "INSERT INTO telemetry (drone_id, ts, snapshot) VALUES (?, ?, ?)",
                    (drone_id, snapshot.get("timestamp", 0.0), _json.dumps(snapshot)),
                )
                self._db_conn.commit()
            except Exception as e:
                print(f"[store] DB write error: {e}")

    def get(self, drone_id: str, last_n: Optional[int] = None) -> List[dict]:
        with self._lock:
            buf = self._data.get(drone_id)
            if not buf:
                return []
            data = list(buf)
        return data[-last_n:] if last_n else data

    def latest(self, drone_id: str) -> Optional[dict]:
        with self._lock:
            buf = self._data.get(drone_id)
            return buf[-1] if buf else None

    def drone_ids(self) -> List[str]:
        with self._lock:
            return list(self._data.keys())

    def export_json(self, drone_id: str) -> str:
        return json.dumps(self.get(drone_id), indent=2)

    def export_csv(self, drone_id: str) -> str:
        rows = self.get(drone_id)
        if not rows:
            return ""
        headers = list(rows[0].keys())
        lines = [",".join(str(h) for h in headers)]
        for row in rows:
            lines.append(",".join(str(row.get(h, "")) for h in headers))
        return "\n".join(lines)

    def query_db(self, drone_id: str, since: float = 0.0, limit: int = 1000) -> list:
        """Query historical data from SQLite (only if db_path was set)."""
        if not self._db_conn:
            return []
        import json as _json

        cur = self._db_conn.execute(
            "SELECT snapshot FROM telemetry"
            " WHERE drone_id=? AND ts>=? ORDER BY ts DESC LIMIT ?",
            (drone_id, since, limit),
        )
        return [_json.loads(row[0]) for row in cur.fetchall()]

    def close(self):
        """Close the SQLite connection cleanly."""
        if self._db_conn:
            self._db_conn.close()
            self._db_conn = None

    def clear(self, drone_id: Optional[str] = None):
        with self._lock:
            if drone_id:
                self._data.pop(drone_id, None)
            else:
                self._data.clear()

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    Path(settings.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.EXPORT_DIR).mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                allergy TEXT,
                alcohol_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def create_submission(name: str, allergy: str, alcohol: dict[str, Any]) -> int:
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO submissions (name, allergy, alcohol_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (name, allergy, json.dumps(alcohol, ensure_ascii=False), created_at),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_latest_submissions(limit: int = 10) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, allergy, alcohol_json, created_at
            FROM submissions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return rows


def get_submission_count() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM submissions").fetchone()
    return int(row["cnt"])


def get_all_submissions() -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, allergy, alcohol_json, created_at
            FROM submissions
            ORDER BY id DESC
            """
        ).fetchall()
    return rows


def export_to_csv() -> str:
    rows = get_all_submissions()
    export_path = Path(settings.EXPORT_DIR) / "submissions_export.csv"

    with export_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "name",
                "allergy",
                "whiteWine",
                "redWine",
                "champagne",
                "beer",
                "whiskey",
                "tinctures",
                "created_at",
            ]
        )

        for row in rows:
            alcohol = json.loads(row["alcohol_json"])
            writer.writerow(
                [
                    row["id"],
                    row["name"],
                    row["allergy"],
                    alcohol.get("whiteWine", False),
                    alcohol.get("redWine", False),
                    alcohol.get("champagne", False),
                    alcohol.get("beer", False),
                    alcohol.get("whiskey", False),
                    alcohol.get("tinctures", False),
                    row["created_at"],
                ]
            )

    return str(export_path)

def delete_submission_by_id(submission_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM submissions WHERE id = ?",
            (submission_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
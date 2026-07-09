import sqlite3
from pathlib import Path

from app.config.settings import settings


def _resolve_sqlite_path(database_url: str) -> Path:
    raw = str(database_url or "sqlite:///linkedin_ai.db")
    if not raw.startswith("sqlite:///"):
        raise ValueError(f"Only sqlite URLs are supported by this patch helper: {raw}")
    value = raw.replace("sqlite:///", "", 1)
    return Path(value)


def main() -> None:
    db_path = _resolve_sqlite_path(settings.DATABASE_URL)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cols = [row[1] for row in cur.execute("PRAGMA table_info(engagement_settings)").fetchall()]
    if "topic_configs_json" in cols:
        print("topic_configs_json already exists")
        conn.close()
        return

    cur.execute(
        "ALTER TABLE engagement_settings ADD COLUMN topic_configs_json TEXT NOT NULL DEFAULT ''"
    )
    conn.commit()
    conn.close()
    print("added topic_configs_json")


if __name__ == "__main__":
    main()

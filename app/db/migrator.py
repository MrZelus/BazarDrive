import sqlite3
from pathlib import Path


def _default_migrations_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "migrations"


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def _list_migration_files(migrations_dir: Path) -> list[Path]:
    if not migrations_dir.exists():
        return []
    return sorted(path for path in migrations_dir.glob("*.sql") if path.is_file())


def _is_idempotent_error(error: sqlite3.OperationalError) -> bool:
    message = str(error).lower()
    return "duplicate column name" in message


def apply_migrations(db_path: str, migrations_dir: Path | None = None) -> None:
    target_dir = migrations_dir or _default_migrations_dir()

    conn = sqlite3.connect(db_path)
    try:
        _ensure_migrations_table(conn)

        cur = conn.cursor()
        cur.execute("SELECT version FROM schema_migrations")
        applied_versions = {row[0] for row in cur.fetchall()}

        for migration_file in _list_migration_files(target_dir):
            version = migration_file.name
            if version in applied_versions:
                continue

            sql = migration_file.read_text(encoding="utf-8")

            try:
                conn.execute("BEGIN")
                conn.executescript(sql)
                conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
                conn.commit()
            except sqlite3.OperationalError as exc:
                conn.rollback()
                if not _is_idempotent_error(exc):
                    raise
                conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
                conn.commit()
    finally:
        conn.close()

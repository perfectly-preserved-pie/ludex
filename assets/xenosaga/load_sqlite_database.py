from sqlite3 import Connection, connect
from pathlib import Path
from typing import Optional

def load_sqlite_database(db_path: Optional[Path] = None) -> Connection:
    """Load the SQLite database and return a connection object.

    If ``db_path`` is not provided it defaults to the bundled
    ``xenosaga.db`` located next to this module.
    """
    if db_path is None:
        db_path = Path(__file__).parent / "xenosaga.db"

    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")

    connection = connect(db_path)
    return connection

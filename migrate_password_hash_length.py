import os
import sqlite3

from config import Config


def migrate(db_path: str) -> None:
    if not os.path.isfile(db_path):
        print(f"❌ DB not found: {db_path}")
        return

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # Check current schema
    cur.execute("PRAGMA table_info(user)")
    cols = cur.fetchall()
    col_defs = {c[1]: c for c in cols}
    if 'password_hash' not in col_defs:
        print("❌ Column password_hash not found in user table")
        con.close()
        return

    # If already large enough, skip
    # SQLite doesn't enforce varchar length, so we rely on schema text
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user'")
    row = cur.fetchone()
    if not row:
        print("❌ user table not found")
        con.close()
        return
    create_sql = row[0]
    if 'password_hash' in create_sql and '(255)' in create_sql:
        print("ℹ️ password_hash already at length 255. Nothing to do.")
        con.close()
        return

    print("➡️  Migrating user.password_hash to length 255 ...")
    try:
        cur.execute("BEGIN TRANSACTION")

        # Create new table with desired schema
        cur.execute(
            """
            CREATE TABLE user_new (
                id INTEGER PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(120) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                is_active BOOLEAN,
                created_at DATETIME,
                last_login DATETIME
            )
            """
        )

        # Copy data
        cur.execute(
            """
            INSERT INTO user_new (id, username, email, password_hash, role, is_active, created_at, last_login)
            SELECT id, username, email, password_hash, role, is_active, created_at, last_login FROM user
            """
        )

        # Drop old and rename
        cur.execute("DROP TABLE user")
        cur.execute("ALTER TABLE user_new RENAME TO user")

        con.commit()
        print("✅ Migration completed.")
    except Exception as e:
        con.rollback()
        print(f"❌ Migration failed: {e}")
    finally:
        con.close()


if __name__ == "__main__":
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    if not db_uri.startswith("sqlite:///"):
        print(f"❌ Not a SQLite URI: {db_uri}")
    else:
        db_path = db_uri.replace("sqlite:///", "")
        migrate(db_path)




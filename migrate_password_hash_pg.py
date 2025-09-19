from app import app, db
from sqlalchemy import text


def migrate_password_hash_length():
    with app.app_context():
        engine = db.get_engine()
        url = str(engine.url)
        if not (url.startswith('postgresql://') or url.startswith('postgresql+psycopg2://')):
            print(f"❌ Not a PostgreSQL URI: {url}")
            return

        print(f"➡️  Connecting to: {url}")
        with engine.begin() as conn:
            # Check current definition
            result = conn.execute(text(
                """
                SELECT character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'user' AND column_name = 'password_hash'
                """
            )).fetchone()

            if result is None:
                print("❌ Column password_hash not found on table user")
                return

            current_len = result[0]
            print(f"ℹ️ Current length: {current_len}")
            if current_len is None or current_len >= 255:
                print("ℹ️ No change needed.")
                return

            # user is a reserved word; quote it
            print("➡️  Altering column length to 255 ...")
            conn.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(255)'))
            print("✅ Migration completed.")


if __name__ == '__main__':
    migrate_password_hash_length()




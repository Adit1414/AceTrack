# backend/migrate_db.py
from database import engine
from sqlalchemy import text

def run_migration():
    print("🚀 Starting database migration...")
    try:
        with engine.connect() as connection:
            # Add the missing column
            print("--- Adding is_authorized column to users table ---")
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_authorized BOOLEAN DEFAULT FALSE;"))

            # Ensure syllabuses.topics is JSON type
            print("--- Ensuring syllabuses.topics is JSON type ---")
            connection.execute(text("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'syllabuses' 
                          AND column_name = 'topics' 
                          AND data_type = 'ARRAY'
                    ) THEN
                        ALTER TABLE syllabuses ALTER COLUMN topics TYPE JSON USING to_json(topics);
                    END IF;
                END $$;
            """))
            
            # Add study_plans missing columns
            print("--- Adding missing columns to study_plans table ---")
            is_sqlite = engine.dialect.name == "sqlite"
            if is_sqlite:
                result = connection.execute(text("PRAGMA table_info(study_plans);")).fetchall()
                cols = [row[1] for row in result]
                if cols:
                    if "days_per_week" not in cols:
                        connection.execute(text("ALTER TABLE study_plans ADD COLUMN days_per_week INTEGER DEFAULT 7;"))
                    if "excluded_topics" not in cols:
                        connection.execute(text("ALTER TABLE study_plans ADD COLUMN excluded_topics TEXT DEFAULT '[]';"))
            else:
                connection.execute(text("ALTER TABLE study_plans ADD COLUMN IF NOT EXISTS days_per_week INTEGER DEFAULT 7;"))
                connection.execute(text("ALTER TABLE study_plans ADD COLUMN IF NOT EXISTS excluded_topics JSON DEFAULT '[]';"))

            # Manually authorize your account (replace with your email)
            print("--- Authorizing admin user ---")
            # EDIT THIS LINE: Change 'vanneet@gmail.com' to your actual email
            email_to_authorize = 'rad@gmail.com' 
            connection.execute(text(f"UPDATE users SET is_authorized = TRUE WHERE email = '{email_to_authorize}';"))
            
            connection.commit()
            print("✅ Migration successful! All columns added and user authorized.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
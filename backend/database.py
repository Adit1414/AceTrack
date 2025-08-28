from dotenv import load_dotenv
import os
import urllib.parse

load_dotenv()  # Loads variables from .env

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_PASS = urllib.parse.quote_plus(os.getenv("DATABASE_PASS"))
SUPABASE_PASS = urllib.parse.quote_plus(os.getenv("SUPABASE_PASS"))
# DATABASE_URL = urllib.parse.quote_plus(os.getenv("DATABASE_URL"))
DATABASE_USER = "postgres"
DATABASE_NAME = "StudyPlanner"

# DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASS}@localhost/{DATABASE_NAME}"
DATABASE_URL = f"postgresql://postgres:{SUPABASE_PASS}@db.sfcszdosbwjrlubgotvj.supabase.co:5432/postgres"

if not DATABASE_PASS:
    raise ValueError("DATABASE_PASS not set in .env file")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

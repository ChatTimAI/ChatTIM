import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PLUGIN_DATABASE_URL = os.getenv(
    "PLUGIN_DATABASE_URL", "postgresql://user:pass@localhost/dbname"
)

engine = create_engine(PLUGIN_DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

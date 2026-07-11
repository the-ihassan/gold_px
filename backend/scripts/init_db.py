"""
Quick-start table creation for local development.

For production, use Alembic migrations instead:
    alembic revision --autogenerate -m "init"
    alembic upgrade head

This script exists so you can spin up the stack and start testing
immediately without hand-writing (or waiting to autogenerate against a
live DB) the first migration.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import engine
from app.models import Base


def main():
    print("Creating all tables from models metadata...")
    Base.metadata.create_all(bind=engine)
    print("Done. Tables created (if they didn't already exist).")


if __name__ == "__main__":
    main()

"""
Simple script to allow dashboard + FastAPI containers to only come up after DB is created
"""
import time
from pathlib import Path

DB_PATH = Path("/app/data/emissions.db")

print("Waiting for database to be created...")
while not DB_PATH.exists():
    time.sleep(5)
    print("...still waiting for DB")

print("Database found, starting service!")
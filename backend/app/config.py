import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'sih_traffic.db'}")
PROJECT_NAME = "SIH26127 Traffic AI & Trajectory Engine"
API_V1_PREFIX = "/api"

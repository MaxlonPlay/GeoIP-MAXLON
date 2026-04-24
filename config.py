import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

DATA_DIR = BASE_DIR / "data"
CSV_DOWNLOAD_URL = "https://ip.guide/bulk/networks.csv"
CACHE_VERSION = "4.2"

DAEMON_WEB_HOST = os.getenv("DAEMON_WEB_HOST", "0.0.0.0")
DAEMON_WEB_PORT = int(os.getenv("DAEMON_WEB_PORT", 8881))

DATA_FILENAME = os.getenv("DATA_FILENAME", str(DATA_DIR / "networks.csv"))

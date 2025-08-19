import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()  # Load environment variables from .env.

BASE_DIR = Path(__file__).resolve().parent.parent

DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()
SQLITE_PATH = os.getenv('SQLITE_PATH', str(BASE_DIR / 'data' / 'school_fees.db'))
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_DB = os.getenv('MYSQL_DB', 'school_fees')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')

SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
LOG_PATH = os.getenv('LOG_PATH', str(BASE_DIR / 'logs' / 'school_fees.log'))
RECEIPTS_DIR = str(BASE_DIR / 'receipts')
BACKUP_DIR = str(BASE_DIR / 'backups')

# Contribution defaults (admin-configurable)
DEFAULT_RATES = {
    'maize': float(os.getenv('RATE_MAIZE', '30.0')),
    'millet': float(os.getenv('RATE_MILLET', '40.0')),
    'beans': float(os.getenv('RATE_BEANS', '25.0'))
}

# Bus fee locations (admin-configurable)
BUS_FEES = {
    'Location1': float(os.getenv('BUS_FEE_LOCATION1', '50.0')),
    'Location2': float(os.getenv('BUS_FEE_LOCATION2', '60.0'))
}
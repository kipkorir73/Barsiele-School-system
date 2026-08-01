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

# Project-root .env (Settings persistence). BASE_DIR is the app/ package directory.
ENV_PATH = BASE_DIR.parent / '.env'
_RATE_ENV_KEYS = {
    'maize': 'RATE_MAIZE',
    'millet': 'RATE_MILLET',
    'beans': 'RATE_BEANS',
}


def update_contribution_rates(rates: dict, env_path: Path | None = None) -> dict:
    """Apply contribution rates immediately and persist them by upserting .env keys.

    Previously Settings appended duplicate RATE_* lines and never mutated DEFAULT_RATES,
    so clerks kept recording cash equivalents at the old in-memory prices until restart
    (and polluted .env with ignored duplicates depending on loader behavior).
    """
    normalized = {}
    for item, env_key in _RATE_ENV_KEYS.items():
        if item not in rates:
            raise ValueError(f"Missing contribution rate for {item}")
        value = float(rates[item])
        if value < 0:
            raise ValueError(f"Contribution rate for {item} cannot be negative")
        normalized[item] = value

    # Mutate the shared dict so importers (e.g. payment_tab) see new rates immediately.
    DEFAULT_RATES.update(normalized)

    path = Path(env_path) if env_path is not None else ENV_PATH
    _upsert_env_rates(path, {env_key: normalized[item] for item, env_key in _RATE_ENV_KEYS.items()})

    # Keep process env in sync for any code that reads os.getenv later.
    for item, env_key in _RATE_ENV_KEYS.items():
        os.environ[env_key] = str(normalized[item])

    return dict(DEFAULT_RATES)


def _upsert_env_rates(env_path: Path, env_values: dict) -> None:
    """Rewrite RATE_* keys in .env (create file if needed), removing duplicates."""
    env_path = Path(env_path)
    if env_path.exists():
        lines = env_path.read_text(encoding='utf-8').splitlines()
    else:
        env_path.parent.mkdir(parents=True, exist_ok=True)
        lines = []

    seen = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in env_values:
                if key not in seen:
                    new_lines.append(f"{key}={env_values[key]}")
                    seen.add(key)
                # Drop any later duplicate assignments for the same key.
                continue
        new_lines.append(line)

    for key, value in env_values.items():
        if key not in seen:
            new_lines.append(f"{key}={value}")

    env_path.write_text('\n'.join(new_lines) + ('\n' if new_lines else ''), encoding='utf-8')

# Bus fee locations (admin-configurable)
BUS_FEES = {
    'Location1': float(os.getenv('BUS_FEE_LOCATION1', '50.0')),
    'Location2': float(os.getenv('BUS_FEE_LOCATION2', '60.0'))
}
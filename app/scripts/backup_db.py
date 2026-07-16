import os
import sqlite3
from datetime import datetime
from pathlib import Path
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

def backup():
    try:
        backup_dir = Path("backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        db_path = Path(os.getenv('SQLITE_PATH', 'app/data/school_fees.db'))
        if not db_path.is_file():
            logging.warning("Database file not found. Please initialize the database first.")
            print("Database file not found. Please initialize the database first.")
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'school_fees_backup_{timestamp}.db'
        backup_path = backup_dir / backup_filename

        # SQLite's backup API creates a consistent snapshot even if another
        # connection is writing to the live database.
        source_uri = f"{db_path.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(source_uri, uri=True) as source:
            with sqlite3.connect(backup_path) as destination:
                source.backup(destination)

        logging.info(f"Backup created successfully: {backup_path}")
        print(f"Backup created successfully: {backup_path}")
        cleanup_old_backups(backup_dir)
        return str(backup_path)
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        print(f"Backup failed: {e}")

def cleanup_old_backups(backup_dir, keep_count=10):
    try:
        backup_files = [(os.path.join(backup_dir, file), os.path.getmtime(os.path.join(backup_dir, file)))
                       for file in os.listdir(backup_dir) if file.startswith('school_fees_backup_') and file.endswith('.db')]
        backup_files.sort(key=lambda x: x[1], reverse=True)
        for file_path, _ in backup_files[keep_count:]:
            os.remove(file_path)
            logging.info(f"Removed old backup: {os.path.basename(file_path)}")
            print(f"Removed old backup: {os.path.basename(file_path)}")
    except Exception as e:
        logging.error(f"Cleanup failed: {e}")
        print(f"Cleanup failed: {e}")

if __name__ == "__main__":
    backup()
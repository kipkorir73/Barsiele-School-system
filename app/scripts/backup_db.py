import shutil, os
from app.config import BACKUP_DIR, SQLITE_PATH
from datetime import datetime
os.makedirs(BACKUP_DIR, exist_ok=True)
dest = os.path.join(BACKUP_DIR, f'school_fees_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
shutil.copy2(SQLITE_PATH, dest)
print('Backup created:', dest)

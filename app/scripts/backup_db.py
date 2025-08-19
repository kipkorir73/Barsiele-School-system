import shutil
from datetime import datetime
import os

def backup():
    if not os.path.exists('backups'):
        os.makedirs('backups')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    shutil.copy('data/school.db', f'backups/school_{timestamp}.db')
    print("Backup created.")

if __name__ == "__main__":
    backup()
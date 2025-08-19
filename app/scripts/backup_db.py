import shutil
import os
from datetime import datetime
from pathlib import Path

def backup():
    try:
        # Create backups directory if it doesn't exist
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Check if database file exists
        db_path = "data/school_fees.db"
        if not os.path.exists(db_path):
            print("Database file not found. Please initialize the database first.")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'school_fees_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        shutil.copy2(db_path, backup_path)
        print(f"Backup created successfully: {backup_path}")
        
        # Keep only last 10 backups
        cleanup_old_backups(backup_dir)
        
    except Exception as e:
        print(f"Backup failed: {e}")

def cleanup_old_backups(backup_dir, keep_count=10):
    """Keep only the most recent backups"""
    try:
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.startswith('school_fees_backup_') and file.endswith('.db'):
                file_path = os.path.join(backup_dir, file)
                backup_files.append((file_path, os.path.getmtime(file_path)))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old backups
        for file_path, _ in backup_files[keep_count:]:
            os.remove(file_path)
            print(f"Removed old backup: {os.path.basename(file_path)}")
            
    except Exception as e:
        print(f"Cleanup failed: {e}")

if __name__ == "__main__":
    backup()

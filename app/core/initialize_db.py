from .db_manager import DBManager
from .models import tables

def init_db():
    db = DBManager()
    for table in tables:
        db.execute(table)
        print(f"✅ Created/ensured table: {table}")
    print("🎉 Database initialized successfully.")

if __name__ == "__main__":
    init_db()

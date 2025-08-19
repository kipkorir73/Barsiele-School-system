from db_manager import DBManager
from models import tables

def init_db():
    db = DBManager()
    for table in tables:
        db.execute(table)
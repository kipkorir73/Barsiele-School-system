import os, logging
from app.db_manager import DatabaseManager
from app import models

logger = logging.getLogger(__name__)

def init_db(use_mysql=False):
    dbm = DatabaseManager(use_mysql=use_mysql)
    conn = dbm.connect()
    cur = conn.cursor()
    # Create tables
    cur.executescript(models.STUDENT_TABLE)
    cur.executescript(models.TERMS_TABLE)
    cur.executescript(models.FEE_STRUCTURE_TABLE)
    cur.executescript(models.CONVERSION_TABLE)
    cur.executescript(models.PAYMENTS_TABLE)
    conn.commit()
    dbm.close()
    logger.info('Database initialized.')

if __name__ == '__main__':
    init_db()

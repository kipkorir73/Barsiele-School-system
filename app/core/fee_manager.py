from app.db_manager import DatabaseManager
from app.config import DEFAULT_RATES
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class FeeManager:
    def __init__(self, dbm=None):
        self.dbm = dbm or DatabaseManager()
        # ensure conversion table exists
        conn = self.dbm.connect()
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS conversion_rates (commodity TEXT UNIQUE, rate_per_kg REAL);')
        # seed defaults if empty
        for k,v in DEFAULT_RATES.items():
            cur.execute('INSERT OR IGNORE INTO conversion_rates (commodity, rate_per_kg) VALUES (?, ?);', (k, v))
        conn.commit()
        self.dbm.close()

    def set_class_fee(self, class_name, term_id, amount):
        conn = self.dbm.connect()
        cur = conn.cursor()
        cur.execute('INSERT INTO fee_structure (class_name, term_id, fee_amount) VALUES (?, ?, ?);', (class_name, term_id, float(amount)))
        conn.commit()
        self.dbm.close()

    def get_class_fee(self, class_name, term_id):
        conn = self.dbm.connect()
        cur = conn.cursor()
        cur.execute('SELECT fee_amount FROM fee_structure WHERE class_name = ? AND term_id = ?;', (class_name, term_id))
        row = cur.fetchone()
        self.dbm.close()
        return row['fee_amount'] if row else None

    def get_conversion_rate(self, commodity):
        conn = self.dbm.connect()
        cur = conn.cursor()
        cur.execute('SELECT rate_per_kg FROM conversion_rates WHERE commodity = ?;', (commodity,))
        row = cur.fetchone()
        self.dbm.close()
        return Decimal(row['rate_per_kg']) if row else None

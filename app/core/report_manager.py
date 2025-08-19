from app.db_manager import DatabaseManager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ReportManager:
    def __init__(self, dbm=None):
        self.dbm = dbm or DatabaseManager()

    def get_collection_summary(self, start_date=None, end_date=None, class_name=None):
        conn = self.dbm.connect()
        cur = conn.cursor()
        q = 'SELECT SUM(total_amount) as total_collections FROM payments WHERE 1=1'
        params = []
        if start_date:
            q += ' AND payment_date >= ?'; params.append(start_date)
        if end_date:
            q += ' AND payment_date <= ?'; params.append(end_date)
        if class_name:
            q = q.replace('FROM payments', 'FROM payments p JOIN students s ON p.student_id = s.student_id') 
            q += ' AND s.class_name = ?'; params.append(class_name)
        cur.execute(q, tuple(params))
        row = cur.fetchone()
        self.dbm.close()
        return {'total_collections': row['total_collections'] or 0.0, 'generated_at': datetime.now().isoformat()}

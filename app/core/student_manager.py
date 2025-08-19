from app.db_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class StudentManager:
    def __init__(self, dbm=None):
        self.dbm = dbm or DatabaseManager()

    def add_student(self, admission_number, full_name, class_name, stream=None):
        conn = self.dbm.connect()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO students (admission_number, full_name, class_name, stream) VALUES (?, ?, ?, ?);',
                        (admission_number, full_name, class_name, stream))
            conn.commit()
            logger.info('Student added: %s', admission_number)
            return True, cur.lastrowid
        except Exception as e:
            logger.exception('Error adding student: %s', e)
            return False, str(e)
        finally:
            self.dbm.close()

    def get_student_by_adm(self, admission_number):
        conn = self.dbm.connect()
        cur = conn.cursor()
        cur.execute('SELECT * FROM students WHERE admission_number = ?;', (admission_number,))
        student = cur.fetchone()
        self.dbm.close()
        return student

    def list_students(self, class_name=None):
        conn = self.dbm.connect()
        cur = conn.cursor()
        if class_name:
            cur.execute('SELECT * FROM students WHERE class_name = ? ORDER BY full_name;', (class_name,))
        else:
            cur.execute('SELECT * FROM students ORDER BY full_name;')
        rows = cur.fetchall()
        self.dbm.close()
        return rows

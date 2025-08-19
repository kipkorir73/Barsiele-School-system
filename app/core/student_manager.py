from db_manager import DBManager

def create_student(admission_number, name, class_, guardian_contact, profile_picture=None):
    db = DBManager()
    db.execute(
        "INSERT INTO students (admission_number, name, class, guardian_contact, profile_picture) VALUES (?, ?, ?, ?, ?)",
        (admission_number, name, class_, guardian_contact, profile_picture)
    )
    return db.last_id()

def update_student(student_id, **kwargs):
    if not kwargs:
        return
    set_clause = ', '.join(f"{k} = ?" for k in kwargs)
    params = list(kwargs.values()) + [student_id]
    db = DBManager()
    db.execute(f"UPDATE students SET {set_clause} WHERE id = ?", params)

def get_student(student_id):
    db = DBManager()
    return db.fetch_one("SELECT * FROM students WHERE id = ?", (student_id,))

def get_all_students():
    db = DBManager()
    return db.fetch_all("SELECT * FROM students")

def search_students(query):
    db = DBManager()
    return db.fetch_all("SELECT * FROM students WHERE name LIKE ? OR admission_number LIKE ?", (f"%{query}%", f"%{query}%"))
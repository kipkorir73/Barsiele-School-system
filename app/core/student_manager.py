from .db_manager import DBManager

def create_student(admission_number, name, class_, guardian_contact, profile_picture=None):
    db = DBManager()
    try:
        db.execute(
            "INSERT INTO students (admission_number, name, class, guardian_contact, profile_picture) VALUES (?, ?, ?, ?, ?)",
            (admission_number, name, class_, guardian_contact, profile_picture)
        )
        return db.last_id()
    finally:
        db.close()

def update_student(student_id, **kwargs):
    if not kwargs:
        return
    
    db = DBManager()
    try:
        set_clause = ', '.join(f"{k} = ?" for k in kwargs)
        params = list(kwargs.values()) + [student_id]
        db.execute(f"UPDATE students SET {set_clause} WHERE id = ?", params)
    finally:
        db.close()

def get_student(student_id):
    db = DBManager()
    try:
        return db.fetch_one("SELECT * FROM students WHERE id = ?", (student_id,))
    finally:
        db.close()

def get_all_students():
    db = DBManager()
    try:
        return db.fetch_all("SELECT * FROM students ORDER BY name")
    finally:
        db.close()

def search_students(query):
    if not query.strip():
        return get_all_students()
    
    db = DBManager()
    try:
        search_pattern = f"%{query}%"
        return db.fetch_all(
            "SELECT * FROM students WHERE name LIKE ? OR admission_number LIKE ? ORDER BY name", 
            (search_pattern, search_pattern)
        )
    finally:
        db.close()
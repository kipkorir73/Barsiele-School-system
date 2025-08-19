tables = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admission_number TEXT UNIQUE,
        name TEXT,
        class TEXT,
        guardian_contact TEXT,
        profile_picture TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        total_fees REAL,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        amount REAL,
        method TEXT,
        date TEXT,
        clerk_id INTEGER,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(clerk_id) REFERENCES users(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_id INTEGER,
        filename TEXT,
        FOREIGN KEY(payment_id) REFERENCES payments(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        timestamp TEXT
    )
    """
]
# Note: For MySQL, replace AUTOINCREMENT with AUTO_INCREMENT and adjust date to DATETIME DEFAULT CURRENT_TIMESTAMP if needed.
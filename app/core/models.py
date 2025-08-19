tables = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(255) UNIQUE,
        password TEXT,
        role VARCHAR(50)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(50) UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        admission_number VARCHAR(50) UNIQUE,
        class_id INTEGER,
        name VARCHAR(255),
        guardian_contact VARCHAR(20),
        profile_picture TEXT,
        bus_location VARCHAR(100),
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        student_id INTEGER,
        total_fees DECIMAL(10, 2),
        bus_fee DECIMAL(10, 2) DEFAULT 0.0,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS contributions (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        student_id INTEGER,
        item VARCHAR(50),
        quantity DECIMAL(10, 2),
        cash_equivalent DECIMAL(10, 2),
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        student_id INTEGER,
        amount DECIMAL(10, 2),
        method VARCHAR(50),
        date DATE,
        clerk_id INTEGER,
        receipt_no VARCHAR(50),
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (clerk_id) REFERENCES users(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        payment_id INTEGER,
        receipt_no VARCHAR(50),
        filename TEXT,
        FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        user_id INTEGER,
        action TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )
    """
]
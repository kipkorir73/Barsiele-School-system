# Simple models: using plain SQL and dicts (no heavy ORM).

STUDENT_TABLE = """
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    class_name TEXT NOT NULL,
    stream TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

TERMS_TABLE = """
CREATE TABLE IF NOT EXISTS terms (
    term_id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_name TEXT NOT NULL,
    year INTEGER NOT NULL,
    start_date TEXT,
    end_date TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

FEE_STRUCTURE_TABLE = """
CREATE TABLE IF NOT EXISTS fee_structure (
    fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT NOT NULL,
    term_id INTEGER NOT NULL,
    fee_amount REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(term_id) REFERENCES terms(term_id) ON DELETE CASCADE
);
"""

CONVERSION_TABLE = """
CREATE TABLE IF NOT EXISTS conversion_rates (
    rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity TEXT UNIQUE NOT NULL,
    rate_per_kg REAL NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

PAYMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    payment_type TEXT NOT NULL, -- 'cash','maize','millet' or 'mixed'
    cash_amount REAL DEFAULT 0,
    maize_kg REAL DEFAULT 0,
    millet_kg REAL DEFAULT 0,
    converted_amount REAL DEFAULT 0,
    total_amount REAL DEFAULT 0,
    receipt_no TEXT,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(term_id) REFERENCES terms(term_id)
);
"""

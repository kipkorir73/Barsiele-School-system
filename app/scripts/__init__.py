import os
from ..core.db_manager import DBManager
from dotenv import load_dotenv

load_dotenv()

def initialize_database():
    with DBManager() as db:
        # Users table
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'clerk'))
            )
        """)
        # Classes table
        db.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL
            )
        """)
        # Students table
        db.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                admission_number VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                class_id INTEGER,
                guardian_contact VARCHAR(15),
                profile_picture VARCHAR(255),
                bus_location VARCHAR(50),
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
            )
        """)
        # Fees table
        db.execute("""
            CREATE TABLE IF NOT EXISTS fees (
                id INTEGER PRIMARY KEY,
                student_id INTEGER UNIQUE NOT NULL,
                total_fees DECIMAL(10, 2) NOT NULL,
                bus_fee DECIMAL(10, 2) DEFAULT 0.00,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """)
        # Payments table
        db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY,
                student_id INTEGER NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                method VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                clerk_id INTEGER NOT NULL,
                receipt_no VARCHAR(50) UNIQUE NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (clerk_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        # Contributions table
        db.execute("""
            CREATE TABLE IF NOT EXISTS contributions (
                id INTEGER PRIMARY KEY,
                student_id INTEGER NOT NULL,
                item VARCHAR(50) NOT NULL,
                quantity DECIMAL(10, 2) NOT NULL,
                cash_equivalent DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """)
        # Receipts table
        db.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY,
                payment_id INTEGER UNIQUE NOT NULL,
                receipt_no VARCHAR(50) UNIQUE NOT NULL,
                filename VARCHAR(255) NOT NULL,
                FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
            )
        """)
        # Audit logs table
        db.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                action VARCHAR(255) NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        # Initial admin user
        db.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                  ('admin', 'admin123', 'admin'))

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")
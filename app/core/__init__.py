from app.core.initialize_db import init_db
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))



if __name__ == "__main__":
    init_db()
    print("Database initialized.")
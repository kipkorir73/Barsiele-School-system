# School Fee Management System (Desktop Starter)

This starter project provides a **desktop-first** Python backend for a School Fee Management System.
It includes basic security features, a simple SQLite DB backend (switchable to MySQL), receipt generation,
and a PyQt UI placeholder. Use this as a scaffold — extend and harden for production.

## What's included
- app/: core backend modules (DB manager, models, managers, auth, receipt generator)
- ui/: PyQt placeholder UI files (starter main window)
- scripts/: helper scripts (db init, backup)
- requirements.txt
- .env.example
- start_desktop.py (launch point)

## Quick start (development)
1. Create and activate a Python virtualenv:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Initialize database (development uses SQLite):
   ```bash
   python scripts/init_db.py
   ```
3. Run the desktop launcher:
   ```bash
   python start_desktop.py
   ```

## Security notes
- Passwords are hashed with bcrypt using passlib.
- Use environment variables (see .env.example) for secrets and DB credentials.
- Prepared statements / parameterized queries are used to prevent SQL injection.
- Logging is configured to write to `logs/school_fees.log`.

## Next steps
- Replace SQLite with MySQL in production, and use secure credentials via env variables.
- Implement secure backup process and encrypt saved backups.
- Add 2FA if needed (pyotp) and secure the UI with session timeouts.

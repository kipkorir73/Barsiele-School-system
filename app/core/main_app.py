import logging, os
from app.config import LOG_PATH
from app.auth import AuthManager
from app.student_manager import StudentManager
from app.payment_manager import PaymentManager
from app.fee_manager import FeeManager
from app.report_manager import ReportManager

def setup_logging():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler()
        ]
    )

def run_app():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info('Starting School Fee Management backend (desktop mode)')
    # minimal CLI loop for demo/test
    auth = AuthManager()
    # create default superadmin if not exists
    try:
        auth.create_user('superadmin', 'change-me', role='superadmin')
    except Exception:
        pass
    print('School Fee Management (backend demo)')
    print('This is a starting point. Plug into PyQt UI later.')

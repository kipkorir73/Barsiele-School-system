import unittest

from app.core.session_lifecycle import (
    _active_login_windows,
    release_login_window,
    resolve_main_window_close,
    retain_login_window,
)


class TestSessionLifecycle(unittest.TestCase):
    def setUp(self):
        _active_login_windows.clear()

    def tearDown(self):
        _active_login_windows.clear()

    def test_logout_closes_session_without_quitting(self):
        # Logout must not ask to exit; answering No used to leave the
        # authenticated window open while a second login was shown.
        self.assertEqual(
            resolve_main_window_close(logging_out=True, exit_confirmed=None),
            "accept_keep_running",
        )
        self.assertEqual(
            resolve_main_window_close(logging_out=True, exit_confirmed=False),
            "accept_keep_running",
        )

    def test_confirmed_exit_quits_process(self):
        self.assertEqual(
            resolve_main_window_close(logging_out=False, exit_confirmed=True),
            "accept_quit",
        )

    def test_cancelled_exit_keeps_authenticated_window(self):
        self.assertEqual(
            resolve_main_window_close(logging_out=False, exit_confirmed=False),
            "ignore",
        )

    def test_retain_and_release_login_window(self):
        window = object()
        retain_login_window(window)
        retain_login_window(window)
        self.assertEqual(_active_login_windows, [window])
        release_login_window(window)
        self.assertEqual(_active_login_windows, [])
        release_login_window(window)  # missing is a no-op


if __name__ == "__main__":
    unittest.main()

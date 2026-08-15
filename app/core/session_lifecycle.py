"""Session lifetime helpers for the desktop GUI.

Login used to hide the login window instead of closing it, and logout called
MainWindow.close() which asked "Exit Application?". Answering No (the natural
choice when the user only wanted to log out) left the authenticated window
open and still spawned a second login/session against the same SQLite file.
Cash payments have no uniqueness check, so both windows could insert ledger
rows for one physical payment.

Confirmed Exit also failed to quit the QApplication while the hidden login
window still existed, so a second process could be started against the live DB.
"""

# Keep a strong reference to the active login window after logout so Qt/Python
# does not garbage-collect it when the previous MainWindow is closed.
_active_login_windows = []


def retain_login_window(window):
    """Hold a process-level reference to a top-level login window."""
    if window is not None and window not in _active_login_windows:
        _active_login_windows.append(window)
    return window


def release_login_window(window):
    """Drop the process-level reference after a successful login."""
    try:
        _active_login_windows.remove(window)
    except ValueError:
        pass


def resolve_main_window_close(*, logging_out: bool, exit_confirmed: bool | None) -> str:
    """Decide how MainWindow.closeEvent should finish.

    Returns:
        'ignore'               – keep the authenticated window open
        'accept_keep_running'  – close it but leave the Qt app running (logout)
        'accept_quit'          – close it and quit the process (user confirmed exit)
    """
    if logging_out:
        return "accept_keep_running"
    if exit_confirmed:
        return "accept_quit"
    return "ignore"

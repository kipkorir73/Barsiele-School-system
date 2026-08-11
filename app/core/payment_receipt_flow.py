"""Helpers that must not treat post-commit receipt failures as payment failures."""
from __future__ import annotations

from typing import Callable, Optional, Tuple


def handle_post_payment_receipt(
    payment_id,
    receipt_no: str,
    generate_fn: Callable,
    open_fn: Callable[[str], None],
    should_open: bool = True,
) -> Tuple[Optional[str], Optional[BaseException], str]:
    """Best-effort receipt work after record_payment has already committed.

    Returns (receipt_path, error, stage) where stage is one of:
    - "ok"
    - "generate"
    - "open"

    Never raises: callers should warn about receipt issues without implying the
    payment itself failed (Cash payments have no dedupe and get duplicated when
    clerks re-enter after a false "Failed to record payment" error).
    """
    try:
        receipt_path = generate_fn(payment_id, receipt_no)
    except BaseException as exc:  # noqa: BLE001 - must not escape to payment UI
        return None, exc, "generate"

    if not receipt_path:
        return None, RuntimeError("receipt generator returned no file"), "generate"

    if not should_open:
        return receipt_path, None, "ok"

    try:
        open_fn(receipt_path)
    except BaseException as exc:  # noqa: BLE001 - must not escape to payment UI
        return receipt_path, exc, "open"

    return receipt_path, None, "ok"

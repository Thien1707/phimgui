"""Chạy tác vụ nặng ngoài main thread, cập nhật UI qua widget.after."""
from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def run_bg(widget, fn: Callable[[], T], on_ok: Callable[[T], None], on_err: Callable[[Exception], None]):
    def work():
        try:
            result = fn()
            if widget.winfo_exists():
                widget.after(0, lambda: on_ok(result))
        except Exception as e:
            if widget.winfo_exists():
                widget.after(0, lambda: on_err(e))

    threading.Thread(target=work, daemon=True).start()

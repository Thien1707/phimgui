"""Khởi chạy Flask (nền) + GUI CustomTkinter."""
import subprocess
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent


def main():
    py = sys.executable
    server = subprocess.Popen(
        [py, "-m", "backend.app"],
        cwd=str(_ROOT),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )
    try:
        sys.path.insert(0, str(_ROOT))
        from gui import api_client

        if not api_client.wait_for_backend(max_wait_sec=15.0):
            print("Cảnh báo: Backend chưa phản hồi — GUI vẫn mở, có thể cần Tải lại.")
        subprocess.call([py, "-m", "gui.main"], cwd=str(_ROOT))
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()

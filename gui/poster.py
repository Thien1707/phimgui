"""Tải poster nền — giới hạn đồng thời, không block UI."""
from __future__ import annotations

import io
import threading

import customtkinter as ctk
import httpx
from PIL import Image

_sem = threading.Semaphore(4)


def attach_poster(
    label: ctk.CTkLabel,
    url: str | None,
    *,
    size: tuple[int, int] = (160, 240),
) -> None:
    label.configure(text="", width=size[0], height=size[1], fg_color="#1f1f1f")
    if not url or not str(url).startswith("http"):
        label.configure(text="—", fg_color="#2a2a2a")
        return

    def work():
        with _sem:
            try:
                with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                    r = client.get(url)
                    r.raise_for_status()
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                img.thumbnail(size, Image.Resampling.LANCZOS)
                w, h = img.size
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))

                def apply():
                    if not label.winfo_exists():
                        return
                    label.configure(image=ctk_img, text="", fg_color="transparent")
                    label._poster_image = ctk_img  # noqa: SLF001

                label.after(0, apply)
            except Exception:
                def fail():
                    if not label.winfo_exists():
                        return
                    label.configure(text="🎬", fg_color="#2a2a2a", image=None)

                label.after(0, fail)

    threading.Thread(target=work, daemon=True).start()

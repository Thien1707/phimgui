"""Thẻ poster có hover và click — Netflix-style grid item."""
from __future__ import annotations

import customtkinter as ctk

from gui.poster import attach_poster


class PosterCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        movie: dict,
        on_open,
        poster_size: tuple[int, int] = (160, 240),
    ):
        super().__init__(master, width=poster_size[0] + 16, fg_color="#1a1a1a", corner_radius=8)
        self.movie = movie
        self.on_open = on_open
        self._poster_size = poster_size
        self._hover = False

        self.configure(cursor="hand2")
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        self._poster_wrap = ctk.CTkFrame(self, fg_color="#0f0f0f", corner_radius=6)
        self._poster_wrap.pack(padx=8, pady=(8, 4))
        self._poster_wrap.configure(cursor="hand2")
        for w in (self._poster_wrap,):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", self._on_click)

        self.poster_lbl = ctk.CTkLabel(self._poster_wrap, text="")
        self.poster_lbl.pack()
        self.poster_lbl.configure(cursor="hand2")
        self.poster_lbl.bind("<Enter>", self._on_enter)
        self.poster_lbl.bind("<Leave>", self._on_leave)
        self.poster_lbl.bind("<Button-1>", self._on_click)

        url = movie.get("posterUrl") or movie.get("thumbUrl")
        attach_poster(self.poster_lbl, url, size=poster_size)

        self._overlay = ctk.CTkLabel(
            self._poster_wrap,
            text="",
            fg_color="transparent",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._overlay.place(relx=0.5, rely=0.5, anchor="center")
        self._overlay.configure(cursor="hand2")
        self._overlay.bind("<Enter>", self._on_enter)
        self._overlay.bind("<Leave>", self._on_leave)
        self._overlay.bind("<Button-1>", self._on_click)

        title = (movie.get("title") or "")[:42]
        if movie.get("viewStatus") == 1:
            title += " · VIP"
        self.title_lbl = ctk.CTkLabel(
            self, text=title, wraplength=poster_size[0] + 8, font=ctk.CTkFont(size=12)
        )
        self.title_lbl.pack(padx=8, pady=(2, 8))
        self.title_lbl.configure(cursor="hand2")
        self.title_lbl.bind("<Enter>", self._on_enter)
        self.title_lbl.bind("<Leave>", self._on_leave)
        self.title_lbl.bind("<Button-1>", self._on_click)

    def _on_enter(self, _event=None):
        if self._hover:
            return
        self._hover = True
        self.configure(border_width=2, border_color="#e50914")
        self._overlay.configure(text="Xem chi tiết")
        self._poster_wrap.configure(fg_color="#262626")

    def _on_leave(self, _event=None):
        self._hover = False
        self.configure(border_width=0)
        self._overlay.configure(text="")
        self._poster_wrap.configure(fg_color="#0f0f0f")

    def _on_click(self, _event=None):
        slug = self.movie.get("slug")
        if slug:
            self.on_open(slug)

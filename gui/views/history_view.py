import customtkinter as ctk

from gui import api_client


class HistoryFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, on_open_detail):
        super().__init__(master)
        self.on_open_detail = on_open_detail

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(top, text="Lịch sử xem", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="Xóa hết", width=80, command=self._clear).pack(side="right")

        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(pady=4)
        self.list = ctk.CTkFrame(self, fg_color="transparent")
        self.list.pack(fill="both", expand=True, padx=12)
        self.after(100, self.load)

    def load(self):
        for w in self.list.winfo_children():
            w.destroy()
        self.status.configure(text="Đang tải...")
        try:
            cont = api_client.api("GET", "/api/history/continue", params={"limit": 6})
            if cont:
                ctk.CTkLabel(
                    self.list, text="Xem tiếp", font=ctk.CTkFont(weight="bold")
                ).pack(anchor="w", pady=(0, 4))
                for item in cont:
                    self._row(item, highlight=True)
            ctk.CTkLabel(self.list, text="Tất cả", font=ctk.CTkFont(weight="bold")).pack(
                anchor="w", pady=(12, 4)
            )
            all_items = api_client.api("GET", "/api/history")
            if not isinstance(all_items, list):
                all_items = []
            if not all_items:
                ctk.CTkLabel(self.list, text="Chưa có lịch sử.").pack(anchor="w")
            for item in all_items:
                self._row(item)
            self.status.configure(text="")
        except api_client.ApiError as e:
            self.status.configure(text=str(e))

    def _row(self, item: dict, highlight: bool = False):
        m = item.get("movieId") or {}
        slug = m.get("slug")
        title = m.get("title") or slug
        ep = item.get("episode", 1)
        row = ctk.CTkFrame(self.list)
        row.pack(fill="x", pady=4)
        color = "#1e3a5f" if highlight else "transparent"
        row.configure(fg_color=color)
        ctk.CTkLabel(row, text=f"{title} — Tập {ep}", wraplength=500).pack(side="left", padx=8, pady=6)
        if slug:
            ctk.CTkButton(
                row, text="Mở", width=60, command=lambda s=slug: self.on_open_detail(s)
            ).pack(side="right", padx=8)

    def _clear(self):
        try:
            api_client.api("DELETE", "/api/history")
            self.load()
        except api_client.ApiError as e:
            self.status.configure(text=str(e))

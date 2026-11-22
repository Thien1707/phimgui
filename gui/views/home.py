import customtkinter as ctk

from gui import api_client
from gui.worker import run_bg
from gui.widgets.poster_card import PosterCard


class HomeFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, user: dict | None, on_open_detail):
        super().__init__(master)
        self.user = user
        self.on_open_detail = on_open_detail
        self.page = 1
        self.search_q = ""
        self.filter_type = ""
        self.filter_country = ""
        self.filter_category = ""
        self._load_id = 0
        self._cat_map = {"Thể loại: tất cả": ""}

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(top, text="Danh sách phim", font=ctk.CTkFont(size=20, weight="bold")).pack(
            side="left"
        )
        ctk.CTkButton(top, text="Tải lại", width=80, command=self.load).pack(side="right")

        filt = ctk.CTkFrame(self, fg_color="transparent")
        filt.pack(fill="x", padx=12, pady=4)
        self.search_entry = ctk.CTkEntry(filt, placeholder_text="Tìm kiếm...", width=200)
        self.search_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(filt, text="Tìm", width=50, command=self._do_search).pack(side="left")
        self.type_menu = ctk.CTkOptionMenu(filt, values=["Loại: tất cả"], width=120, command=self._on_type)
        self.type_menu.pack(side="left", padx=8)
        self.country_menu = ctk.CTkOptionMenu(
            filt, values=["Quốc gia: tất cả"], width=140, command=self._on_country
        )
        self.country_menu.pack(side="left", padx=4)
        self.cat_menu = ctk.CTkOptionMenu(
            filt, values=["Thể loại: tất cả"], width=140, command=self._on_category
        )
        self.cat_menu.pack(side="left", padx=4)

        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(pady=4)
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=8, pady=8)

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(pady=8)
        ctk.CTkButton(nav, text="← Trước", width=80, command=self.prev_page).pack(side="left", padx=4)
        self.page_label = ctk.CTkLabel(nav, text="Trang 1")
        self.page_label.pack(side="left", padx=8)
        ctk.CTkButton(nav, text="Sau →", width=80, command=self.next_page).pack(side="left", padx=4)

        self.after(50, self._load_filters_async)
        self.after(80, self.load)

    def _load_filters_async(self):
        def fetch():
            f = api_client.api("GET", "/api/movies/filters")
            cats = api_client.api("GET", "/api/categories")
            return f, cats

        def ok(result):
            f, cats = result
            types = ["Loại: tất cả"] + (f.get("types") or [])
            self.type_menu.configure(values=types)
            countries = ["Quốc gia: tất cả"] + (f.get("countries") or [])
            self.country_menu.configure(values=countries)
            cat_names = ["Thể loại: tất cả"]
            self._cat_map = {"Thể loại: tất cả": ""}
            for c in cats.get("items") or []:
                label = c.get("displayName") or c.get("name")
                cat_names.append(label)
                self._cat_map[label] = str(c.get("_id") or "")
            self.cat_menu.configure(values=cat_names)

        def err(_e):
            self._cat_map = {"Thể loại: tất cả": ""}

        run_bg(self, fetch, ok, err)

    def _on_type(self, val):
        self.filter_type = "" if val.startswith("Loại:") else val
        self.page = 1
        self.load()

    def _on_country(self, val):
        self.filter_country = "" if val.startswith("Quốc gia:") else val
        self.page = 1
        self.load()

    def _on_category(self, val):
        self.filter_category = self._cat_map.get(val, "")
        self.page = 1
        self.load()

    def _do_search(self):
        self.search_q = self.search_entry.get().strip()
        self.page = 1
        self.load()

    def load(self):
        self._load_id += 1
        req_id = self._load_id
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.status.configure(text="Đang tải danh sách…")

        def fetch():
            if self.search_q:
                return api_client.api(
                    "GET",
                    "/api/movies/search",
                    params={"q": self.search_q, "page": self.page, "limit": 12},
                )
            params = {"page": self.page, "limit": 12}
            if self.filter_type:
                params["type"] = self.filter_type
            if self.filter_country:
                params["country"] = self.filter_country
            if self.filter_category:
                params["category"] = self.filter_category
            return api_client.api("GET", "/api/movies", params=params)

        def ok(data):
            if req_id != self._load_id:
                return
            items = data.get("items") or []
            pag = data.get("pagination") or {}
            self.page_label.configure(text=f"Trang {pag.get('page', self.page)}")
            self.status.configure(
                text=f"{pag.get('total', len(items))} phim — nhấp poster để xem chi tiết"
            )
            for i, m in enumerate(items):
                row, col = divmod(i, 4)
                card = PosterCard(self.grid_frame, movie=m, on_open=self.on_open_detail)
                card.grid(row=row, column=col, padx=10, pady=10, sticky="n")
            for c in range(4):
                self.grid_frame.grid_columnconfigure(c, weight=1)

        def err(e):
            if req_id != self._load_id:
                return
            msg = str(e) if isinstance(e, api_client.ApiError) else "Lỗi tải phim"
            self.status.configure(text=msg)

        run_bg(self, fetch, ok, err)

    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.load()

    def next_page(self):
        self.page += 1
        self.load()

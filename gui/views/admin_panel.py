import customtkinter as ctk

from gui import api_client


class AdminPanelFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=8, pady=8)
        self.tabs.add("Tổng quan")
        self.tabs.add("Phim")
        self.tabs.add("Users")
        self.tabs.add("Cài đặt")
        self.tabs.add("Nhật ký")

        self._tab_overview(self.tabs.tab("Tổng quan"))
        self._tab_movies(self.tabs.tab("Phim"))
        self._tab_users(self.tabs.tab("Users"))
        self._tab_settings(self.tabs.tab("Cài đặt"))
        self._tab_logs(self.tabs.tab("Nhật ký"))

    def _tab_overview(self, parent):
        self.overview_lbl = ctk.CTkLabel(parent, text="Đang tải...", justify="left")
        self.overview_lbl.pack(anchor="w", padx=12, pady=12)
        ctk.CTkButton(parent, text="Tải lại", command=self._load_overview).pack(anchor="w", padx=12)
        self.after(200, self._load_overview)

    def _load_overview(self):
        try:
            o = api_client.api("GET", "/api/admin/dashboard/overview")
            text = "\n".join(f"{k}: {v}" for k, v in o.items())
            self.overview_lbl.configure(text=text)
        except api_client.ApiError as e:
            self.overview_lbl.configure(text=str(e))

    def _tab_movies(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=8)
        self.import_slug = ctk.CTkEntry(row, placeholder_text="slug phim (phimapi)", width=280)
        self.import_slug.pack(side="left", padx=4)
        ctk.CTkButton(row, text="Import", width=80, command=self._import_movie).pack(side="left", padx=4)
        self.movie_msg = ctk.CTkLabel(parent, text="")
        self.movie_msg.pack(anchor="w", padx=12)
        self.movie_list = ctk.CTkScrollableFrame(parent, height=320)
        self.movie_list.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkButton(parent, text="Tải danh sách phim", command=self._load_movies).pack(padx=8, pady=4)
        self.after(300, self._load_movies)

    def _import_movie(self):
        slug = self.import_slug.get().strip()
        if not slug:
            return
        try:
            api_client.api("POST", "/api/admin/movies/import", json_body={"slug": slug})
            self.movie_msg.configure(
                text=f"Đã import: {slug}. Bấm «Trang chủ» bên trái để xem phim.",
                text_color="#4ade80",
            )
            self._load_movies()
        except api_client.ApiError as e:
            self.movie_msg.configure(text=str(e), text_color="#f87171")

    def _load_movies(self):
        for w in self.movie_list.winfo_children():
            w.destroy()
        try:
            data = api_client.api("GET", "/api/admin/movies")
            for m in (data.get("items") or [])[:80]:
                row = ctk.CTkFrame(self.movie_list, fg_color="transparent")
                row.pack(fill="x", pady=2)
                mid = m.get("_id")
                title = (m.get("title") or "")[:50]
                ctk.CTkLabel(row, text=f"{title} ({m.get('slug')})", width=400, anchor="w").pack(
                    side="left"
                )
                ctk.CTkButton(
                    row, text="VIP", width=40, command=lambda i=mid: self._patch_movie(i, 1)
                ).pack(side="right", padx=2)
                ctk.CTkButton(
                    row, text="Free", width=40, command=lambda i=mid: self._patch_movie(i, 0)
                ).pack(side="right", padx=2)
                ctk.CTkButton(
                    row, text="Xóa", width=40, fg_color="#7f1d1d", command=lambda i=mid: self._del_movie(i)
                ).pack(side="right", padx=2)
        except api_client.ApiError as e:
            ctk.CTkLabel(self.movie_list, text=str(e)).pack(anchor="w")

    def _patch_movie(self, movie_id, view_status):
        try:
            api_client.api(
                "PATCH", f"/api/admin/movies/{movie_id}", json_body={"viewStatus": view_status}
            )
            self._load_movies()
        except api_client.ApiError as e:
            self.movie_msg.configure(text=str(e), text_color="#f87171")

    def _del_movie(self, movie_id):
        try:
            api_client.api("DELETE", f"/api/admin/movies/{movie_id}")
            self._load_movies()
        except api_client.ApiError as e:
            self.movie_msg.configure(text=str(e), text_color="#f87171")

    def _tab_users(self, parent):
        search_row = ctk.CTkFrame(parent, fg_color="transparent")
        search_row.pack(fill="x", padx=8, pady=8)
        self.user_search = ctk.CTkEntry(search_row, placeholder_text="Tìm email/tên", width=200)
        self.user_search.pack(side="left", padx=4)
        ctk.CTkButton(search_row, text="Tìm", width=60, command=self._load_users).pack(side="left")
        self.user_list = ctk.CTkScrollableFrame(parent, height=360)
        self.user_list.pack(fill="both", expand=True, padx=8, pady=8)
        self.after(400, self._load_users)

    def _load_users(self):
        for w in self.user_list.winfo_children():
            w.destroy()
        q = self.user_search.get().strip()
        path = "/api/admin/users"
        params = {"search": q} if q else None
        try:
            data = api_client.api("GET", path, params=params)
            for u in data.get("items") or []:
                row = ctk.CTkFrame(self.user_list, fg_color="transparent")
                row.pack(fill="x", pady=2)
                uid = u.get("id")
                label = f"{u.get('displayName')} · {u.get('email')} · {u.get('role')}"
                if u.get("banned"):
                    label += " [BANNED]"
                ctk.CTkLabel(row, text=label, anchor="w").pack(side="left", padx=4)
                ctk.CTkButton(row, text="VIP", width=36, command=lambda i=uid: self._vip_user(i)).pack(
                    side="right", padx=2
                )
                if u.get("banned"):
                    ctk.CTkButton(
                        row, text="Mở", width=36, command=lambda i=uid: self._unban(i)
                    ).pack(side="right", padx=2)
                else:
                    ctk.CTkButton(
                        row, text="Khóa", width=36, command=lambda i=uid: self._ban(i)
                    ).pack(side="right", padx=2)
        except api_client.ApiError as e:
            ctk.CTkLabel(self.user_list, text=str(e)).pack(anchor="w")

    def _ban(self, uid):
        api_client.api("PATCH", f"/api/admin/users/{uid}/ban")
        self._load_users()

    def _unban(self, uid):
        api_client.api("PATCH", f"/api/admin/users/{uid}/unban")
        self._load_users()

    def _vip_user(self, uid):
        api_client.api(
            "PATCH",
            f"/api/admin/users/{uid}/vip",
            json_body={"isVip": True, "days": 30},
        )
        self._load_users()

    def _tab_settings(self, parent):
        self.set_site = ctk.CTkEntry(parent, width=320, placeholder_text="Tên site")
        self.set_site.pack(padx=12, pady=8, anchor="w")
        self.maint = ctk.BooleanVar(value=False)
        self.reg = ctk.BooleanVar(value=True)
        self.comments = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(parent, text="Bảo trì", variable=self.maint).pack(anchor="w", padx=12)
        ctk.CTkCheckBox(parent, text="Cho đăng ký", variable=self.reg).pack(anchor="w", padx=12)
        ctk.CTkCheckBox(parent, text="Bình luận", variable=self.comments).pack(anchor="w", padx=12)
        ctk.CTkButton(parent, text="Lưu cài đặt", command=self._save_settings).pack(
            anchor="w", padx=12, pady=12
        )
        self.set_msg = ctk.CTkLabel(parent, text="")
        self.set_msg.pack(anchor="w", padx=12)
        self.after(500, self._load_settings)

    def _load_settings(self):
        try:
            s = api_client.api("GET", "/api/admin/settings")
            self.set_site.delete(0, "end")
            self.set_site.insert(0, s.get("siteName") or "")
            self.maint.set(bool(s.get("maintenanceMode")))
            self.reg.set(bool(s.get("registrationEnabled")))
            self.comments.set(bool(s.get("commentsEnabled")))
        except api_client.ApiError as e:
            self.set_msg.configure(text=str(e))

    def _save_settings(self):
        try:
            api_client.api(
                "PUT",
                "/api/admin/settings",
                json_body={
                    "siteName": self.set_site.get().strip(),
                    "maintenanceMode": self.maint.get(),
                    "registrationEnabled": self.reg.get(),
                    "commentsEnabled": self.comments.get(),
                },
            )
            self.set_msg.configure(text="Đã lưu.", text_color="#4ade80")
        except api_client.ApiError as e:
            self.set_msg.configure(text=str(e), text_color="#f87171")

    def _tab_logs(self, parent):
        self.log_box = ctk.CTkTextbox(parent, height=400)
        self.log_box.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkButton(parent, text="Tải nhật ký", command=self._load_logs).pack(padx=8, pady=4)
        self.after(600, self._load_logs)

    def _load_logs(self):
        self.log_box.delete("1.0", "end")
        try:
            data = api_client.api("GET", "/api/admin/logs", params={"limit": 40})
            for item in data.get("items") or []:
                line = f"{item.get('createdAt')} | {item.get('action')} | {item.get('targetType')}:{item.get('targetId')}\n"
                self.log_box.insert("end", line)
        except api_client.ApiError as e:
            self.log_box.insert("end", str(e))

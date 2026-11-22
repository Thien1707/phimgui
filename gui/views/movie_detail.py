import customtkinter as ctk

from gui import api_client
from gui.poster import attach_poster
from gui.views.watch import parse_episode_links
from gui.worker import run_bg


class MovieDetailFrame(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        slug: str,
        user: dict | None,
        *,
        on_watch,
        cached_movie: dict | None = None,
        on_cached=None,
    ):
        super().__init__(master, fg_color="transparent")
        self.slug = slug
        self.user = user
        self.on_watch = on_watch
        self.on_cached = on_cached
        self.movie: dict = cached_movie or {}
        self._selected_ep = ctk.IntVar(value=1)

        self.status = ctk.CTkLabel(self, text="")
        self.status.pack(pady=8)
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=12)

        if cached_movie:
            self.after(50, self._render)
        else:
            self.status.configure(text="Đang lấy thông tin phim…")
            self.after(50, self.load)

    def load(self):
        slug = self.slug

        def fetch():
            return api_client.api("GET", f"/api/movies/{slug}", timeout=45.0)

        def ok(data):
            self.movie = data.get("movie") or {}
            if self.on_cached:
                self.on_cached(self.slug, self.movie)
            self._render()

        def err(e):
            msg = str(e) if isinstance(e, api_client.ApiError) else "Không tải được phim"
            self.status.configure(text=msg)

        run_bg(self, fetch, ok, err)

    def _render(self):
        for w in self.body.winfo_children():
            w.destroy()
        m = self.movie
        if not m:
            self.status.configure(text="Không có dữ liệu phim.")
            return

        header = ctk.CTkFrame(self.body, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        poster_lbl = ctk.CTkLabel(header, text="")
        poster_lbl.pack(side="left", padx=(0, 16))
        attach_poster(poster_lbl, m.get("posterUrl") or m.get("thumbUrl"), size=(200, 300))

        info = ctk.CTkFrame(header, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            info,
            text=m.get("title") or self.slug,
            font=ctk.CTkFont(size=24, weight="bold"),
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))
        meta = f"{m.get('year') or ''} · {m.get('type') or ''} · {m.get('country') or ''}".strip(" ·")
        if meta:
            ctk.CTkLabel(info, text=meta, text_color="#94a3b8", wraplength=520, justify="left").pack(
                anchor="w"
            )

        eps = parse_episode_links(m) if m.get("canWatch") else []
        if eps:
            self._selected_ep.set(eps[0][0])
            if len(eps) > 1:
                ep_row = ctk.CTkFrame(info, fg_color="transparent")
                ep_row.pack(anchor="w", pady=(12, 4))
                ctk.CTkLabel(ep_row, text="Tập:").pack(side="left", padx=(0, 8))
                opts = [str(n) for n, _, _, _ in eps]
                self._ep_str = ctk.StringVar(value=opts[0])
                ctk.CTkOptionMenu(
                    ep_row,
                    variable=self._ep_str,
                    values=opts,
                    width=100,
                    command=lambda v: self._selected_ep.set(int(v)),
                ).pack(side="left")

            ctk.CTkButton(
                info,
                text="▶  Xem phim",
                height=44,
                width=200,
                fg_color="#e50914",
                hover_color="#b20710",
                font=ctk.CTkFont(size=16, weight="bold"),
                command=self._start_watch,
            ).pack(anchor="w", pady=(16, 0))
        elif not m.get("canWatch"):
            ctk.CTkLabel(
                info,
                text=f"Cần đăng nhập hoặc VIP để xem ({m.get('accessReason')})",
                text_color="#fbbf24",
                wraplength=480,
                justify="left",
            ).pack(anchor="w", pady=(12, 0))
        else:
            ctk.CTkLabel(
                info,
                text="Chưa có nguồn phát từ phimapi. Thử lại sau.",
                text_color="#f87171",
            ).pack(anchor="w", pady=(12, 0))

        ctk.CTkLabel(
            self.body,
            text=(m.get("content") or "")[:1500],
            wraplength=720,
            justify="left",
        ).pack(anchor="w", pady=12)

        self.status.configure(text="")
        mid = str(m.get("id") or "").strip()
        if mid:
            self.after(100, lambda mid=mid: self._build_ratings(mid))
            self.after(150, lambda mid=mid: self._build_comments(mid))

    def _start_watch(self):
        if not self.movie.get("canWatch"):
            self.status.configure(text="Bạn không có quyền xem phim này.")
            return
        eps = parse_episode_links(self.movie)
        if not eps:
            self.status.configure(text="Không có link phát.")
            return
        ep = self._selected_ep.get()
        self.on_watch(self.slug, self.movie, ep)

    def _build_ratings(self, movie_id: str):
        if not movie_id:
            return
        box = ctk.CTkFrame(self.body)
        box.pack(anchor="w", fill="x", pady=12)
        ctk.CTkLabel(box, text="Đánh giá", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=8, pady=4)
        try:
            r = api_client.api("GET", f"/api/ratings/movie/{movie_id}")
            ctk.CTkLabel(box, text=f"★ {r.get('average', 0)} ({r.get('count', 0)} lượt)").pack(
                anchor="w", padx=8
            )
            if self.user:
                star_row = ctk.CTkFrame(box, fg_color="transparent")
                star_row.pack(anchor="w", padx=8, pady=4)
                mine = r.get("userStars")
                for s in range(1, 6):
                    label = f"[{s}★]" if s == mine else f"{s}★"
                    ctk.CTkButton(
                        star_row,
                        text=label,
                        width=40,
                        command=lambda stars=s: self._rate(movie_id, stars),
                    ).pack(side="left", padx=2)
        except api_client.ApiError as e:
            ctk.CTkLabel(box, text=str(e), text_color="#f87171").pack(anchor="w", padx=8)

    def _rate(self, movie_id: str, stars: int):
        try:
            api_client.api("POST", f"/api/ratings/movie/{movie_id}", json_body={"stars": stars})
            self._render()
        except api_client.ApiError as e:
            self.status.configure(text=str(e))

    def _build_comments(self, movie_id: str):
        if not movie_id:
            return
        box = ctk.CTkFrame(self.body)
        box.pack(anchor="w", fill="x", pady=8)
        ctk.CTkLabel(box, text="Bình luận", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=8, pady=4
        )
        self.comment_list = ctk.CTkFrame(box, fg_color="transparent")
        self.comment_list.pack(fill="x", padx=8)
        if self.user:
            entry_row = ctk.CTkFrame(box, fg_color="transparent")
            entry_row.pack(fill="x", padx=8, pady=8)
            self.comment_entry = ctk.CTkEntry(entry_row, placeholder_text="Viết bình luận...", width=400)
            self.comment_entry.pack(side="left", padx=(0, 8))
            ctk.CTkButton(
                entry_row, text="Gửi", width=60, command=lambda: self._post_comment(movie_id)
            ).pack(side="left")
        self._load_comments(movie_id)

    def _load_comments(self, movie_id: str):
        for w in self.comment_list.winfo_children():
            w.destroy()
        try:
            data = api_client.api("GET", f"/api/comments/movie/{movie_id}")
            for c in data.get("items") or []:
                u = (c.get("user") or {}).get("displayName") or "?"
                line = f"{u}: {(c.get('body') or '')[:200]}"
                ctk.CTkLabel(self.comment_list, text=line, wraplength=680, justify="left").pack(
                    anchor="w", pady=2
                )
        except api_client.ApiError as e:
            ctk.CTkLabel(self.comment_list, text=str(e), text_color="#f87171").pack(anchor="w")

    def _post_comment(self, movie_id: str):
        body = self.comment_entry.get().strip()
        if not body:
            return
        try:
            api_client.api("POST", f"/api/comments/movie/{movie_id}", json_body={"body": body})
            self.comment_entry.delete(0, "end")
            self._load_comments(movie_id)
        except api_client.ApiError as e:
            self.status.configure(text=str(e))

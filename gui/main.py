import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _run_app() -> None:
    """Khởi chạy Tk trên thread STA (Windows) để WebView2 hoạt động."""
    import customtkinter as ctk

    from gui import api_client
    from gui.views.admin_panel import AdminPanelFrame
    from gui.views.history_view import HistoryFrame
    from gui.views.home import HomeFrame
    from gui.views.login import LoginFrame
    from gui.views.movie_detail import MovieDetailFrame
    from gui.views.profile import ProfileFrame
    from gui.views.watch import WatchFrame
    from gui.worker import run_bg

    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.title("PHIMHAY-GUI")
            self.geometry("1100x760")
            self.minsize(900, 600)
            self.user = None
            self.container = ctk.CTkFrame(self)
            self.container.pack(fill="both", expand=True)
            self.shell = None
            self.main = None
            self.sidebar = None
            self.status_bar = None
            self._movie_cache: dict[str, dict] = {}
            self._in_watch = False
            self._show_boot()

        def _clear(self):
            for w in self.container.winfo_children():
                w.destroy()
            self.shell = None
            self.main = None
            self.sidebar = None
            self.status_bar = None
            self._in_watch = False

        def _show_boot(self):
            self._clear()
            token = api_client.get_token()
            if not token:
                LoginFrame(self.container, on_success=self._enter_main).pack(fill="both", expand=True)
                return
            try:
                self.user = api_client.api("GET", "/api/auth/me")
                self._enter_main(self.user)
            except api_client.ApiError:
                api_client.set_token(None)
                LoginFrame(self.container, on_success=self._enter_main).pack(fill="both", expand=True)

        def _enter_main(self, user):
            self.user = user
            self._build_shell()
            self._show_home()

        def _build_shell(self):
            if self.shell and self.main:
                return
            if not self.shell:
                self._clear()
                self.shell = ctk.CTkFrame(self.container)
                self.shell.pack(fill="both", expand=True)
                self.sidebar = ctk.CTkFrame(self.shell, width=200)
                self.sidebar.pack(side="left", fill="y")
                self.sidebar.pack_propagate(False)

                name = (self.user or {}).get("displayName") or "User"
                role = (self.user or {}).get("role") or "user"
                ctk.CTkLabel(
                    self.sidebar, text=name, font=ctk.CTkFont(weight="bold"), wraplength=180
                ).pack(pady=(16, 4), padx=8)
                ctk.CTkLabel(self.sidebar, text=role, text_color="#64748b").pack(pady=(0, 12))

                for label, cmd in (
                    ("Trang chủ", self._show_home),
                    ("Lịch sử", self._show_history),
                    ("Hồ sơ", self._show_profile),
                ):
                    ctk.CTkButton(self.sidebar, text=label, command=cmd).pack(fill="x", padx=8, pady=4)

                if (self.user or {}).get("isAdmin"):
                    ctk.CTkButton(
                        self.sidebar, text="Quản trị", fg_color="#4338ca", command=self._show_admin
                    ).pack(fill="x", padx=8, pady=(16, 4))

                ctk.CTkButton(self.sidebar, text="Đăng xuất", command=self._logout).pack(
                    fill="x", padx=8, pady=(24, 8)
                )

                self.main = ctk.CTkFrame(self.shell)
                self.main.pack(side="left", fill="both", expand=True)

            self._ensure_chrome_visible(True)
            self._ensure_status_bar()

        def _ensure_status_bar(self):
            if self.status_bar and self.status_bar.winfo_exists():
                return
            self.status_bar = ctk.CTkFrame(self, height=28)
            self.status_bar.pack(fill="x", side="bottom")
            self._status_lbl = ctk.CTkLabel(self.status_bar, text="Đang kết nối API…")
            self._status_lbl.pack(side="left", padx=8)

            def fetch():
                h = api_client.api("GET", "/api/health")
                pub = api_client.api("GET", "/api/settings/public")
                return h, pub

            def ok(res):
                h, pub = res
                db_ok = "DB OK" if h.get("db") else "DB lỗi"
                site = pub.get("siteName") or "PHIMHAY-GUI"
                if self.status_bar and self.status_bar.winfo_exists():
                    self._status_lbl.configure(
                        text=f"{site} | API OK | {db_ok} | {api_client.api_base()}"
                    )

            def err(e):
                if self.status_bar and self.status_bar.winfo_exists():
                    self._status_lbl.configure(text=str(e), text_color="#f87171")

            run_bg(self, fetch, ok, err)

        def _ensure_chrome_visible(self, visible: bool):
            self._in_watch = not visible
            if not self.shell or not self.sidebar:
                return
            if visible:
                if not self.sidebar.winfo_ismapped():
                    self.sidebar.pack(side="left", fill="y", before=self.main)
                if self.status_bar and not self.status_bar.winfo_ismapped():
                    self.status_bar.pack(fill="x", side="bottom")
                self.bind("<Escape>", lambda _e: None)
            else:
                self.sidebar.pack_forget()
                if self.status_bar:
                    self.status_bar.pack_forget()

        def _clear_main(self):
            if self.main:
                for w in self.main.winfo_children():
                    w.destroy()

        def _cache_movie(self, slug: str, movie: dict):
            self._movie_cache[slug] = movie

        def _show_home(self):
            self._build_shell()
            self._ensure_chrome_visible(True)
            self._clear_main()
            HomeFrame(self.main, self.user, on_open_detail=self._show_detail).pack(
                fill="both", expand=True
            )

        def _show_history(self):
            self._build_shell()
            self._ensure_chrome_visible(True)
            self._clear_main()
            HistoryFrame(self.main, on_open_detail=self._show_detail).pack(fill="both", expand=True)

        def _show_profile(self):
            self._build_shell()
            self._ensure_chrome_visible(True)
            self._clear_main()
            ProfileFrame(self.main, self.user or {}, on_updated=self._on_profile_updated).pack(
                fill="both", expand=True
            )

        def _show_admin(self):
            self._build_shell()
            self._ensure_chrome_visible(True)
            self._clear_main()
            AdminPanelFrame(self.main).pack(fill="both", expand=True)

        def _on_profile_updated(self, user):
            self.user = user

        def _show_detail(self, slug: str):
            self._build_shell()
            self._ensure_chrome_visible(True)
            self._clear_main()
            bar = ctk.CTkFrame(self.main, fg_color="transparent")
            bar.pack(fill="x", padx=8, pady=4)
            ctk.CTkButton(bar, text="← Trang chủ", width=100, command=self._show_home).pack(side="left")
            MovieDetailFrame(
                self.main,
                slug,
                self.user,
                on_watch=self._show_watch,
                cached_movie=self._movie_cache.get(slug),
                on_cached=self._cache_movie,
            ).pack(fill="both", expand=True)

        def _show_watch(self, slug: str, movie: dict, episode: int):
            self._cache_movie(slug, movie)
            self._build_shell()
            self._ensure_chrome_visible(False)
            self._clear_main()
            frame = WatchFrame(
                self.main,
                slug,
                movie,
                self.user,
                initial_episode=episode,
                on_back=lambda: self._show_detail(slug),
            )
            frame.pack(fill="both", expand=True)
            self.bind("<Escape>", lambda _e: frame._on_escape())

        def _logout(self):
            api_client.set_token(None)
            self.user = None
            self._movie_cache.clear()
            self._show_boot()

    App().mainloop()


def _start_sta_thread(target) -> None:
    import clr

    clr.AddReference("System.Threading")
    from System.Threading import ApartmentState, Thread, ThreadStart

    t = Thread(ThreadStart(target))
    t.ApartmentState = ApartmentState.STA
    t.Start()
    t.Join()


def main():
    if sys.platform == "win32":
        try:
            _start_sta_thread(_run_app)
            return
        except Exception:
            pass
    _run_app()


if __name__ == "__main__":
    main()

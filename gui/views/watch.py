"""Trang xem phim — Netflix mobile style, một cửa sổ."""
from __future__ import annotations

import tkinter as tk
import webbrowser

import customtkinter as ctk

from gui import api_client
from gui.video_player import EmbeddedVideoPlayer, resolve_player_url
from gui.worker import run_bg


def parse_episode_links(movie: dict) -> list[tuple[int, str, str, str]]:
    """(episode_num, stream_url, embed_url, label)"""
    out: list[tuple[int, str, str, str]] = []
    for server in movie.get("episodes") or []:
        sname = server.get("server_name") or ""
        for ep in server.get("server_data") or []:
            m3u8 = (ep.get("link_m3u8") or "").strip()
            embed = (ep.get("link_embed") or "").strip()
            if not m3u8 and not embed:
                continue
            name = ep.get("name") or f"Tập {len(out) + 1}"
            try:
                num = int(str(name).replace("Tập", "").strip().split()[0])
            except ValueError:
                num = len(out) + 1
            label = f"{name}" + (f" ({sname})" if sname else "")
            stream = m3u8 or embed
            out.append((num, stream, embed, label))
    if not out:
        return out
    seen = set()
    uniq = []
    for item in out:
        if item[0] in seen:
            continue
        seen.add(item[0])
        uniq.append(item)
    return sorted(uniq, key=lambda x: x[0])


def _fmt_ms(ms: int) -> str:
    if ms < 0:
        ms = 0
    total = ms // 1000
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class WatchFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        slug: str,
        movie: dict,
        user: dict | None,
        *,
        initial_episode: int | None,
        on_back,
    ):
        super().__init__(master, fg_color="#0a0a0a")
        self.slug = slug
        self.movie = movie
        self.user = user
        self.on_back = on_back
        self.episodes = parse_episode_links(movie)
        self._current_ep = initial_episode or (self.episodes[0][0] if self.episodes else 1)
        self._player: EmbeddedVideoPlayer | None = None
        self._browser_url = ""
        self._seek_drag = False
        self._tick_job: str | None = None
        self._fullscreen = False
        self._key_bindids: list[tuple[str, str]] = []
        self.fullscreen_btn = None

        top = ctk.CTkFrame(self, fg_color="#0a0a0a", height=48)
        top.pack(fill="x", padx=8, pady=(8, 0))
        self._top_bar = top
        ctk.CTkButton(
            top,
            text="←",
            width=40,
            height=36,
            fg_color="transparent",
            hover_color="#333",
            font=ctk.CTkFont(size=22),
            command=self._go_back,
        ).pack(side="left")
        title = movie.get("title") or slug
        ctk.CTkLabel(
            top,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f5f5f5",
        ).pack(side="left", padx=8)

        self.ep_label = ctk.CTkLabel(top, text="", text_color="#94a3b8")
        self.ep_label.pack(side="right", padx=12)

        self.video_outer = ctk.CTkFrame(self, fg_color="#000000", corner_radius=4, height=480)
        self.video_outer.pack(fill="both", expand=True, padx=16, pady=12)
        self.video_outer.pack_propagate(False)
        self._video_tk = tk.Frame(self.video_outer, bg="#000000", highlightthickness=0)
        self._video_tk.pack(fill="both", expand=True, padx=2, pady=2)

        self.controls = ctk.CTkFrame(self, fg_color="#141414", corner_radius=6)
        self.controls.pack(fill="x", padx=16, pady=(0, 8))

        row1 = ctk.CTkFrame(self.controls, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(8, 4))
        self.play_btn = ctk.CTkButton(
            row1, text="▶", width=44, command=self._toggle_play, state="disabled"
        )
        self.play_btn.pack(side="left")
        self.time_cur = ctk.CTkLabel(row1, text="00:00", width=52, text_color="#cbd5e1")
        self.time_cur.pack(side="left", padx=(8, 4))
        self.seek_slider = ctk.CTkSlider(
            row1,
            from_=0,
            to=1,
            number_of_steps=1000,
            command=self._on_seek_drag,
            state="disabled",
        )
        self.seek_slider.set(0)
        self.seek_slider.pack(side="left", fill="x", expand=True, padx=4)
        self.seek_slider.bind("<ButtonPress-1>", lambda _e: self._seek_drag_start())
        self.seek_slider.bind("<ButtonRelease-1>", lambda _e: self._seek_drag_end())
        self.time_total = ctk.CTkLabel(row1, text="00:00", width=52, text_color="#cbd5e1")
        self.time_total.pack(side="left", padx=(4, 8))

        row2 = ctk.CTkFrame(self.controls, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(row2, text="Âm lượng", text_color="#94a3b8").pack(side="left")
        self.vol_slider = ctk.CTkSlider(
            row2,
            from_=0,
            to=100,
            width=140,
            command=self._on_volume,
            state="disabled",
        )
        self.vol_slider.set(85)
        self.vol_slider.pack(side="left", padx=8)
        ctk.CTkButton(row2, text="−10s", width=56, command=lambda: self._seek_delta(-10_000)).pack(
            side="left", padx=4
        )
        ctk.CTkButton(row2, text="+10s", width=56, command=lambda: self._seek_delta(10_000)).pack(
            side="left", padx=4
        )
        self.fullscreen_btn = ctk.CTkButton(
            row2,
            text="⛶",
            width=44,
            height=32,
            font=ctk.CTkFont(size=18),
            fg_color="#334155",
            command=self._toggle_fullscreen,
        )
        self.fullscreen_btn.pack(side="right")

        self.player_status = ctk.CTkLabel(self, text="", text_color="#94a3b8")
        self.player_status.pack(pady=2)
        self.error_lbl = ctk.CTkLabel(self, text="", text_color="#f87171", wraplength=700)
        self.error_lbl.pack(pady=4)

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(pady=(0, 8))
        self._action_row = action_row
        ctk.CTkButton(
            action_row,
            text="Mở trình duyệt (player web)",
            fg_color="#334155",
            hover_color="#475569",
            command=self._open_in_browser,
        ).pack()

        self._ep_bar = None
        if len(self.episodes) > 1:
            ep_bar = ctk.CTkScrollableFrame(self, height=72, fg_color="#141414", orientation="horizontal")
            ep_bar.pack(fill="x", padx=16, pady=(0, 12))
            self._ep_bar = ep_bar
            for num, _stream, _embed, label in self.episodes:
                ctk.CTkButton(
                    ep_bar,
                    text=str(num),
                    width=44,
                    height=44,
                    fg_color="#333" if num != self._current_ep else "#e50914",
                    hover_color="#555",
                    command=lambda n=num: self._play_episode(n),
                ).pack(side="left", padx=4, pady=8)

        self._bind_keys()
        self._video_tk.bind("<Double-Button-1>", self._on_video_double_click, add="+")
        self.after(200, lambda: self._play_episode(self._current_ep))

    def _bind_keys(self) -> None:
        """bind_all để phím vẫn hoạt động khi VLC giữ focus."""
        root = self.winfo_toplevel()
        bindings = (
            ("<Escape>", self._on_escape),
            ("<Key-space>", self._on_space),
            ("<Key-f>", self._toggle_fullscreen),
            ("<Key-F>", self._toggle_fullscreen),
            ("<Left>", self._on_key_left),
            ("<Right>", self._on_key_right),
            ("<Up>", self._on_key_up),
            ("<Down>", self._on_key_down),
        )
        for seq, fn in bindings:
            bid = root.bind_all(seq, fn, add="+")
            self._key_bindids.append((seq, bid))

    def _unbind_keys(self) -> None:
        root = self.winfo_toplevel()
        for seq, _bid in self._key_bindids:
            try:
                root.unbind_all(seq)
            except Exception:
                pass
        self._key_bindids.clear()

    def _on_key_left(self, _event=None):
        self._seek_delta(-10_000)
        return "break"

    def _on_key_right(self, _event=None):
        self._seek_delta(10_000)
        return "break"

    def _on_key_up(self, _event=None):
        self._bump_volume(8)
        return "break"

    def _on_key_down(self, _event=None):
        self._bump_volume(-8)
        return "break"

    def _on_video_double_click(self, _event=None):
        self._toggle_fullscreen()
        return "break"

    def _on_escape(self, _event=None):
        if self._fullscreen:
            self._toggle_fullscreen()
            return "break"
        self._go_back()
        return "break"

    def _on_space(self, _event=None):
        if self._player and self._player.mode == "vlc":
            self._toggle_play()
            return "break"
        return None

    def _set_controls_vlc(self, enabled: bool) -> None:
        st = "normal" if enabled else "disabled"
        self.play_btn.configure(state=st)
        self.seek_slider.configure(state=st)
        self.vol_slider.configure(state=st)

    def _on_player_mode(self, mode: str) -> None:
        self._set_controls_vlc(mode == "vlc")
        if mode == "vlc":
            self._start_tick()
            if self._player:
                self.vol_slider.set(self._player.get_volume())
        else:
            self._stop_tick()
            self.play_btn.configure(text="▶")

    def _start_tick(self) -> None:
        self._stop_tick()
        self._tick()

    def _stop_tick(self) -> None:
        if self._tick_job:
            try:
                self.after_cancel(self._tick_job)
            except Exception:
                pass
            self._tick_job = None

    def _tick(self) -> None:
        if not self.winfo_exists():
            return
        p = self._player
        if p and p.mode == "vlc":
            state = p.vlc_state_label()
            if state == "loading":
                self.player_status.configure(text="Đang tải phim…")
            elif state == "playing":
                self.player_status.configure(text="")
                self.play_btn.configure(text="⏸")
            elif state == "paused":
                self.player_status.configure(text="")
                self.play_btn.configure(text="▶")
            elif state == "ended":
                self.play_btn.configure(text="▶")

            length = p.get_length_ms()
            pos = p.get_time_ms()
            if length > 0:
                self.time_total.configure(text=_fmt_ms(length))
                if not self._seek_drag:
                    self.seek_slider.set(min(1.0, max(0.0, pos / length)))
            self.time_cur.configure(text=_fmt_ms(pos))

        self._tick_job = self.after(350, self._tick)

    def _toggle_play(self) -> None:
        if not self._player or self._player.mode != "vlc":
            return
        playing = self._player.toggle_pause()
        self.play_btn.configure(text="▶" if playing is False else "⏸")

    def _on_seek_drag(self, value: float) -> None:
        if not self._seek_drag or not self._player or self._player.mode != "vlc":
            return
        self._player.set_position(float(value))

    def _seek_drag_start(self) -> None:
        self._seek_drag = True

    def _seek_drag_end(self) -> None:
        self._seek_drag = False
        if self._player and self._player.mode == "vlc":
            self._player.set_position(self.seek_slider.get())

    def _seek_delta(self, ms: int) -> None:
        if self._player and self._player.mode == "vlc":
            self._player.seek_relative_ms(ms)

    def _on_volume(self, value: float) -> None:
        if self._player and self._player.mode == "vlc":
            self._player.set_volume(int(value))

    def _bump_volume(self, delta: int) -> None:
        if not self._player or self._player.mode != "vlc":
            return
        v = max(0, min(100, self._player.get_volume() + delta))
        self.vol_slider.set(v)
        self._player.set_volume(v)

    def _toggle_fullscreen(self, _event=None) -> None:
        root = self.winfo_toplevel()
        self._fullscreen = not self._fullscreen
        root.attributes("-fullscreen", self._fullscreen)
        if self._fullscreen:
            self.controls.pack_forget()
            for w in (self._top_bar, self.player_status, self.error_lbl, self._action_row):
                w.pack_forget()
            if self._ep_bar:
                self._ep_bar.pack_forget()
            self.video_outer.pack_forget()
            self.video_outer.pack(fill="both", expand=True, padx=0, pady=0)
            # Thanh điều khiển dưới video (VLC che mọi widget đè lên video)
            self.controls.pack(fill="x", side="bottom", padx=12, pady=(0, 10))
        else:
            self.controls.pack_forget()
            self._restore_layout()
        self.after(250, self._refresh_vlc_embed)

    def _restore_layout(self) -> None:
        self.video_outer.pack_forget()
        self._top_bar.pack(fill="x", padx=8, pady=(8, 0))
        self.video_outer.pack(fill="both", expand=True, padx=16, pady=12)
        self.controls.pack(fill="x", padx=16, pady=(0, 8))
        self.player_status.pack(pady=2)
        self.error_lbl.pack(pady=4)
        self._action_row.pack(pady=(0, 8))
        if self._ep_bar:
            self._ep_bar.pack(fill="x", padx=16, pady=(0, 12))

    def _refresh_vlc_embed(self) -> None:
        if self._player:
            self._player.refresh_window()

    def _go_back(self):
        if self._fullscreen:
            self._toggle_fullscreen()
        self._unbind_keys()
        self._stop_tick()
        if self._player:
            self._player.stop()
        self.on_back()

    def _open_in_browser(self):
        url = (self._player.last_url if self._player else "") or self._browser_url
        if url.startswith("http"):
            webbrowser.open(url)
        else:
            self.error_lbl.configure(text="Chưa có link phát cho tập này.")

    def _play_episode(self, ep_num: int):
        self.error_lbl.configure(text="")
        stream_url = ""
        embed_url = ""
        label = f"Tập {ep_num}"
        for num, stream, embed, lab in self.episodes:
            if num == ep_num:
                stream_url = stream
                embed_url = embed
                label = lab
                break
        self._current_ep = ep_num
        self.ep_label.configure(text=label)
        self._browser_url = resolve_player_url(stream_url, embed_url or None)

        if not stream_url and not embed_url:
            self.error_lbl.configure(
                text="Không có nguồn phát cho tập này. Thử tập khác hoặc kiểm tra quyền xem (VIP/đăng nhập)."
            )
            return

        mid = self.movie.get("id")
        if self.user and mid:

            def save_hist():
                api_client.api(
                    "POST",
                    "/api/history",
                    json_body={"movieId": mid, "episode": ep_num, "currentTime": 1},
                )

            run_bg(self, save_hist, lambda _r: None, lambda _e: None)

        self.player_status.configure(text="Đang mở player…")
        self.error_lbl.configure(text="")
        self.seek_slider.set(0)
        self.time_cur.configure(text="00:00")
        self.time_total.configure(text="00:00")

        if self._player is None:

            def on_player_err(msg: str):
                self.player_status.configure(text="")
                self.error_lbl.configure(text=msg)

            self._player = EmbeddedVideoPlayer(
                self._video_tk,
                on_error=on_player_err,
                on_mode_change=self._on_player_mode,
            )

        def start():
            self._video_tk.update_idletasks()
            self._player.play(stream_url, embed_url=embed_url or None)
            if self.winfo_exists():
                self.after(15000, self._warn_if_stuck)

        self.after(50, start)

    def _warn_if_stuck(self):
        if not self.winfo_exists():
            return
        if self._player and self._player.mode == "none":
            self.error_lbl.configure(
                text="Player chưa chạy được trong app. Bấm «Mở trình duyệt» để xem phim."
            )

    def destroy(self):
        self._unbind_keys()
        self._stop_tick()
        if self._player:
            self._player.stop()
        super().destroy()

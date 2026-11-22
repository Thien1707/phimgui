"""Trình phát nhúng: VLC (m3u8) → WebView2 → hướng dẫn mở trình duyệt."""
from __future__ import annotations

import os
import sys
import tkinter as tk
from pathlib import Path
from typing import Callable
from urllib.parse import quote

PHIMAPI_PLAYER = "https://player.phimapi.com/player/?url="
_ROOT = Path(__file__).resolve().parent.parent
_WEBVIEW2_PROFILE = _ROOT / ".webview2_profile"
_vlc_shared = None

# Buffer nhỏ hơn → bắt đầu phát nhanh hơn (HLS VOD).
_VLC_INSTANCE_ARGS = (
    "--network-caching=1200",
    "--live-caching=1200",
    "--http-reconnect",
    "--quiet",
)
_VLC_MEDIA_OPTS = (
    ":network-caching=1200",
    ":live-caching=1200",
    ":http-reconnect",
)


def _is_hls_or_direct(url: str) -> bool:
    u = (url or "").lower()
    return ".m3u8" in u or u.endswith(".mp4") or u.endswith(".mkv")


def resolve_player_url(stream_url: str, embed_url: str | None) -> str:
    """URL mở trong WebView2 / trình duyệt."""
    embed_url = (embed_url or "").strip()
    stream_url = (stream_url or "").strip()
    if stream_url.startswith("http") and _is_hls_or_direct(stream_url):
        return PHIMAPI_PLAYER + quote(stream_url, safe="")
    if embed_url.startswith("http"):
        return embed_url
    if stream_url.startswith("http"):
        return stream_url
    return ""


def _prepare_webview2_env() -> None:
    try:
        _WEBVIEW2_PROFILE.mkdir(parents=True, exist_ok=True)
        os.environ["WEBVIEW2_USER_DATA_FOLDER"] = str(_WEBVIEW2_PROFILE.resolve())
    except OSError:
        pass


def _python_bitness() -> int:
    return 64 if sys.maxsize > 2**32 else 32


def _vlc_dirs_windows() -> list[str]:
    dirs: list[str] = []
    if os.environ.get("VLC_HOME"):
        dirs.append(os.environ["VLC_HOME"])
    if _python_bitness() == 64:
        dirs.extend(
            (
                r"C:\Program Files\VideoLAN\VLC",
                r"C:\Program Files (x86)\VideoLAN\VLC",
            )
        )
    else:
        dirs.extend(
            (
                r"C:\Program Files (x86)\VideoLAN\VLC",
                r"C:\Program Files\VideoLAN\VLC",
            )
        )
    return dirs


def _configure_vlc_windows() -> tuple[bool, str]:
    """Trả về (ok, ghi chú lỗi nếu có)."""
    if sys.platform != "win32":
        return True, ""
    saw_x86_only = False
    for vlc_dir in _vlc_dirs_windows():
        if not vlc_dir or not os.path.isdir(vlc_dir):
            continue
        dll = os.path.join(vlc_dir, "libvlc.dll")
        if not os.path.isfile(dll):
            continue
        if _python_bitness() == 64 and "(x86)" in vlc_dir.replace("/", "\\"):
            saw_x86_only = True
            continue
        os.environ["PATH"] = vlc_dir + os.pathsep + os.environ.get("PATH", "")
        os.environ["VLC_PLUGIN_PATH"] = os.path.join(vlc_dir, "plugins")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(vlc_dir)
        return True, ""
    if saw_x86_only:
        return False, (
            "Bạn cài VLC bản 32-bit (x86). App Python 64-bit cần VLC 64-bit: "
            "gỡ VLC cũ → tải lại tại videolan.org (Windows 64-bit)."
        )
    return False, "Chưa tìm thấy VLC. Cài tại videolan.org rồi khởi động lại app."


def _get_vlc_instance():
    global _vlc_shared
    if _vlc_shared is not None:
        return _vlc_shared
    import vlc

    if sys.platform == "win32":
        ok, _ = _configure_vlc_windows()
        if not ok:
            return None
    _vlc_shared = vlc.Instance(*_VLC_INSTANCE_ARGS)
    return _vlc_shared


class EmbeddedVideoPlayer:
    def __init__(
        self,
        host: tk.Frame,
        on_error: Callable[[str], None] | None = None,
        on_mode_change: Callable[[str], None] | None = None,
    ):
        self.host = host
        self.on_error = on_error
        self.on_mode_change = on_mode_change
        self._vlc_instance = None
        self._vlc_player = None
        self._webview2 = None
        self.last_url = ""
        self._vlc_hint = ""
        self._mode = "none"

    @property
    def mode(self) -> str:
        return self._mode

    def _set_mode(self, mode: str) -> None:
        if mode == self._mode:
            return
        self._mode = mode
        if self.on_mode_change:
            self.on_mode_change(mode)

    def play(self, stream_url: str, embed_url: str | None = None) -> None:
        self.stop(keep_vlc=True)
        stream_url = (stream_url or "").strip()
        embed_url = (embed_url or "").strip() or None
        m3u8 = stream_url if _is_hls_or_direct(stream_url) else ""
        if not m3u8 and embed_url and _is_hls_or_direct(embed_url):
            m3u8 = embed_url

        player_page = resolve_player_url(stream_url, embed_url)
        self.last_url = player_page or stream_url or (embed_url or "")

        if not self.last_url:
            self._fail("Không có link phát.")
            return

        if m3u8 and self._play_vlc(m3u8):
            return

        vlc_extra = f" {self._vlc_hint}" if self._vlc_hint else ""

        if (
            player_page
            and sys.platform == "win32"
            and os.environ.get("PHIMHAY_DISABLE_WEBVIEW2", "") != "1"
        ):
            if self._play_webview2(player_page):
                return
            alt = (embed_url or "").strip()
            if alt.startswith("http") and alt != player_page and self._play_webview2(alt):
                self.last_url = alt
                return

        self._fail(
            "Không mở được player trong app. Bấm «Mở trình duyệt» bên dưới."
            + vlc_extra
        )

    def _play_webview2(self, url: str) -> bool:
        try:
            _prepare_webview2_env()
            from tkwebview2.tkwebview2 import WebView2

            self.host.update_idletasks()
            w = max(640, self.host.winfo_width() or 640)
            h = max(360, self.host.winfo_height() or 360)
            self._webview2 = WebView2(self.host, width=w, height=h, url=url)
            self._webview2.pack(fill="both", expand=True)
            self._set_mode("webview")
            return True
        except Exception:
            self._webview2 = None
            return False

    def _play_vlc(self, url: str) -> bool:
        self._vlc_hint = ""
        if sys.platform == "win32":
            ok, note = _configure_vlc_windows()
            if not ok:
                self._vlc_hint = note
                return False
        try:
            import vlc
        except (ImportError, OSError, FileNotFoundError) as e:
            if sys.platform == "win32" and "193" in str(e):
                self._vlc_hint = (
                    " VLC 32-bit không tương thích Python 64-bit — cài VLC bản 64-bit."
                )
            return False
        try:
            inst = _get_vlc_instance()
            if inst is None:
                return False
            self._vlc_instance = inst
            if self._vlc_player is None:
                self._vlc_player = self._vlc_instance.media_player_new()
            media = self._vlc_instance.media_new(url)
            for opt in _VLC_MEDIA_OPTS:
                media.add_option(opt)
            self._vlc_player.set_media(media)
            self.host.update_idletasks()
            wid = self.host.winfo_id()
            if sys.platform == "win32":
                self._vlc_player.set_hwnd(wid)
            elif sys.platform.startswith("linux"):
                self._vlc_player.set_xwindow(wid)
            elif sys.platform == "darwin":
                self._vlc_player.set_nsobject(wid)
            if self._vlc_player.audio_get_volume() < 0:
                self._vlc_player.audio_set_volume(85)
            self._vlc_player.play()
            self._set_mode("vlc")
            return True
        except Exception:
            self._vlc_player = None
            return False

    def toggle_pause(self) -> bool | None:
        """True = đang phát, False = tạm dừng, None = không VLC."""
        if not self._vlc_player:
            return None
        if self._vlc_player.is_playing():
            self._vlc_player.pause()
            return False
        self._vlc_player.play()
        return True

    def set_pause(self, paused: bool) -> None:
        if not self._vlc_player:
            return
        playing = bool(self._vlc_player.is_playing())
        if paused and playing:
            self._vlc_player.pause()
        elif not paused and not playing:
            self._vlc_player.play()

    def get_volume(self) -> int:
        if not self._vlc_player:
            return 85
        v = self._vlc_player.audio_get_volume()
        return max(0, min(100, int(v))) if v >= 0 else 85

    def set_volume(self, volume: int) -> None:
        if not self._vlc_player:
            return
        self._vlc_player.audio_set_volume(max(0, min(100, int(volume))))

    def get_time_ms(self) -> int:
        if not self._vlc_player:
            return 0
        t = self._vlc_player.get_time()
        return max(0, int(t)) if t and t > 0 else 0

    def get_length_ms(self) -> int:
        if not self._vlc_player:
            return 0
        ln = self._vlc_player.get_length()
        return max(0, int(ln)) if ln and ln > 0 else 0

    def set_position(self, fraction: float) -> None:
        if not self._vlc_player:
            return
        f = max(0.0, min(1.0, float(fraction)))
        self._vlc_player.set_position(f)

    def seek_relative_ms(self, delta_ms: int) -> None:
        if not self._vlc_player:
            return
        cur = self.get_time_ms()
        ln = self.get_length_ms()
        target = cur + delta_ms
        if ln > 0:
            target = max(0, min(ln, target))
            self.set_position(target / ln)
        else:
            self._vlc_player.set_time(max(0, target))

    def refresh_window(self) -> None:
        """Gắn lại VLC sau khi đổi kích thước / toàn màn hình."""
        if not self._vlc_player:
            return
        try:
            self.host.update_idletasks()
            wid = self.host.winfo_id()
            if sys.platform == "win32":
                self._vlc_player.set_hwnd(wid)
            elif sys.platform.startswith("linux"):
                self._vlc_player.set_xwindow(wid)
            elif sys.platform == "darwin":
                self._vlc_player.set_nsobject(wid)
        except Exception:
            pass

    def vlc_state_label(self) -> str:
        if not self._vlc_player:
            return "none"
        try:
            import vlc

            st = self._vlc_player.get_state()
            if st in (vlc.State.Opening, vlc.State.Buffering):
                return "loading"
            if st == vlc.State.Playing:
                return "playing"
            if st == vlc.State.Paused:
                return "paused"
            if st == vlc.State.Ended:
                return "ended"
            return "other"
        except Exception:
            return "other"

    def stop(self, *, keep_vlc: bool = False) -> None:
        if self._vlc_player is not None:
            try:
                self._vlc_player.stop()
            except Exception:
                pass
            if not keep_vlc:
                self._vlc_player = None
        if not keep_vlc:
            self._vlc_instance = None
        self._set_mode("none")
        if self._webview2 is not None:
            try:
                self._webview2.destroy()
            except Exception:
                pass
            self._webview2 = None

    def _fail(self, msg: str) -> None:
        if self.on_error:
            self.on_error(msg)

"""
Icon loader for the pre-extracted icons_white_theme folder.
Files are named icon_r{ROW:02d}_c{COL:02d}.png  (1-indexed).

Rows/cols correspond to the same 7x7 grid as the original sprite sheet.
"""

import os
import sys
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QSize


# ---------------------------------------------------------------------------
# Grid mapping  (row, col) — 0-indexed internally, +1 for filenames
# ---------------------------------------------------------------------------
ICON_MAP = {
    # Row 3 (0-idx) — playback transport
    "skip_back":    (3, 0),
    "step_back":    (3, 1),
    "rewind":       (3, 2),
    "play":         (3, 3),
    "fast_fwd":     (3, 4),
    "step_fwd":     (3, 5),
    "skip_fwd":     (3, 6),
    # Row 4 — transport controls
    "next_track":   (4, 0),
    "shuffle":      (4, 1),
    "stop":         (4, 2),
    "pause":        (4, 3),
    "record":       (4, 4),
    "replay":       (4, 5),
    "eject":        (4, 6),
    # Row 5 — audio tools
    "waveform":     (5, 0),
    "equalizer":    (5, 1),
    "waveform2":    (5, 2),
    "microphone":   (5, 3),
    "headphones":   (5, 4),
    "heart":        (5, 5),
    "star":         (5, 6),
    # Row 6 — actions
    "download":     (6, 0),
    "upload":       (6, 1),
    "broadcast":    (6, 2),
    "settings":     (6, 3),
    "expand":       (6, 5),
    # Row 2 — volume
    "vol_low":      (2, 0),
    "vol_mid":      (2, 1),
    "vol_mute":     (2, 2),
    "vol_up":       (2, 6),
    # Row 1 — misc
    "music":        (1, 2),
    # Row 0
    "power":        (0, 0),
}

# Colour constants kept for API compatibility — no longer used for tinting
DEFAULT_COLOR = (55, 65, 81)
ACCENT_COLOR  = (55, 65, 81)
DANGER_COLOR  = (55, 65, 81)


def _icons_dir() -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", "icons_white_theme")


_cache: dict[tuple, QPixmap] = {}


def get_icon(
    name: str,
    size: int = 28,
    color: tuple = DEFAULT_COLOR,   # kept for signature compatibility, unused
) -> QPixmap:
    """Return a QPixmap for the named icon, scaled to `size` × `size`."""
    cache_key = (name, size)
    if cache_key in _cache:
        return _cache[cache_key]

    row, col = ICON_MAP[name]
    filename = f"icon_r{row + 1:02d}_c{col + 1:02d}.png"
    path = os.path.join(_icons_dir(), filename)

    pm = QPixmap(path)
    if not pm.isNull() and size > 0:
        pm = pm.scaled(size, size, aspectRatioMode=1,  # Qt.KeepAspectRatio
                       transformMode=1)                 # Qt.SmoothTransformation

    _cache[cache_key] = pm
    return pm

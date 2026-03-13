"""
src/presentation/media_loader.py

Loads animated media (GIF, MP4, WebM) and static images into lists of
pygame Surfaces for display in the TaskPopupOverlay.

Supported formats:
- Animated GIF   (.gif)   — frame extraction via Pillow
- Video          (.mp4, .webm) — frame extraction via OpenCV
- Static images  (.png, .jpg, .jpeg, .bmp, .webp) — single-frame list

A module-level cache avoids re-decoding the same file on repeated popup
triggers within the same session.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_GIF_EXTENSIONS: frozenset[str] = frozenset({".gif"})
_VIDEO_EXTENSIONS: frozenset[str] = frozenset({".mp4", ".webm"})

# Safety cap: do not load more than this many frames from a video file.
_MAX_VIDEO_FRAMES: int = 300  # ≈ 10 s at 30 fps

# Pre-scale all frames to this size so the overlay renders without scaling every frame.
_FRAME_WIDTH: int = 240
_FRAME_HEIGHT: int = 240

# Module-level cache: path → (frames, frame_duration_ms)
_cache: dict[Path, tuple[list[Any], float]] = {}


def load_media(path: Path) -> tuple[list[Any], float]:
    """Return ``(frames, frame_duration_ms)`` for the media file at *path*.

    *frames* is a list of ``pygame.Surface`` objects pre-scaled to 240 × 240.
    *frame_duration_ms* is how long each frame should be displayed in
    milliseconds (0.0 for static images).  Returns ``([], 0.0)`` on any
    failure so callers can fall back to the placeholder.

    Results are cached by resolved path so the same file is only decoded once
    per session.
    """
    resolved = path.resolve()
    if resolved in _cache:
        return _cache[resolved]

    if not resolved.exists():
        logger.warning("media_loader: file not found: %s", resolved)
        return [], 0.0

    suffix = resolved.suffix.lower()
    try:
        if suffix in _GIF_EXTENSIONS:
            result = _load_gif(resolved)
        elif suffix in _VIDEO_EXTENSIONS:
            result = _load_video(resolved)
        else:
            result = _load_static(resolved)
    except Exception:  # noqa: BLE001
        logger.warning("media_loader: failed to load %s", resolved, exc_info=True)
        result = [], 0.0

    if result[0]:  # only cache successful loads
        _cache[resolved] = result
    return result


def clear_cache() -> None:
    """Discard all cached frames (e.g. after pygame display is recreated)."""
    _cache.clear()


# ---------------------------------------------------------------------------
# Internal loaders
# ---------------------------------------------------------------------------


def _load_static(path: Path) -> tuple[list[Any], float]:
    """Load a single static image as a one-element frame list."""
    try:
        import pygame as _pygame  # noqa: PLC0415

        surf = _pygame.image.load(str(path)).convert_alpha()
        surf = _pygame.transform.smoothscale(surf, (_FRAME_WIDTH, _FRAME_HEIGHT))
        return [surf], 0.0
    except Exception:  # noqa: BLE001
        logger.debug("media_loader: pygame could not load static image %s", path)
        return [], 0.0


def _load_gif(path: Path) -> tuple[list[Any], float]:
    """Extract all frames from an animated GIF using Pillow.

    Falls back to a single pygame static load when Pillow is unavailable.
    """
    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError:
        logger.debug("media_loader: Pillow not installed — loading GIF as static image")
        return _load_static(path)

    try:
        import pygame as _pygame  # noqa: PLC0415
    except ImportError:
        return [], 0.0

    frames: list[Any] = []
    durations: list[float] = []

    with Image.open(path) as img:
        n_frames: int = getattr(img, "n_frames", 1)
        for frame_idx in range(n_frames):
            img.seek(frame_idx)
            rgba = img.convert("RGBA")
            surf = _pygame.image.frombytes(rgba.tobytes(), rgba.size, "RGBA")
            surf = _pygame.transform.smoothscale(surf, (_FRAME_WIDTH, _FRAME_HEIGHT))
            frames.append(surf)
            durations.append(float(img.info.get("duration", 100)))

    if not frames:
        return [], 0.0

    avg_duration = sum(durations) / len(durations)
    return frames, avg_duration


def _load_video(path: Path) -> tuple[list[Any], float]:
    """Extract frames from an MP4 or WebM file using OpenCV.

    Frames are capped at ``_MAX_VIDEO_FRAMES`` (≈ 10 s at 30 fps) to avoid
    excessive memory use.
    """
    try:
        import cv2  # noqa: PLC0415
    except ImportError:
        logger.warning(
            "media_loader: opencv-python not installed — cannot play video %s", path
        )
        return [], 0.0

    try:
        import pygame as _pygame  # noqa: PLC0415
    except ImportError:
        return [], 0.0

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        logger.warning("media_loader: cv2 could not open %s", path)
        return [], 0.0

    fps: float = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_duration_ms = 1000.0 / fps
    frames: list[Any] = []

    try:
        while len(frames) < _MAX_VIDEO_FRAMES:
            ret, bgr = cap.read()
            if not ret:
                break
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            surf = _pygame.image.frombytes(rgb.tobytes(), (w, h), "RGB")
            surf = _pygame.transform.smoothscale(surf, (_FRAME_WIDTH, _FRAME_HEIGHT))
            frames.append(surf)
    finally:
        cap.release()

    return frames, frame_duration_ms

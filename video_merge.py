"""
Replaces the manual Clipchamp step: mux the Manim render with the Sarvam
TTS audio. If the audio runs longer than the video (usually does, since
narration pacing is unpredictable), the video's last frame is frozen
(ffmpeg tpad filter) for the difference instead of the video looping or
cutting off — this is the "extend the white screen / duplicate the last
static frame" trick you were doing by hand.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _duration_seconds(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def merge(video_path: Path, audio_path: Path, out_path: Path) -> Path:
    video_dur = _duration_seconds(video_path)
    audio_dur = _duration_seconds(audio_path)
    pad_seconds = max(0.0, audio_dur - video_dur + 0.3)  # +0.3s safety buffer

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if pad_seconds > 0:
        filter_complex = (
            f"[0:v]tpad=stop_mode=clone:stop_duration={pad_seconds:.2f}[v]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-c:a", "aac",
            "-shortest",
            str(out_path),
        ]
    else:
        # video already covers the audio — just mux, trimming video to audio length
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-c:a", "aac",
            "-shortest",
            str(out_path),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg merge failed:\n{result.stderr}")

    return out_path

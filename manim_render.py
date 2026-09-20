"""
Writes the Manim code Gemini generated to a .py file and runs it headlessly
(the script calls scene.render() itself, so we just `python <file>`).
Locates the resulting .mp4 under Manim's default media directory.

This replaces the "run it in Colab" step — any machine with `manim` and its
system deps (ffmpeg, a LaTeX distro if MathTex is used) installed can do
this unattended.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


def _extract_scene_class_name(code: str) -> str:
    match = re.search(r"class\s+(\w+)\s*\(\s*Scene\s*\)", code)
    if not match:
        raise ValueError("Could not find a Scene subclass in generated Manim code")
    return match.group(1)


def render_scene(manim_code: str, work_dir: Path) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    script_path = work_dir / "generated_scene.py"
    script_path.write_text(manim_code, encoding="utf-8")

    scene_name = _extract_scene_class_name(manim_code)

    result = subprocess.run(
        ["python", str(script_path)],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Manim render failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    # Manim's default output layout: <cwd>/media/videos/<script_stem>/<res>/<SceneName>.mp4
    media_root = work_dir / "media" / "videos" / script_path.stem
    candidates = list(media_root.rglob(f"{scene_name}.mp4"))
    if not candidates:
        raise FileNotFoundError(
            f"Rendered mp4 not found under {media_root}. "
            f"stdout was:\n{result.stdout}"
        )
    # pick the most recently modified in case of multiple resolutions
    return max(candidates, key=lambda p: p.stat().st_mtime)

"""
The same stages as the original one-shot main.py, but split so a UI can
show a preview before publishing:

  generate_for_preview(topic) -> stops right after uploading the merged
      video to Cloudinary. Returns everything the dashboard needs to show
      a preview: a public video URL, and Gemini's suggested caption/hashtags.

  publish_to_instagram(...) -> takes the (possibly user-edited) caption and
      the video_url from generate_for_preview, and does the actual
      Instagram publish.

Kept in its own module so both main.py (CLI) and app.py (dashboard API)
call the same code instead of duplicating pipeline logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from config import Settings
from gemini_client import generate_script
from instagram_publish import publish_reel, upload_public_video
from manim_render import render_scene
from sarvam_tts import synthesize
from video_merge import merge


import shutil


def _validate_tts_script(tts_script: str) -> None:
    """Validate that TTS script contains only natural Hindi text, no code/symbols."""
    # Check for code-like patterns
    code_patterns = [
        r'\{.*\}',           # Curly braces
        r'\[.*\]',           # Square brackets (except time markers)
        r'<.*>',             # Angle brackets
        r'def \w+',          # Function definitions
        r'class \w+',        # Class definitions
        r'import \w+',       # Import statements
        r'=\s*\w+',          # Variable assignments
        r'\w+\(\)',          # Function calls
        r'#\w+',             # Hash symbols (except hashtags)
        r'\$\w+',            # Dollar symbols
        r'0x[0-9a-fA-F]+',   # Hex numbers
        r'\d{3,}',           # Long number sequences
    ]

    # Allow time markers like [0s], [6s] etc.
    time_marker_pattern = r'\[\d+s\]'
    # Remove valid time markers before checking for other brackets
    clean_script = re.sub(time_marker_pattern, '', tts_script)

    for pattern in code_patterns:
        if re.search(pattern, clean_script):
            raise ValueError(
                f"TTS script contains code-like patterns: {pattern}. "
                f"TTS script must be pure Hindi narration without code, numbers, or special characters."
            )

    # Check for excessive special characters
    special_chars = r'[{}<>$#@]'
    if re.search(special_chars, clean_script):
        raise ValueError(
            f"TTS script contains special characters {special_chars}. "
            f"TTS script must be pure Hindi narration without code or symbols."
        )


@dataclass
class PreviewResult:
    video_url: str
    suggested_caption: str
    suggested_hashtags: list[str]
    local_video_path: Path
    cloudinary_public_id: str = ""


def generate_for_preview(topic: str, settings: Settings, max_retries: int = 2) -> PreviewResult:
    work_dir = settings.work_dir / topic[:40].replace(" ", "_").replace("/", "_")

    last_error = None
    script = None
    video_path = None

    total_attempts = 1 + max_retries
    for attempt in range(total_attempts):
        try:
            if attempt > 0:
                print(f"[pipeline] Retrying scene generation (attempt {attempt + 1}/{total_attempts}) with error feedback...")
            script = generate_script(
                topic=topic,
                api_key=settings.gemini_api_key,
                error_feedback=last_error,
            )
            # Validate TTS script to prevent code/symbols from leaking into audio
            _validate_tts_script(script.tts_script_hindi)
            video_path = render_scene(script.manim_code, work_dir)
            break
        except Exception as exc:
            last_error = str(exc)
            print(f"[pipeline] Attempt {attempt + 1} failed: {exc}")
            # Clean up partial renders before retrying
            shutil.rmtree(work_dir / "media", ignore_errors=True)
            if attempt == total_attempts - 1:
                raise

    audio_path = synthesize(
        text=script.tts_script_hindi,
        api_key=settings.sarvam_api_key,
        out_path=work_dir / "narration.wav",
        model=settings.sarvam_tts_model,
        speaker=settings.sarvam_tts_speaker,
        language_code=settings.sarvam_tts_language,
    )
    final_path = merge(video_path, audio_path, work_dir / "final.mp4")
    upload_res = upload_public_video(
        final_path,
        settings.cloudinary_cloud_name,
        settings.cloudinary_api_key,
        settings.cloudinary_api_secret,
    )

    # Clean up local work_dir temporary files (Manim partial renders, WAV, intermediate MP4)
    try:
        shutil.rmtree(work_dir, ignore_errors=True)
    except Exception as e:
        print(f"[cleanup] warning: could not remove {work_dir}: {e}")

    return PreviewResult(
        video_url=upload_res.secure_url,
        suggested_caption=script.caption,
        suggested_hashtags=script.hashtags,
        local_video_path=final_path,
        cloudinary_public_id=upload_res.public_id,
    )


def publish_to_instagram(video_url: str, caption: str, settings: Settings) -> str:
    return publish_reel(
        video_url=video_url,
        caption=caption,
        ig_user_id=settings.ig_user_id,
        access_token=settings.ig_access_token,
        api_version=settings.ig_graph_api_version,
    )

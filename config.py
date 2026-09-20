"""
Loads every setting from .env once, in one place, so the rest of the
codebase never touches os.environ directly. Fails loudly and early if a
required key is missing instead of failing halfway through a pipeline run.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REQUIRED_KEYS = [
    "GEMINI_API_KEY",
    "SARVAM_API_KEY",
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
    "IG_USER_ID",
    "IG_ACCESS_TOKEN",
]


def _require(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(
            f"Missing required env var {name}. Copy .env.example to .env "
            f"and fill it in."
        )
    return val


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    sarvam_api_key: str
    sarvam_tts_model: str
    sarvam_tts_speaker: str
    sarvam_tts_language: str
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    ig_user_id: str
    ig_access_token: str
    ig_graph_api_version: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    notify_email_to: str
    work_dir: Path


def load_settings() -> Settings:
    for key in REQUIRED_KEYS:
        _require(key)

    return Settings(
        gemini_api_key=os.environ["GEMINI_API_KEY"],
        sarvam_api_key=os.environ["SARVAM_API_KEY"],
        sarvam_tts_model=os.getenv("SARVAM_TTS_MODEL", "bulbul:v3"),
        sarvam_tts_speaker=os.getenv("SARVAM_TTS_SPEAKER", "shubh"),
        sarvam_tts_language=os.getenv("SARVAM_TTS_LANGUAGE", "hi-IN"),
        cloudinary_cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        cloudinary_api_key=os.environ["CLOUDINARY_API_KEY"],
        cloudinary_api_secret=os.environ["CLOUDINARY_API_SECRET"],
        ig_user_id=os.environ["IG_USER_ID"],
        ig_access_token=os.environ["IG_ACCESS_TOKEN"],
        ig_graph_api_version=os.getenv("IG_GRAPH_API_VERSION", "v21.0"),
        smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        notify_email_to=os.getenv("NOTIFY_EMAIL_TO", ""),
        work_dir=Path(os.getenv("WORK_DIR", "./work")),
    )

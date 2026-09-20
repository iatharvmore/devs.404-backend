"""
Calls Sarvam AI's Bulbul v3 text-to-speech REST API directly
(POST https://api.sarvam.ai/text-to-speech) and writes the decoded audio
to disk. Splits text into <=2500-char chunks (the bulbul:v3 limit) and
concatenates the resulting audio, since a 60s Hindi script can occasionally
run close to that limit.
"""
from __future__ import annotations

import base64
from pathlib import Path

import requests

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
MAX_CHARS = 2400  # stay under the 2500-char bulbul:v3 hard limit


def _chunk_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    # split on sentence boundaries where possible
    parts, current = [], ""
    for sentence in text.replace("।", "।|").split("|"):
        if len(current) + len(sentence) <= max_chars:
            current += sentence
        else:
            if current:
                parts.append(current)
            current = sentence
    if current:
        parts.append(current)
    return parts


def synthesize(
    text: str,
    api_key: str,
    out_path: Path,
    model: str = "bulbul:v3",
    speaker: str = "shubh",
    language_code: str = "hi-IN",
) -> Path:
    chunks = _chunk_text(text)
    audio_bytes_list: list[bytes] = []

    for chunk in chunks:
        resp = requests.post(
            SARVAM_TTS_URL,
            headers={
                "api-subscription-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": chunk,
                "target_language_code": language_code,
                "model": model,
                "speaker": speaker,
                "speech_sample_rate": 24000,
            },
            timeout=60,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Sarvam TTS failed [{resp.status_code}]: {resp.text}"
            )
        data = resp.json()
        for audio_b64 in data["audios"]:
            audio_bytes_list.append(base64.b64decode(audio_b64))

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if len(audio_bytes_list) == 1:
        out_path.write_bytes(audio_bytes_list[0])
        return out_path

    # multiple chunks: write each to a temp file and concatenate with ffmpeg
    # (simple binary WAV concatenation is unreliable across headers, so we
    # shell out rather than hand-roll WAV math)
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_files = []
        for i, b in enumerate(audio_bytes_list):
            p = Path(tmp) / f"part_{i}.wav"
            p.write_bytes(b)
            tmp_files.append(p)

        list_file = Path(tmp) / "list.txt"
        list_file.write_text(
            "\n".join(f"file '{p}'" for p in tmp_files), encoding="utf-8"
        )

        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(list_file), "-c", "copy", str(out_path),
            ],
            check=True,
            capture_output=True,
        )

    return out_path

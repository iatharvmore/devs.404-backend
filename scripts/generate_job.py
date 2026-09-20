"""
Triggered by a `repository_dispatch` event of type "generate" (sent by the
Vercel /api/generate function). Reads job_id + topic from the event
payload, runs the same generate_for_preview() pipeline used by the CLI and
FastAPI dashboard, and writes the result to status/<job_id>.json.

The workflow that calls this script commits status/ back to the repo
afterwards — that file IS the "database" the Vercel UI polls.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import load_settings  # noqa: E402
from notify import send_email  # noqa: E402
from pipeline import generate_for_preview  # noqa: E402

STATUS_DIR = Path(__file__).resolve().parent.parent / "status"


def write_status(job_id: str, data: dict) -> None:
    STATUS_DIR.mkdir(exist_ok=True)
    (STATUS_DIR / f"{job_id}.json").write_text(json.dumps(data, indent=2))


def main() -> None:
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    payload = event["client_payload"]
    job_id = payload["job_id"]
    topic = payload["topic"]

    write_status(job_id, {"job_id": job_id, "topic": topic, "status": "generating"})

    settings = load_settings()
    try:
        result = generate_for_preview(topic, settings)
        write_status(
            job_id,
            {
                "job_id": job_id,
                "topic": topic,
                "status": "ready",
                "video_url": result.video_url,
                "caption": result.suggested_caption,
                "hashtags": result.suggested_hashtags,
            },
        )
        _notify(
            settings,
            f"[dev's.404] Video ready to review: {topic}",
            f"Your reel for \"{topic}\" is ready.\n\nPreview: {result.video_url}\n\n"
            f"Open the dashboard to review and publish.",
        )
    except Exception:
        tb = traceback.format_exc()
        write_status(job_id, {"job_id": job_id, "topic": topic, "status": "failed", "error": tb})
        _notify(settings, f"[dev's.404] Generation FAILED: {topic}", tb)
        raise


def _notify(settings, subject: str, body: str) -> None:
    try:
        send_email(
            subject=subject,
            body=body,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_password=settings.smtp_password,
            to_addr=settings.notify_email_to,
        )
    except Exception:
        print(f"[notify] email failed:\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()

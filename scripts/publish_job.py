"""
Triggered by a `repository_dispatch` event of type "publish" (sent by the
Vercel /api/publish function). Reads the job's video_url from its existing
status/<job_id>.json (written earlier by generate_job.py), publishes to
Instagram with the (possibly user-edited) caption/hashtags from the
payload, and updates the status file.
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
from pipeline import publish_to_instagram  # noqa: E402

STATUS_DIR = Path(__file__).resolve().parent.parent / "status"


def read_status(job_id: str) -> dict:
    return json.loads((STATUS_DIR / f"{job_id}.json").read_text())


def write_status(job_id: str, data: dict) -> None:
    (STATUS_DIR / f"{job_id}.json").write_text(json.dumps(data, indent=2))


def main() -> None:
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    payload = event["client_payload"]
    job_id = payload["job_id"]
    caption = payload["caption"]
    hashtags = payload.get("hashtags", [])

    data = read_status(job_id)
    data["status"] = "publishing"
    write_status(job_id, data)

    settings = load_settings()
    try:
        full_caption = caption.strip()
        if hashtags:
            full_caption += "\n\n" + " ".join(hashtags)
        media_id = publish_to_instagram(data["video_url"], full_caption, settings)
        data["status"] = "published"
        data["media_id"] = media_id
        write_status(job_id, data)
        _notify(
            settings,
            f"[dev's.404] Published: {data['topic']}",
            f"Your reel for \"{data['topic']}\" is live.\nMedia ID: {media_id}",
        )
    except Exception:
        tb = traceback.format_exc()
        data["status"] = "failed"
        data["error"] = tb
        write_status(job_id, data)
        _notify(settings, f"[dev's.404] Publish FAILED: {data['topic']}", tb)
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

"""
Run the whole dev's.404 pipeline end to end for one topic.

Usage:
    python main.py "How does attention work in transformers?"

or, to pull from a queue file (one topic per line, consumed top to bottom —
good for GitHub Actions cron triggering this with no args):
    python main.py --from-queue topics.txt

Every stage's failure is caught, emailed to you with the traceback, and
re-raised (non-zero exit) so a scheduler like GitHub Actions/cron marks the
run as failed.
"""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from config import load_settings
from gemini_client import generate_script
from instagram_publish import publish_reel, upload_public_video
from manim_render import render_scene
from notify import send_email
from sarvam_tts import synthesize
from video_merge import merge


def run_pipeline(topic: str) -> str:
    settings = load_settings()
    work_dir = settings.work_dir / topic[:40].replace(" ", "_").replace("/", "_")

    print(f"[1/5] Generating script + Hindi TTS narration for: {topic!r}")
    script = generate_script(topic, settings.gemini_api_key)

    print("[2/5] Rendering Manim scene...")
    video_path = render_scene(script.manim_code, work_dir)

    print("[3/5] Synthesizing TTS audio via Sarvam...")
    audio_path = synthesize(
        text=script.tts_script_hindi,
        api_key=settings.sarvam_api_key,
        out_path=work_dir / "narration.wav",
        model=settings.sarvam_tts_model,
        speaker=settings.sarvam_tts_speaker,
        language_code=settings.sarvam_tts_language,
    )

    print("[4/5] Merging video + audio...")
    final_path = merge(video_path, audio_path, work_dir / "final.mp4")

    print("[5/5] Uploading + publishing to Instagram...")
    public_url = upload_public_video(
        final_path,
        settings.cloudinary_cloud_name,
        settings.cloudinary_api_key,
        settings.cloudinary_api_secret,
    )
    caption = f"{topic}\n\n#ai #computerscience #devs404"
    media_id = publish_reel(
        video_url=public_url,
        caption=caption,
        ig_user_id=settings.ig_user_id,
        access_token=settings.ig_access_token,
        api_version=settings.ig_graph_api_version,
    )

    return media_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", nargs="?", help="Topic for today's reel")
    parser.add_argument(
        "--from-queue",
        help="Path to a text file with one topic per line; the first line "
        "is used and then removed from the file.",
    )
    args = parser.parse_args()

    if args.from_queue:
        queue_path = Path(args.from_queue)
        lines = [l for l in queue_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not lines:
            print("Queue is empty — nothing to do.")
            return
        topic, remaining = lines[0], lines[1:]
    elif args.topic:
        topic, remaining, queue_path = args.topic, None, None
    else:
        parser.error("Provide a topic or --from-queue <file>")
        return

    settings = load_settings()

    try:
        media_id = run_pipeline(topic)
    except Exception:
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        send_email(
            subject=f"[dev's.404] FAILED: {topic}",
            body=f"Pipeline failed for topic: {topic}\n\n{tb}",
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_password=settings.smtp_password,
            to_addr=settings.notify_email_to,
        )
        sys.exit(1)

    send_email(
        subject=f"[dev's.404] Posted: {topic}",
        body=f"Reel posted successfully.\nTopic: {topic}\nMedia ID: {media_id}",
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password=settings.smtp_password,
        to_addr=settings.notify_email_to,
    )

    if queue_path is not None:
        queue_path.write_text("\n".join(remaining) + ("\n" if remaining else ""), encoding="utf-8")

    print(f"Done. Media ID: {media_id}")


if __name__ == "__main__":
    main()

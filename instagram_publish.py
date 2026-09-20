"""
Two steps, matching Instagram's current (2026) Content Publishing API:

1. Upload the final mp4 to Cloudinary to get a public URL — the IG API
   requires video_url to be reachable by Meta's servers when it fetches it,
   it does not accept direct file uploads.
2. Publish as a Reel via the Instagram Graph API 3-step flow:
     POST /{ig-user-id}/media          (media_type=REELS, video_url=...)
  -> GET  /{container_id}?fields=status_code   (poll until FINISHED)
  -> POST /{ig-user-id}/media_publish  (creation_id=container_id)

Docs: https://developers.facebook.com/docs/instagram-platform/content-publishing
Requires: IG account is Business/Creator, linked to a Facebook Page, and the
access token has instagram_basic + instagram_content_publish permissions.
"""
from __future__ import annotations

import time
from pathlib import Path

import cloudinary
import cloudinary.uploader
import requests


def upload_public_video(
    video_path: Path,
    cloud_name: str,
    api_key: str,
    api_secret: str,
) -> str:
    cloudinary.config(
        cloud_name=cloud_name, api_key=api_key, api_secret=api_secret, secure=True
    )
    result = cloudinary.uploader.upload(
        str(video_path), resource_type="video", folder="daves404_reels"
    )
    return result["secure_url"]


def publish_reel(
    video_url: str,
    caption: str,
    ig_user_id: str,
    access_token: str,
    api_version: str = "v21.0",
    poll_interval_s: int = 5,
    poll_timeout_s: int = 300,
) -> str:
    base = f"https://graph.facebook.com/{api_version}"

    # Step 1: create the Reels container
    create_resp = requests.post(
        f"{base}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": access_token,
        },
        timeout=30,
    )
    create_resp.raise_for_status()
    container_id = create_resp.json()["id"]

    # Step 2: poll until Meta has finished processing the video
    deadline = time.time() + poll_timeout_s
    while time.time() < deadline:
        status_resp = requests.get(
            f"{base}/{container_id}",
            params={"fields": "status_code", "access_token": access_token},
            timeout=30,
        )
        status_resp.raise_for_status()
        status = status_resp.json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError(f"IG container {container_id} failed processing")
        time.sleep(poll_interval_s)
    else:
        raise TimeoutError(
            f"IG container {container_id} did not finish processing in time"
        )

    # Step 3: publish
    publish_resp = requests.post(
        f"{base}/{ig_user_id}/media_publish",
        data={"creation_id": container_id, "access_token": access_token},
        timeout=30,
    )
    publish_resp.raise_for_status()
    media_id = publish_resp.json()["id"]
    return media_id

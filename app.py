"""
Dashboard backend.

Endpoints:
  POST /api/jobs              {topic} -> {job_id}         start generation in background
  GET  /api/jobs/{job_id}     -> job status + preview data once ready
  POST /api/jobs/{job_id}/publish   {caption, hashtags} -> publishes to Instagram

Jobs are kept in memory — fine for a single-user personal dashboard running
on your own server. No login/token: this is meant to sit behind your own
VPS, reachable only by you. If you ever expose it more broadly, put it
behind a reverse proxy with basic auth rather than adding auth back in here.

Sends you an email when a video is ready to review, and again once it's
published.

Run with:  uvicorn app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import threading
import traceback
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import load_settings
from notify import send_email
from pipeline import generate_for_preview, publish_to_instagram

import shutil

JobStatus = Literal["pending", "generating", "ready", "publishing", "published", "failed"]


@dataclass
class Job:
    id: str
    topic: str
    status: JobStatus = "pending"
    video_url: str | None = None
    caption: str | None = None
    hashtags: list[str] = field(default_factory=list)
    error: str | None = None
    media_id: str | None = None
    cloudinary_public_id: str | None = None


JOBS: dict[str, Job] = {}

app = FastAPI(title="dev's.404 reel dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateJobRequest(BaseModel):
    topic: str


class PublishRequest(BaseModel):
    caption: str
    hashtags: list[str] = []


def _notify(settings, subject: str, body: str) -> None:
    # best-effort — a broken SMTP config should never take down a job
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
        print(f"[notify] email send failed:\n{traceback.format_exc()}")


def _run_generation(job: Job) -> None:
    job.status = "generating"
    settings = load_settings()
    try:
        result = generate_for_preview(job.topic, settings)
        job.video_url = result.video_url
        job.caption = result.suggested_caption
        job.hashtags = result.suggested_hashtags
        job.cloudinary_public_id = result.cloudinary_public_id
        job.status = "ready"
        _notify(
            settings,
            subject=f"[dev's.404] Video ready to review: {job.topic}",
            body=(
                f"Your reel for \"{job.topic}\" is rendered and ready.\n\n"
                f"Preview: {job.video_url}\n\n"
                f"Open the dashboard to review the caption and publish."
            ),
        )
    except Exception:
        job.error = traceback.format_exc()
        job.status = "failed"
        _notify(
            settings,
            subject=f"[dev's.404] Generation FAILED: {job.topic}",
            body=f"Generation failed for topic: {job.topic}\n\n{job.error}",
        )


def _run_publish(job: Job, caption: str, hashtags: list[str]) -> None:
    job.status = "publishing"
    settings = load_settings()
    try:
        full_caption = caption.strip()
        if hashtags:
            full_caption += "\n\n" + " ".join(hashtags)
        media_id = publish_to_instagram(job.video_url, full_caption, settings)
        job.media_id = media_id
        job.status = "published"
        _notify(
            settings,
            subject=f"[dev's.404] Published: {job.topic}",
            body=f"Your reel for \"{job.topic}\" is live on Instagram.\nMedia ID: {media_id}",
        )
    except Exception:
        job.error = traceback.format_exc()
        job.status = "failed"
        _notify(
            settings,
            subject=f"[dev's.404] Publish FAILED: {job.topic}",
            body=f"Publish failed for topic: {job.topic}\n\n{job.error}",
        )


@app.post("/api/jobs")
def create_job(req: CreateJobRequest):
    job = Job(id=str(uuid.uuid4()), topic=req.topic)
    JOBS[job.id] = job
    thread = threading.Thread(target=_run_generation, args=(job,), daemon=True)
    thread.start()
    return {"job_id": job.id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "topic": job.topic,
        "status": job.status,
        "video_url": job.video_url,
        "caption": job.caption,
        "hashtags": job.hashtags,
        "media_id": job.media_id,
        "error": job.error,
        "cloudinary_public_id": job.cloudinary_public_id,
    }


@app.post("/api/jobs/{job_id}/publish")
def publish_job(job_id: str, req: PublishRequest):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "ready":
        raise HTTPException(
            status_code=400, detail=f"Job is '{job.status}', not ready to publish"
        )
    thread = threading.Thread(
        target=_run_publish, args=(job, req.caption, req.hashtags), daemon=True
    )
    thread.start()
    return {"status": "publishing"}


@app.get("/api/jobs")
def list_jobs():
    return [
        {"job_id": j.id, "topic": j.topic, "status": j.status}
        for j in sorted(JOBS.values(), key=lambda j: j.id, reverse=True)
    ]


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete from memory
    del JOBS[job_id]

    # Clean up status file if it exists
    status_dir = Path(__file__).parent / "status"
    status_file = status_dir / f"{job_id}.json"
    if status_file.exists():
        try:
            status_file.unlink()
        except Exception as e:
            print(f"[cleanup] Failed to delete status file {status_file}: {e}")

    # Clean up Cloudinary video if we have a public_id
    if job.video_url and job.cloudinary_public_id:
        try:
            import cloudinary
            settings = load_settings()
            cloudinary.config(
                cloud_name=settings.cloudinary_cloud_name,
                api_key=settings.cloudinary_api_key,
                api_secret=settings.cloudinary_api_secret,
            )
            cloudinary.uploader.destroy(job.cloudinary_public_id, resource_type="video")
            print(f"[cleanup] Deleted Cloudinary video: {job.cloudinary_public_id}")
        except Exception as e:
            print(f"[cleanup] Failed to delete Cloudinary video: {e}")

    return {"status": "deleted"}


# Serve the dashboard's static frontend (index.html, app.js, style.css)
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")


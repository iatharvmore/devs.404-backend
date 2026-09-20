# dev's.404 reel pipeline

Automates: topic → Gemini (script + Hindi TTS script) → Sarvam TTS →
Manim render → ffmpeg merge (freezes last frame if audio outruns video,
replacing the manual Clipchamp step) → Instagram Reel publish → email
notification.

## Setup (local run)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
sudo apt-get install ffmpeg          # Linux; brew install ffmpeg on Mac
cp .env.example .env                 # then paste your keys into .env
```

### Where each key comes from

| Key | Where to get it |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| `SARVAM_API_KEY` | https://dashboard.sarvam.ai |
| `CLOUDINARY_*` | Free account at https://cloudinary.com — Dashboard shows cloud name/key/secret. Used only to get a temporary public URL for the video, since Instagram's API fetches the video from a URL rather than accepting an upload. |
| `IG_USER_ID`, `IG_ACCESS_TOKEN` | Meta for Developers app with the Instagram Graph API product added. Your IG account must be a **Business or Creator account linked to a Facebook Page**. You need `instagram_basic` + `instagram_content_publish` permissions. Long-lived tokens last ~60 days — set a calendar reminder to refresh. |
| `SMTP_USER`/`SMTP_PASSWORD` | If using Gmail: enable 2FA, then create an **App Password** — your normal password won't work over SMTP. |

## Run once, manually

```bash
python main.py "How does attention work in transformers?"
```

## Run from a queue (what the GitHub Actions workflow uses)

```bash
python main.py --from-queue topics.txt
```
Pops the first non-empty line, runs the pipeline, rewrites the file without
that line.

## Automating it: GitHub Actions (no server needed)

`.github/workflows/post_reel.yml` runs this daily on GitHub's free runners.

1. Push this repo to GitHub (keep `.env` out of it — `.gitignore` already
   excludes it).
2. Repo → Settings → Secrets and variables → Actions → add each key from
   `.env.example` as a repo secret (same names).
3. Edit `topics.txt` whenever you want to queue more topics — commit and
   push.
4. The workflow runs on the cron schedule, or trigger it manually from the
   Actions tab (`workflow_dispatch`).

This covers your "load is too much" question: GitHub Actions gives you
2,000 free CI minutes/month on a free personal account, and a Manim render
for a 60s clip plus TTS/API calls typically finishes in a few minutes — so
daily posting comfortably fits without needing your own server or a
Vercel frontend. Reach for a real backend only if you want a UI to manage
the topic queue instead of editing `topics.txt`; the pipeline logic here
doesn't change either way, only how it's triggered.

## Dashboard, fully free: Vercel UI + GitHub Actions as the backend

This is the recommended setup if you don't want to run or pay for any
server. No persistent process exists anywhere — GitHub Actions runs the
pipeline only when triggered, and the repo itself acts as the database via
small JSON files under `status/`.

```
Vercel (free)                         GitHub (free)
┌────────────────┐   repository_    ┌───────────────────────┐
│ static UI +     │   dispatch      │ Actions workflow runs  │
│ 4 tiny Node     │ ───────────────▶│ pipeline.py, commits   │
│ functions       │                 │ status/<job_id>.json   │
│ (vercel-        │◀─────────────── │                        │
│  dashboard/)    │  polls the file └───────────────────────┘
└────────────────┘  via GitHub API
```

### 1. Push this repo to GitHub (if you haven't already)

Private is fine — every function below authenticates with a token.

### 2. Add your existing secrets as repo secrets

Settings → Secrets and variables → Actions → add each key from
`.env.example` (`GEMINI_API_KEY`, `SARVAM_API_KEY`, `CLOUDINARY_*`,
`IG_USER_ID`, `IG_ACCESS_TOKEN`, `SMTP_USER`, `SMTP_PASSWORD`,
`NOTIFY_EMAIL_TO`) — same names, no `.env` file needed on this path.

### 3. Create a GitHub Personal Access Token for Vercel

This is the one new credential this setup needs — it lets the Vercel
functions create files and fire dispatch events in your repo.

- Fine-grained token (github.com → Settings → Developer settings → Personal
  access tokens → Fine-grained tokens): scope it to just this repo, with
  **Contents: Read and write** permission. That's all it needs.
- Keep it secret — it's as powerful as write access to this one repo.

### 4. Deploy `vercel-dashboard/` to Vercel

```bash
cd vercel-dashboard
npx vercel deploy --prod
```
(or connect the repo in the Vercel dashboard and set the **root directory**
to `vercel-dashboard/` in project settings, so Vercel doesn't try to build
the Python code alongside it.)

In the Vercel project's Settings → Environment Variables, add:

| Key | Value |
|---|---|
| `GITHUB_TOKEN` | the fine-grained PAT from step 3 |
| `GITHUB_OWNER` | your GitHub username/org |
| `GITHUB_REPO` | this repo's name |

Redeploy after adding them (env var changes need a redeploy to take effect).

### 5. Use it

Open the Vercel URL. Type a topic → Generate. The function writes a
`queued` status file and fires a `repository_dispatch` — check the
**Actions** tab and you'll see "Dashboard - generate" start within
seconds. The page polls automatically and flips to the preview once the
workflow finishes (a few minutes: Gemini + render + TTS + ffmpeg +
Cloudinary upload). Edit the caption/hashtags if you want, hit Publish,
and the same pattern runs the "Dashboard - publish" workflow. You'll get
the same two emails as before (ready-to-review, then published).

### Why this works within free tiers

- Vercel's free (Hobby) plan: serverless functions here do almost nothing
  (a couple of HTTP calls each), miles under any free-tier limit.
- GitHub Actions: 2,000 free minutes/month on a free personal account. A
  generate run is a few minutes; even posting daily uses a small fraction
  of that.
- No idle cost anywhere — nothing runs, and nothing is "on", between jobs.

### Trade-offs vs. the self-hosted FastAPI dashboard (below)

- Slower to start (Actions runners take 10-30s to spin up) and slower to
  poll (5s intervals here vs. near-instant on a real backend) — fine for a
  personal tool, not built for snappy UX.
- Every status update is a git commit — your repo's history will fill up
  with `status: ...` commits. Harmless, but if it bothers you, squash
  periodically or move `status/` to an orphan branch.
- If you outgrow this (want it to feel instant, or run heavier jobs), the
  FastAPI + VPS dashboard below is the upgrade path — same pipeline code,
  just always-on instead of triggered.

## Dashboard, self-hosted (always-on server, more responsive)

A small FastAPI backend (`app.py`) + single-page frontend (`static/`) that
wraps the same pipeline: type a topic, it generates in the background, you
review the video and edit the Gemini-drafted caption/hashtags, then hit
Publish. No login — it's meant to run on your own server for just you.

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open `http://<server-ip>:8000` and use it straight away.

You'll get two emails per reel (via the same SMTP settings as before):
one when the video finishes rendering and is ready to review, and one
once you hit Publish and it's actually live on Instagram. Failures at
either stage email you too, with the error.

**Why not Vercel for this part:** the dashboard has to run Manim + ffmpeg
as real subprocesses and hold job state across a multi-minute render.
Vercel's serverless functions are stateless and time out long before a
render finishes, so this needs an always-on process — a small VPS
(Hetzner/DigitalOcean, ~$5/mo) running `uvicorn` behind `systemd` (auto-
restarts on crash/reboot) works well. Put it behind a reverse proxy
(Caddy or nginx) if you want HTTPS on a real domain instead of hitting the
IP:port directly — Caddy gets you a free TLS cert with about 5 lines of
config. Since there's no login, only expose this on a domain/IP you don't
share, or put it behind your VPS's firewall / a VPN if you want it more locked down.

The GitHub Actions cron workflow from before still works independently of
the dashboard — use the dashboard when you want to review before posting,
use the Actions workflow for topics you're fine auto-publishing straight
from the queue.

## Notes on things that commonly break

- **Manim + LaTeX**: if any generated scene uses `MathTex`, the runner
  needs a LaTeX distro (`sudo apt-get install texlive-full` — large, or
  a slimmer subset). Plain `Text()` doesn't need LaTeX at all.
- **Instagram video encoding requirements**: H.264 video, AAC audio,
  3s–15min duration, aspect ratio between 0.01:1 and 10:1. The `merge()`
  step already encodes with `libx264`/`aac`.
- **IG access token expiry**: short-lived tokens expire in ~1 hour; long-lived
  tokens last ~60 days. Exchange a short-lived token for a long-lived one
  via `GET /oauth/access_token?grant_type=fb_exchange_token...` before
  putting it in `.env`/secrets.
- **50 posts/24h** is Instagram's publishing rate limit — irrelevant at
  daily cadence.

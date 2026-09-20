const API_BASE = ""; // same origin — backend serves this file too

const topicInput = document.getElementById("topicInput");
const generateBtn = document.getElementById("generateBtn");

const statusSection = document.getElementById("status");
const statusText = document.getElementById("statusText");

const previewSection = document.getElementById("preview");
const previewVideo = document.getElementById("previewVideo");
const captionInput = document.getElementById("captionInput");
const hashtagsInput = document.getElementById("hashtagsInput");
const publishBtn = document.getElementById("publishBtn");

const publishedMsg = document.getElementById("publishedMsg");
const mediaIdSpan = document.getElementById("mediaId");
const errorMsg = document.getElementById("errorMsg");
const jobList = document.getElementById("jobList");

let currentJobId = null;
let pollTimer = null;

function apiHeaders(extra = {}) {
  return { ...extra };
}

function showOnly(section) {
  [statusSection, previewSection, publishedMsg, errorMsg].forEach((el) =>
    el.classList.add("hidden")
  );
  if (section) section.classList.remove("hidden");
}

generateBtn.addEventListener("click", async () => {
  const topic = topicInput.value.trim();
  if (!topic) return;

  generateBtn.disabled = true;
  showOnly(statusSection);
  statusText.textContent = "Starting generation...";

  try {
    const res = await fetch(`${API_BASE}/api/jobs`, {
      method: "POST",
      headers: apiHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ topic }),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    currentJobId = data.job_id;
    pollJob(currentJobId);
  } catch (err) {
    showError(err.message);
    generateBtn.disabled = false;
  }
});

function pollJob(jobId) {
  clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}`, {
        headers: apiHeaders(),
      });
      if (!res.ok) throw new Error(await res.text());
      const job = await res.json();
      handleJobUpdate(job);
    } catch (err) {
      clearInterval(pollTimer);
      showError(err.message);
    }
  }, 3000);
}

const STATUS_LABELS = {
  pending: "Queued...",
  generating: "Generating script, rendering video, synthesizing narration... (this can take a few minutes)",
  ready: "Ready for review",
  publishing: "Publishing to Instagram...",
  published: "Published",
  failed: "Failed",
};

function handleJobUpdate(job) {
  statusText.textContent = STATUS_LABELS[job.status] || job.status;

  if (job.status === "ready") {
    clearInterval(pollTimer);
    generateBtn.disabled = false;
    previewVideo.src = job.video_url;
    captionInput.value = job.caption || "";
    hashtagsInput.value = (job.hashtags || []).join(" ");
    showOnly(previewSection);
  } else if (job.status === "published") {
    clearInterval(pollTimer);
    generateBtn.disabled = false;
    mediaIdSpan.textContent = job.media_id;
    showOnly(publishedMsg);
    refreshJobList();
  } else if (job.status === "failed") {
    clearInterval(pollTimer);
    generateBtn.disabled = false;
    showError(job.error || "Unknown error");
    refreshJobList();
  } else {
    showOnly(statusSection);
  }
}

publishBtn.addEventListener("click", async () => {
  if (!currentJobId) return;
  publishBtn.disabled = true;
  showOnly(statusSection);
  statusText.textContent = STATUS_LABELS.publishing;

  const caption = captionInput.value.trim();
  const hashtags = hashtagsInput.value.trim().split(/\s+/).filter(Boolean);

  try {
    const res = await fetch(`${API_BASE}/api/jobs/${currentJobId}/publish`, {
      method: "POST",
      headers: apiHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ caption, hashtags }),
    });
    if (!res.ok) throw new Error(await res.text());
    pollJob(currentJobId);
  } catch (err) {
    showError(err.message);
    publishBtn.disabled = false;
  }
});

function showError(message) {
  errorMsg.textContent = message;
  showOnly(errorMsg);
}

async function refreshJobList() {
  try {
    const res = await fetch(`${API_BASE}/api/jobs`, { headers: apiHeaders() });
    if (!res.ok) return;
    const jobs = await res.json();
    jobList.innerHTML = "";
    jobs.slice(0, 10).forEach((j) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${j.topic}</span><span class="job-status">${j.status}</span>`;
      jobList.appendChild(li);
    });
  } catch {
    // silent — job history is a nice-to-have, not critical
  }
}

refreshJobList();

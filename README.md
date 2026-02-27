# Naukri CV Bulk Downloader

Bulk download all CVs/resumes from your Naukri recruiter portal job listings. Iterates through every job posting, selects all applicants, and triggers batch downloads.

## Deploy on Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file path: `full_downloader/app.py`
5. Deploy

The `packages.txt` file ensures Playwright's system dependencies are installed automatically.

## Run Locally

```bash
pip install -r requirements.txt
playwright install chromium
streamlit run app.py
```

## Usage

1. Log into [Naukri Recruiter Portal](https://hiring.naukri.com)
2. Export cookies using EditThisCookie extension (JSON format)
3. Paste cookies into the app
4. Click "Start Bulk Download"
5. If interrupted, restart — it resumes from where it left off

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit web UI |
| `scraper.py` | Core Playwright automation |
| `config.py` | All CSS selectors, URLs, timing |
| `progress_tracker.py` | Resume-after-interruption |
| `packages.txt` | System deps for Streamlit Cloud |
| `requirements.txt` | Python dependencies |

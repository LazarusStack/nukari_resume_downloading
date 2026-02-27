"""
Streamlit UI for Naukri CV Bulk Downloader.
Deployable on Streamlit Cloud or any cloud platform.
"""

import streamlit as st
import json
import os
import subprocess
import threading

# Auto-install Playwright browsers for cloud deployment
try:
    subprocess.run(["playwright", "install", "chromium"], check=True, capture_output=True)
except Exception:
    pass

from scraper import NaukriBulkDownloader, CaptchaError
from progress_tracker import ProgressTracker
from config import PROGRESS_FILE

st.set_page_config(page_title="Naukri CV Bulk Downloader", layout="wide")

st.title("Naukri CV Bulk Downloader")
st.markdown("Bulk download all CVs/resumes from your Naukri recruiter portal job listings.")

# --- Session State ---
if "logs" not in st.session_state:
    st.session_state.logs = []
if "running" not in st.session_state:
    st.session_state.running = False
if "downloader" not in st.session_state:
    st.session_state.downloader = None

# --- Sidebar: Progress Stats ---
tracker = ProgressTracker()
stats = tracker.get_stats()

with st.sidebar:
    st.header("Progress")
    st.metric("Jobs Completed", stats["completed"])
    st.metric("Total Batch Downloads", stats["total_downloads"])
    if stats["started_at"]:
        st.caption(f"Started: {stats['started_at']}")

    st.divider()
    if st.button("Reset Progress", type="secondary"):
        tracker.reset()
        st.session_state.logs = []
        st.rerun()

    st.divider()
    st.header("Instructions")
    st.markdown("""
1. **Get Cookies**: Log into [Naukri Recruiter Portal](https://hiring.naukri.com).
   Open DevTools (F12) → Application → Cookies, or use
   [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie) to export as JSON.
2. **Paste** the JSON cookie array below.
3. **Click Start** to begin bulk downloading.
4. Downloads go to the portal's default (ZIP/PDF per batch).
5. If interrupted, **restart** — it auto-resumes from where it left off.
""")

# --- Cookie Input ---
cookie_input = st.text_area(
    "Paste Naukri Cookies (JSON format)",
    height=200,
    placeholder='[{"domain": ".naukri.com", "name": "...", "value": "...", ...}]',
)

# --- Controls ---
col1, col2 = st.columns(2)

with col1:
    start_btn = st.button("Start Bulk Download", type="primary", disabled=st.session_state.running)

with col2:
    stop_btn = st.button("Stop", disabled=not st.session_state.running)

# --- Log Display ---
log_container = st.container()

def add_log(message):
    st.session_state.logs.append(message)

# --- Stop Handler ---
if stop_btn and st.session_state.downloader:
    st.session_state.downloader.stop()
    add_log("Stop requested... will stop after current job.")
    st.session_state.running = False

# --- Start Handler ---
if start_btn:
    if not cookie_input:
        st.error("Please paste your Naukri cookies in JSON format.")
    else:
        # Parse cookies
        try:
            cookies = json.loads(cookie_input)
            if not isinstance(cookies, list):
                st.error("Cookies must be a JSON array.")
                st.stop()
        except json.JSONDecodeError:
            st.error("Invalid JSON. Please paste valid cookie JSON array.")
            st.stop()

        st.session_state.logs = []
        st.session_state.running = True
        add_log("Starting bulk CV download...")

        progress_tracker = ProgressTracker()
        downloader = NaukriBulkDownloader(
            cookies=cookies,
            progress_tracker=progress_tracker,
            log_callback=add_log,
        )
        st.session_state.downloader = downloader

        try:
            with st.spinner("Downloading CVs... check logs below for progress."):
                downloader.run()
            add_log("All done!")
            st.success("Bulk download complete!")
        except CaptchaError as e:
            st.error(f"CAPTCHA detected: {e}")
            add_log(f"CAPTCHA: {e}")
        except Exception as e:
            st.error(f"Error: {e}")
            add_log(f"Error: {e}")
        finally:
            st.session_state.running = False
            st.session_state.downloader = None

# --- Show Logs ---
with log_container:
    if st.session_state.logs:
        st.subheader("Logs")
        log_text = "\n".join(st.session_state.logs)
        st.code(log_text, language="text")

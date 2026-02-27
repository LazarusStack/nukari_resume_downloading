"""
Configuration for Naukri CV Bulk Downloader.
All CSS selectors, URLs, and timing constants in one place.
When Naukri changes their DOM, update selectors here.
"""

import os

# --- URLs ---
JOB_LISTING_URL = "https://hiring.naukri.com/hiring/job-listing"
JOB_APPLIES_URL = "https://hiring.naukri.com/hiring/{job_id}/applies"

# --- CSS Selectors ---
SELECTORS = {
    # Job listing page
    "job_links": 'a[href*="/applies"]',
    "job_link_pattern": r"/hiring/(\w+)/applies",

    # Pagination (shared between job listing and applicant pages)
    "next_page": "i.ico-expand.next",
    "page_value": "span.page-value",

    # Applicant page
    "select_all_label": "label.selectAll",
    "select_all_checkbox": "#selectAll",
    "download_btn": "div.action.allTab",
    "download_label": "span.download-label",
    "show_dropdown": "div.show-count-selected",
    "show_160": "text=160",

    # Detection
    "no_responses": "text=No responses yet",
    "captcha_text": "text=To continue your request please check the box",
    "blocked_text": "text=Browser is using an unauthorised plugin",
    "success_toast": "text=Profile downloaded successfully",
}

# --- Timing (seconds) — intentionally slow to avoid rate limiting ---
TIMING = {
    "page_load_wait": 5.0,         # Wait after navigating to a new page
    "after_show_dropdown": 2.0,    # Wait after clicking show dropdown
    "after_show_select": 4.0,      # Wait after selecting 160
    "after_select_all": 3.0,       # Wait after clicking Select All
    "after_download": 8.0,         # Wait after clicking Download
    "after_next_page": 4.0,        # Wait after clicking next page
    "between_jobs": 5.0,           # Wait between processing jobs
    "min_jitter": 1.0,             # Min random jitter added to delays
    "max_jitter": 3.0,             # Max random jitter added to delays
    "scroll_delay": 0.3,           # Delay between scroll steps
}

# --- Browser ---
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# --- File Paths ---
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress.json")

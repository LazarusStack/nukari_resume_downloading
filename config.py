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
    "success_toast": "text=Profile downloaded successfully",
}

# --- Timing (milliseconds for Playwright, seconds for sleep) ---
TIMING = {
    "page_load_wait": 2.0,         # Wait after navigating to a new page
    "after_show_dropdown": 0.5,    # Wait after clicking show dropdown
    "after_show_select": 1.5,      # Wait after selecting 160
    "after_select_all": 0.8,       # Wait after clicking Select All
    "after_download": 2.5,         # Wait after clicking Download
    "after_next_page": 1.5,        # Wait after clicking next page
    "between_jobs": 1.0,           # Wait between processing jobs
    "min_jitter": 0.5,             # Min random jitter added to delays
    "max_jitter": 1.5,             # Max random jitter added to delays
}

# --- File Paths ---
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress.json")

"""
Core automation logic for bulk CV downloading from Naukri recruiter portal.
Uses Playwright to navigate the portal and download CVs for all job postings.
"""

import re
import time
import random
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from config import (
    JOB_LISTING_URL,
    JOB_APPLIES_URL,
    SELECTORS,
    TIMING,
    DOWNLOAD_DIR,
)
from progress_tracker import ProgressTracker


class CaptchaError(Exception):
    """Raised when a CAPTCHA is detected on the page."""
    pass


class NaukriBulkDownloader:
    def __init__(self, cookies, progress_tracker=None, log_callback=None):
        self.raw_cookies = cookies
        self.cookies = self._normalize_cookies(cookies)
        self.progress = progress_tracker or ProgressTracker()
        self.log = log_callback or print
        self.browser = None
        self.context = None
        self.page = None
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def _normalize_cookies(self, cookies):
        """Fix sameSite values for Playwright compatibility."""
        normalized = []
        for cookie in cookies:
            c = dict(cookie)
            same_site = c.get("sameSite", "")
            if same_site in ("unspecified", "no_restriction"):
                c["sameSite"] = "Lax"
            elif same_site:
                c["sameSite"] = same_site.capitalize()
            # Remove fields Playwright doesn't accept
            for key in ("hostOnly", "storeId", "session", "id", "expirationDate"):
                c.pop(key, None)
            # Convert expirationDate to expires if present in original
            if "expirationDate" in cookie:
                c["expires"] = cookie["expirationDate"]
            normalized.append(c)
        return normalized

    def _sleep(self, base_seconds):
        """Sleep with random jitter to avoid detection."""
        jitter = random.uniform(TIMING["min_jitter"], TIMING["max_jitter"])
        time.sleep(base_seconds + jitter)

    def setup_browser(self):
        """Launch headless Chromium and inject cookies."""
        self.log("Launching browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()

        try:
            self.context.add_cookies(self.cookies)
            self.log("Cookies added successfully.")
        except Exception as e:
            self.log(f"Error adding cookies: {e}")
            raise

        self.page = self.context.new_page()

    def cleanup(self):
        """Close browser and Playwright."""
        if self.browser:
            self.browser.close()
        if hasattr(self, "playwright") and self.playwright:
            self.playwright.stop()
        self.log("Browser closed.")

    def _check_captcha(self):
        """Check if a CAPTCHA appeared. Raises CaptchaError if found."""
        try:
            captcha = self.page.locator(SELECTORS["captcha_text"])
            if captcha.count() > 0 and captcha.first.is_visible():
                raise CaptchaError(
                    "CAPTCHA detected! Please solve it manually and restart the script."
                )
        except PlaywrightTimeout:
            pass

    def _check_no_responses(self):
        """Check if the job has no applicant responses."""
        try:
            no_resp = self.page.locator(SELECTORS["no_responses"])
            return no_resp.count() > 0 and no_resp.first.is_visible()
        except Exception:
            return False

    def _get_total_pages(self):
        """Parse 'Page X of Y' to extract total pages."""
        try:
            page_text = self.page.locator(SELECTORS["page_value"]).first.text_content()
            match = re.search(r"of\s+(\d+)", page_text)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return 1

    def _has_next_page(self):
        """Check if a next-page button exists and is clickable."""
        try:
            next_btn = self.page.locator(SELECTORS["next_page"]).first
            return next_btn.is_visible()
        except Exception:
            return False

    def collect_all_job_ids(self):
        """Navigate job listing pages and collect all job IDs."""
        self.log(f"Navigating to job listing: {JOB_LISTING_URL}")
        self.page.goto(JOB_LISTING_URL, timeout=30000)
        self._sleep(TIMING["page_load_wait"])

        # Check for login redirect
        if "login" in self.page.url.lower():
            raise RuntimeError(
                "Redirected to login page. Cookies may be invalid or expired."
            )

        self._check_captcha()

        all_jobs = []
        page_num = 1

        while True:
            if self._stop_requested:
                break

            self.log(f"Scanning job listing page {page_num}...")

            # Extract job links
            links = self.page.locator(SELECTORS["job_links"])
            count = links.count()

            for i in range(count):
                href = links.nth(i).get_attribute("href") or ""
                match = re.search(SELECTORS["job_link_pattern"], href)
                if match:
                    job_id = match.group(1)
                    # Try to get job title from the link or parent
                    title = links.nth(i).text_content().strip() or job_id
                    all_jobs.append({"id": job_id, "title": title})

            self.log(f"  Found {count} jobs on page {page_num}")

            # Check for next page
            if not self._has_next_page():
                break

            self.page.locator(SELECTORS["next_page"]).first.click()
            self._sleep(TIMING["after_next_page"])
            page_num += 1

        # Deduplicate by job ID
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job["id"] not in seen:
                seen.add(job["id"])
                unique_jobs.append(job)

        self.log(f"Total unique jobs found: {len(unique_jobs)}")
        return unique_jobs

    def download_cvs_for_job(self, job_id, job_title=""):
        """Download all CVs for a single job posting."""
        url = JOB_APPLIES_URL.format(job_id=job_id)
        self.page.goto(url, timeout=30000)
        self._sleep(TIMING["page_load_wait"])

        self._check_captcha()

        # Check for no responses
        if self._check_no_responses():
            self.log(f"  No responses for job {job_title} — skipping")
            return 0

        # Set page size to 160 (max)
        try:
            dropdown = self.page.locator(SELECTORS["show_dropdown"])
            if dropdown.count() > 0 and dropdown.first.is_visible():
                dropdown.first.click()
                self._sleep(TIMING["after_show_dropdown"])
                self.page.locator(SELECTORS["show_160"]).click()
                self._sleep(TIMING["after_show_select"])
        except Exception as e:
            self.log(f"  Could not set page size to 160: {e}")

        # Get total pages
        total_pages = self._get_total_pages()
        self.log(f"  {total_pages} page(s) of applicants")

        download_count = 0

        for page_num in range(1, total_pages + 1):
            if self._stop_requested:
                break

            self._check_captcha()

            self.log(f"  Page {page_num}/{total_pages}: selecting all & downloading...")

            # Click Select All
            try:
                select_all = self.page.locator(SELECTORS["select_all_label"])
                if select_all.count() > 0 and select_all.first.is_visible():
                    select_all.first.click()
                    self._sleep(TIMING["after_select_all"])
                else:
                    self.log(f"  Select All not found on page {page_num} — skipping")
                    continue
            except Exception as e:
                self.log(f"  Error clicking Select All: {e}")
                continue

            # Click Download
            try:
                download_btn = self.page.locator(SELECTORS["download_btn"])
                if download_btn.count() > 0 and download_btn.first.is_visible():
                    download_btn.first.click()
                    self._sleep(TIMING["after_download"])
                    download_count += 1
                    self.log(f"  Downloaded batch from page {page_num}")
                else:
                    self.log(f"  Download button not found on page {page_num}")
            except Exception as e:
                self.log(f"  Error clicking Download: {e}")

            # Navigate to next page if not last
            if page_num < total_pages:
                try:
                    if self._has_next_page():
                        self.page.locator(SELECTORS["next_page"]).first.click()
                        self._sleep(TIMING["after_next_page"])
                except Exception as e:
                    self.log(f"  Error navigating to next page: {e}")
                    break

        return download_count

    def run(self):
        """Main entry point: collect jobs, then download CVs for each."""
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        self.setup_browser()
        self.progress.mark_started()

        try:
            # Step 1: Collect all job IDs
            jobs = self.collect_all_job_ids()

            if not jobs:
                self.log("No jobs found. Check if cookies are valid.")
                return

            # Filter out already completed jobs
            remaining = [j for j in jobs if not self.progress.is_completed(j["id"])]
            skipped = len(jobs) - len(remaining)
            if skipped > 0:
                self.log(f"Skipping {skipped} already-completed jobs (resuming)")

            # Step 2: Download CVs for each job
            for i, job in enumerate(remaining):
                if self._stop_requested:
                    self.log("Stop requested. Saving progress...")
                    break

                self.log(
                    f"\n[Job {i+1}/{len(remaining)}] {job['title']} ({job['id']})"
                )

                try:
                    dl_count = self.download_cvs_for_job(job["id"], job["title"])
                    self.progress.mark_complete(job["id"], job["title"], dl_count)
                    self.log(f"  Completed: {dl_count} batch download(s)")
                except CaptchaError as e:
                    self.log(f"\n  CAPTCHA DETECTED: {e}")
                    self.log("  Please solve the CAPTCHA manually and restart.")
                    break
                except Exception as e:
                    self.log(f"  Error processing job {job['id']}: {e}")
                    # Continue to next job instead of stopping
                    continue

                self._sleep(TIMING["between_jobs"])

            # Final stats
            stats = self.progress.get_stats()
            self.log(f"\nDone! {stats['completed']} jobs processed, "
                     f"{stats['total_downloads']} total batch downloads.")

        finally:
            self.cleanup()


if __name__ == "__main__":
    import json

    # For testing: paste cookies JSON here or load from file
    cookie_file = os.path.join(os.path.dirname(__file__), "cookies.json")
    if os.path.exists(cookie_file):
        with open(cookie_file) as f:
            cookies = json.load(f)
    else:
        print("Create a cookies.json file with your Naukri cookies to run standalone.")
        exit(1)

    tracker = ProgressTracker()
    downloader = NaukriBulkDownloader(cookies, tracker)
    downloader.run()

"""
Tracks completed job IDs to support resume-after-interruption.
Saves state to progress.json so the script can pick up where it left off.
"""

import json
import os
import time
from config import PROGRESS_FILE


class ProgressTracker:
    def __init__(self, filepath=PROGRESS_FILE):
        self.filepath = filepath
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                return json.load(f)
        return {
            "completed_jobs": {},  # job_id -> {title, completed_at}
            "total_downloads": 0,
            "started_at": None,
        }

    def _save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=2)

    def is_completed(self, job_id):
        return str(job_id) in self.data["completed_jobs"]

    def mark_complete(self, job_id, job_title="", download_count=0):
        self.data["completed_jobs"][str(job_id)] = {
            "title": job_title,
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "downloads": download_count,
        }
        self.data["total_downloads"] += download_count
        self._save()

    def mark_started(self):
        if not self.data["started_at"]:
            self.data["started_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self._save()

    def get_stats(self):
        return {
            "completed": len(self.data["completed_jobs"]),
            "total_downloads": self.data["total_downloads"],
            "started_at": self.data["started_at"],
        }

    def reset(self):
        self.data = {
            "completed_jobs": {},
            "total_downloads": 0,
            "started_at": None,
        }
        self._save()

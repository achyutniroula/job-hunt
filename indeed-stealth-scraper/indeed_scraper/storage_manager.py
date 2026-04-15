"""
storage_manager.py — Save job results to JSON and CSV.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .job_parser import JOB_FIELDS
from .logger import get_logger

log = get_logger(__name__)


class StorageManager:
    """
    Writes parsed job dicts to timestamped JSON and CSV files.

    The CSV file is opened once in append mode so successive paginated
    batches accumulate in the same file without rewriting headers.
    """

    def __init__(self, output_dir: str = "output") -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._json_path = self._output_dir / f"jobs_{ts}.json"
        self._csv_path = self._output_dir / f"jobs_{ts}.csv"

        self._all_jobs: list[dict] = []
        self._csv_initialized = False

        log.info(f"Storage initialised | JSON: {self._json_path} | CSV: {self._csv_path}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_batch(self, jobs: list[dict]) -> None:
        """Persist a batch of parsed jobs to both JSON and CSV."""
        if not jobs:
            return
        self._all_jobs.extend(jobs)
        self._write_json()
        self._append_csv(jobs)
        log.info(f"Saved batch of {len(jobs)} jobs | total so far: {len(self._all_jobs)}")

    def save_all(self, jobs: list[dict]) -> None:
        """Replace the accumulated list with the given jobs and persist."""
        self._all_jobs = jobs
        self._write_json()
        # Rewrite CSV from scratch
        self._csv_initialized = False
        self._append_csv(jobs)

    @property
    def json_path(self) -> Path:
        return self._json_path

    @property
    def csv_path(self) -> Path:
        return self._csv_path

    @property
    def total_saved(self) -> int:
        return len(self._all_jobs)

    # ------------------------------------------------------------------
    # Internal writers
    # ------------------------------------------------------------------

    def _write_json(self) -> None:
        try:
            with open(self._json_path, "w", encoding="utf-8") as f:
                json.dump(self._all_jobs, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            log.error(f"Failed to write JSON: {exc}")

    def _append_csv(self, jobs: list[dict]) -> None:
        if not jobs:
            return
        try:
            write_header = not self._csv_initialized
            with open(self._csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=list(JOB_FIELDS),
                    extrasaction="ignore",
                )
                if write_header:
                    writer.writeheader()
                    self._csv_initialized = True
                writer.writerows(jobs)
        except OSError as exc:
            log.error(f"Failed to write CSV: {exc}")

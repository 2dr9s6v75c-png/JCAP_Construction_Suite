"""
JCAP Construction Suite
Auto Assignment Worker

Standalone background worker for 24/7 Material Request auto-assignment.

Production defaults:
- Auto-assign after 60 minutes
- Poll PostgreSQL every 60 seconds
- Process all currently overdue Material Requests each cycle

This worker does not require the JCAP desktop application to be open.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from modules.quotation.services.auto_assignment_service import (
    AutoAssignmentService,
)


DEFAULT_THRESHOLD_MINUTES = 60
DEFAULT_POLL_SECONDS = 60
DEFAULT_MAX_ASSIGNMENTS_PER_CYCLE = 100

LOG_DIRECTORY = Path("logs")
LOG_FILE = LOG_DIRECTORY / "auto_assignment_worker.log"


def configure_logging() -> None:
    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if this module is reloaded.
    if root_logger.handlers:
        return

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "JCAP 24/7 Material Request Auto Assignment Worker"
        )
    )

    parser.add_argument(
        "--threshold-minutes",
        type=int,
        default=DEFAULT_THRESHOLD_MINUTES,
        help=(
            "Minutes an MR may remain New and unassigned before "
            "auto-assignment. Default: 60."
        ),
    )

    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=DEFAULT_POLL_SECONDS,
        help=(
            "Seconds between worker checks. Default: 60."
        ),
    )

    parser.add_argument(
        "--max-assignments",
        type=int,
        default=DEFAULT_MAX_ASSIGNMENTS_PER_CYCLE,
        help=(
            "Maximum MRs processed during one worker cycle. "
            "Default: 100."
        ),
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help=(
            "Run one auto-assignment cycle and exit. "
            "Useful for controlled testing."
        ),
    )

    return parser


def validate_args(args: argparse.Namespace) -> None:
    if args.threshold_minutes < 1:
        raise ValueError(
            "--threshold-minutes must be at least 1."
        )

    if args.poll_seconds < 5:
        raise ValueError(
            "--poll-seconds must be at least 5."
        )

    if args.max_assignments < 1:
        raise ValueError(
            "--max-assignments must be at least 1."
        )


def run_cycle(
    service: AutoAssignmentService,
    *,
    threshold_minutes: int,
    max_assignments: int,
) -> list[dict]:
    results = service.auto_assign_all_due(
        threshold_minutes=threshold_minutes,
        max_assignments=max_assignments,
    )

    if not results:
        logging.info(
            "No Material Requests are currently due for auto-assignment."
        )
        return []

    for result in results:
        material_request = result.get("material_request") or {}
        assigned_to = result.get("assigned_to") or {}

        logging.info(
            "AUTO ASSIGNED | MR=%s | Officer=%s | Threshold=%s min",
            material_request.get("mr_number") or "Unknown",
            assigned_to.get("full_name") or "Unknown",
            result.get("threshold_minutes"),
        )

    logging.info(
        "Auto-assignment cycle completed. Assigned %s MR(s).",
        len(results),
    )

    return results


def main() -> int:
    configure_logging()

    parser = build_parser()
    args = parser.parse_args()

    try:
        validate_args(args)
    except ValueError as error:
        logging.error("%s", error)
        return 2

    logging.info("=" * 72)
    logging.info("JCAP Auto Assignment Worker starting.")
    logging.info(
        "Threshold: %s minute(s)",
        args.threshold_minutes,
    )
    logging.info(
        "Poll interval: %s second(s)",
        args.poll_seconds,
    )
    logging.info(
        "Maximum assignments per cycle: %s",
        args.max_assignments,
    )
    logging.info(
        "Mode: %s",
        "ONE CYCLE" if args.once else "CONTINUOUS 24/7",
    )
    logging.info("=" * 72)

    service = AutoAssignmentService()

    try:
        while True:
            try:
                run_cycle(
                    service,
                    threshold_minutes=args.threshold_minutes,
                    max_assignments=args.max_assignments,
                )
            except Exception:
                logging.exception(
                    "Auto-assignment cycle failed. "
                    "The worker will continue running."
                )

            if args.once:
                break

            time.sleep(args.poll_seconds)

    except KeyboardInterrupt:
        logging.info(
            "JCAP Auto Assignment Worker stopped by user."
        )

    logging.info("JCAP Auto Assignment Worker exited.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
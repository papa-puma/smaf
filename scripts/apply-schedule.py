#!/usr/bin/env python3
"""Apply per-semester schedule.yml values across the course tree.

For every `courses/<id>/schedule.yml` that exists, this script:

  1. Writes a managed block of per-semester metadata into the course-level
     `_metadata.yml` (between BEGIN/END markers, idempotent).
  2. Generates one `_metadata.yml` per lecture folder containing the
     `date`, `week`, `venue`, and `time` for that lecture (auto-generated,
     gitignored).

Quarto's pre-render hook calls this script, so a `quarto render` always
sees fresh per-semester metadata. The slides.qmd files themselves carry
ONLY stable content (title, subtitle, topics) and never change semester
to semester.

Usage (manual):
    python scripts/apply-schedule.py [--dry-run]

Wired into `_quarto.yml` via:
    project:
      pre-render: python scripts/apply-schedule.py
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "ERROR: PyYAML is required. Install with `pip install pyyaml`.\n"
    )
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parent.parent
COURSES_DIR = REPO_ROOT / "courses"

BEGIN_MARKER = "# === BEGIN auto-generated from schedule.yml — do not hand-edit below ==="
END_MARKER = "# === END auto-generated ==="


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _format_human_date(value: Any) -> str:
    """Render a date as e.g. '19 January 2026'.

    Accepts a datetime.date / datetime.datetime, an ISO string, or returns
    the input unchanged if it can't be parsed.
    """
    if isinstance(value, (dt.date, dt.datetime)):
        return value.strftime("%-d %B %Y") if sys.platform != "win32" else value.strftime("%#d %B %Y")
    if isinstance(value, str):
        try:
            d = dt.date.fromisoformat(value)
        except ValueError:
            return value
        return d.strftime("%-d %B %Y") if sys.platform != "win32" else d.strftime("%#d %B %Y")
    return str(value)


def _format_iso_date(value: Any) -> str:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()[:10]
    return str(value)


def _format_short_date(value: Any) -> str:
    """Render a date as DD.MM.YYYY (German short form, useful in slide tables)."""
    if isinstance(value, (dt.date, dt.datetime)):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, str):
        try:
            d = dt.date.fromisoformat(value)
        except ValueError:
            return value
        return d.strftime("%d.%m.%Y")
    return str(value)


def _yaml_dump(data: dict[str, Any]) -> str:
    """Dump YAML with stable, human-readable formatting."""
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=100,
    )


# ----------------------------------------------------------------------
# Per-course handling
# ----------------------------------------------------------------------

def build_course_managed_block(schedule: dict[str, Any]) -> dict[str, Any]:
    """Return the dict that goes into the course `_metadata.yml` managed block.

    Flattens select schedule.yml fields into top-level keys so they are easy
    to reference from any qmd in the course folder via `{{< meta KEY >}}`.
    """
    out: dict[str, Any] = {}
    out["semester"] = schedule.get("semester", "")
    out["exam-id"] = str(schedule.get("exam-id", ""))
    out["registration-deadline"] = _format_human_date(schedule.get("registration-deadline", ""))
    out["registration-deadline-iso"] = _format_iso_date(schedule.get("registration-deadline", ""))
    out["registration-system"] = schedule.get("registration-system", "")
    out["default-venue"] = schedule.get("default-venue", "")
    out["default-time"] = schedule.get("default-time", "")

    # Flatten assignment deadlines into easy-to-reference keys.
    assignments = schedule.get("assignments", {}) or {}
    for slug, meta in assignments.items():
        if not isinstance(meta, dict):
            continue
        deadline = meta.get("deadline")
        weight = meta.get("weight")
        out[f"{slug}-deadline"] = _format_human_date(deadline)
        out[f"{slug}-deadline-iso"] = _format_iso_date(deadline)
        if weight is not None:
            out[f"{slug}-weight"] = weight

    # Flatten lecture dates so individual slide bodies can reference them
    # via {{< meta lecture-NN-slug-date >}} (and the short DD.MM.YYYY form).
    lectures = schedule.get("lectures", {}) or {}
    for slug, meta in lectures.items():
        if not isinstance(meta, dict):
            continue
        date_val = meta.get("date")
        out[f"{slug}-date"] = _format_human_date(date_val)
        out[f"{slug}-date-short"] = _format_short_date(date_val)
        out[f"{slug}-date-iso"] = _format_iso_date(date_val)
        if meta.get("week") is not None:
            out[f"{slug}-week"] = meta["week"]
        if meta.get("time"):
            out[f"{slug}-time"] = meta["time"]
        if meta.get("venue"):
            out[f"{slug}-venue"] = meta["venue"]

    return out


def write_course_metadata(course_dir: Path, managed: dict[str, Any], dry_run: bool = False) -> None:
    """Update the course-level `_metadata.yml` managed block, leaving any
    hand-edited content above the BEGIN marker untouched.

    If the file does not exist or has no markers, creates / appends them.
    """
    meta_path = course_dir / "_metadata.yml"
    managed_yaml = _yaml_dump(managed).rstrip() + "\n"
    block = f"{BEGIN_MARKER}\n{managed_yaml}{END_MARKER}\n"

    existing = meta_path.read_text(encoding="utf-8") if meta_path.exists() else ""

    if BEGIN_MARKER in existing and END_MARKER in existing:
        head, _, rest = existing.partition(BEGIN_MARKER)
        _, _, tail = rest.partition(END_MARKER)
        new_text = head.rstrip() + ("\n\n" if head.strip() else "") + block + tail.lstrip()
    else:
        sep = "\n\n" if existing.strip() else ""
        new_text = existing.rstrip() + sep + block

    if dry_run:
        print(f"[dry-run] would write {meta_path}")
        return
    meta_path.write_text(new_text, encoding="utf-8")
    print(f"  wrote {meta_path.relative_to(REPO_ROOT)}")


def write_lecture_metadata(
    lecture_folder: Path,
    lecture_meta: dict[str, Any],
    defaults: dict[str, Any],
    dry_run: bool = False,
) -> None:
    """Write a fully-auto-generated `_metadata.yml` inside one lecture folder."""
    out: dict[str, Any] = {}
    if "week" in lecture_meta:
        out["week"] = lecture_meta["week"]
    if "date" in lecture_meta:
        out["date"] = _format_iso_date(lecture_meta["date"])
    out["venue"] = lecture_meta.get("venue", defaults.get("default-venue", ""))
    out["time"] = lecture_meta.get("time", defaults.get("default-time", ""))
    if "recording" in lecture_meta:
        out["recording"] = lecture_meta["recording"]
    if "readings" in lecture_meta:
        out["readings"] = lecture_meta["readings"]

    header = (
        "# Auto-generated by scripts/apply-schedule.py from ../../schedule.yml.\n"
        "# Do NOT hand-edit; changes will be overwritten on next render.\n\n"
    )
    text = header + _yaml_dump(out)

    target = lecture_folder / "_metadata.yml"
    if dry_run:
        print(f"[dry-run] would write {target}")
        return
    target.write_text(text, encoding="utf-8")
    print(f"  wrote {target.relative_to(REPO_ROOT)}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def process_course(course_dir: Path, dry_run: bool = False) -> int:
    schedule_path = course_dir / "schedule.yml"
    if not schedule_path.exists():
        return 0

    print(f"Applying schedule for {course_dir.relative_to(REPO_ROOT)}")
    with schedule_path.open(encoding="utf-8") as fh:
        schedule = yaml.safe_load(fh) or {}

    # 1. Course-level metadata
    managed = build_course_managed_block(schedule)
    write_course_metadata(course_dir, managed, dry_run=dry_run)

    # 2. Per-lecture metadata
    lectures_root = course_dir / "lectures"
    lectures_cfg = schedule.get("lectures", {}) or {}
    for folder_name, lecture_meta in lectures_cfg.items():
        lecture_folder = lectures_root / folder_name
        if not lecture_folder.is_dir():
            print(f"  WARNING: lecture folder missing for entry '{folder_name}' — skipping",
                  file=sys.stderr)
            continue
        if not isinstance(lecture_meta, dict):
            lecture_meta = {}
        write_lecture_metadata(
            lecture_folder,
            lecture_meta,
            defaults=schedule,
            dry_run=dry_run,
        )

    return 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true", help="Print actions without writing.")
    args = p.parse_args(argv)

    if not COURSES_DIR.is_dir():
        print(f"No courses directory found at {COURSES_DIR}", file=sys.stderr)
        return 0

    processed = 0
    for course_dir in sorted(COURSES_DIR.iterdir()):
        if not course_dir.is_dir():
            continue
        processed += process_course(course_dir, dry_run=args.dry_run)

    if processed == 0:
        print("No schedule.yml files found — nothing to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

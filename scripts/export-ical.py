#!/usr/bin/env python3
"""Export a course timetable as an iCalendar (.ics) file.

Reads each lecture's YAML front-matter (`date`, optional `time`, `duration`,
`location`) and writes a single .ics file students can subscribe to.

Usage:
    python scripts/export-ical.py courses/research-in-finance \\
        --time "16:00" --duration 90 --location "Helmholtzstraße 22"

Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Re-use the parser from the moodle generator
sys.path.insert(0, str(Path(__file__).parent))
try:
    from importlib import import_module
    moodle_module = import_module("generate-moodle-setup".replace("-", "_"))
    parse_yaml_front_matter = moodle_module.parse_yaml_front_matter  # type: ignore[attr-defined]
    discover_lectures = moodle_module.discover_lectures  # type: ignore[attr-defined]
except Exception:
    # Inline fallback if module import fails (filenames with dashes are awkward)
    def parse_yaml_front_matter(text: str) -> dict[str, Any]:
        if not text.startswith("---"):
            return {}
        end = text.find("\n---", 3)
        if end == -1:
            return {}
        block = text[3:end].strip()
        out: dict[str, Any] = {}
        current_list: list[str] | None = None
        for raw in block.splitlines():
            line = raw.rstrip()
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            list_match = re.match(r"^(\s+)-\s+(.*)$", line)
            if list_match and current_list is not None:
                current_list.append(list_match.group(2).strip().strip('"').strip("'"))
                continue
            kv = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
            if kv:
                key, val = kv.group(1), kv.group(2).strip()
                if val == "":
                    current_list = []
                    out[key] = current_list
                else:
                    current_list = None
                    out[key] = val.strip('"').strip("'")
        return out

    def discover_lectures(course_dir: Path) -> list[dict[str, Any]]:
        root = course_dir / "lectures"
        if not root.is_dir():
            return []
        out = []
        for p in sorted(root.glob("lecture-*/slides.qmd")):
            meta = parse_yaml_front_matter(p.read_text(encoding="utf-8"))
            meta["_folder"] = p.parent.name
            out.append(meta)
        return out


def ics_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def fmt_dt_local(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def fmt_dt_utc(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("course_dir", type=Path)
    p.add_argument("--time", default="14:00", help="Default lecture start time HH:MM")
    p.add_argument("--duration", type=int, default=90, help="Default duration in minutes")
    p.add_argument("--location", default="Helmholtzstraße 22, Ulm")
    p.add_argument("--tz", default="Europe/Berlin", help="Timezone label (informational)")
    p.add_argument("-o", "--output", type=Path, default=None)
    args = p.parse_args()

    if not args.course_dir.is_dir():
        print(f"Course not found: {args.course_dir}", file=sys.stderr)
        return 2

    lectures = discover_lectures(args.course_dir)
    if not lectures:
        print("No lectures found.", file=sys.stderr)
        return 1

    course_id = args.course_dir.name
    out_path = args.output or (args.course_dir / "course.ics")
    now = datetime.utcnow()

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//Ulm SMF//{course_id}//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for lec in lectures:
        date_str = str(lec.get("date", "")).strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            continue
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            hh, mm = map(int, args.time.split(":"))
            dt_start = d.replace(hour=hh, minute=mm)
            dt_end = dt_start + timedelta(minutes=args.duration)
        except ValueError:
            continue

        title = ics_escape(str(lec.get("title", lec.get("_folder", ""))))
        topics = lec.get("topics")
        if isinstance(topics, list) and topics:
            description = ics_escape("Topics: " + "; ".join(str(t) for t in topics))
        else:
            description = ""

        uid = f"{course_id}-{lec.get('_folder', uuid.uuid4().hex)}@uni-ulm.de"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{fmt_dt_utc(now)}",
            f"DTSTART;TZID={args.tz}:{fmt_dt_local(dt_start)}",
            f"DTEND;TZID={args.tz}:{fmt_dt_local(dt_end)}",
            f"SUMMARY:{title}",
            f"LOCATION:{ics_escape(args.location)}",
        ])
        if description:
            lines.append(f"DESCRIPTION:{description}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    out_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

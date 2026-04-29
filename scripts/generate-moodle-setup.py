#!/usr/bin/env python3
"""Generate MOODLE-SETUP.md for a course.

Reads each lecture's YAML front-matter (title, date, week, topics) and emits a
copy-paste checklist of section titles + GitHub Pages URLs. The professor
pastes this into Moodle once per term; future content edits propagate via the
existing URLs.

Usage:
    python scripts/generate-moodle-setup.py courses/research-in-finance \\
        --term "Summer 2026" \\
        --site-url https://<user>.github.io/<repo>

The script uses only the Python standard library — no third-party deps.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


def parse_yaml_front_matter(text: str) -> dict[str, Any]:
    """Minimal YAML front-matter parser. Sufficient for our flat structure.

    Handles: scalars, dates, simple lists with `-` indented items, quoted strings.
    Does NOT handle: nested mappings, anchors, flow-style sequences.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end].strip()

    result: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for raw in block.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        list_match = re.match(r"^(\s+)-\s+(.*)$", line)
        if list_match and current_list is not None:
            current_list.append(_strip_quotes(list_match.group(2).strip()))
            continue

        kv = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
        if kv:
            key = kv.group(1)
            val = kv.group(2).strip()
            if val == "":
                current_key = key
                current_list = []
                result[key] = current_list
            else:
                current_key = None
                current_list = None
                result[key] = _strip_quotes(val)

    return result


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def discover_lectures(course_dir: Path) -> list[dict[str, Any]]:
    """Return a list of lecture metadata dicts, sorted by (week, date)."""
    lectures_root = course_dir / "lectures"
    if not lectures_root.is_dir():
        return []

    lectures = []
    for slides_path in sorted(lectures_root.glob("lecture-*/slides.qmd")):
        text = slides_path.read_text(encoding="utf-8")
        meta = parse_yaml_front_matter(text)
        meta["_folder"] = slides_path.parent.name
        meta["_path"] = slides_path
        meta["_has_assignment"] = (slides_path.parent / "assignment.qmd").exists()
        meta["_has_exam"] = (slides_path.parent / "exam.qmd").exists()
        lectures.append(meta)

    def sort_key(m: dict[str, Any]) -> tuple[int, str]:
        try:
            week = int(m.get("week", 999))
        except (TypeError, ValueError):
            week = 999
        return (week, str(m.get("date", "")))

    lectures.sort(key=sort_key)
    return lectures


def discover_course_assignments(course_dir: Path) -> list[dict[str, Any]]:
    """Return a list of assignment metadata dicts for course-level assignments."""
    root = course_dir / "assignments"
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(root.glob("*.qmd")):
        meta = parse_yaml_front_matter(p.read_text(encoding="utf-8"))
        meta["_filename"] = p.stem
        out.append(meta)
    return out


def render_checklist(
    course_id: str,
    course_title: str,
    term: str,
    site_url: str,
    lectures: list[dict[str, Any]],
    assignments: list[dict[str, Any]] | None = None,
) -> str:
    site_url = site_url.rstrip("/")
    course_base = f"{site_url}/courses/{course_id}"
    assignments = assignments or []

    lines: list[str] = []
    lines.append(f"# Moodle setup — {course_title} — {term}")
    lines.append("")
    lines.append(
        "Create the matching topics in Moodle in the order shown below and paste the URLs as resource links. "
        "Re-running the generator after content edits **does not** require updating Moodle — the URLs are stable."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Topic: Course information")
    lines.append("")
    lines.append(f"- Syllabus: {course_base}/syllabus.html")
    lines.append(f"- Course homepage: {course_base}/index.html")
    lines.append(f"- Gradebook (staff only): {course_base}/gradebook.html")
    lines.append("")

    if assignments:
        lines.append("## Topic: Assignments")
        lines.append("")
        for a in assignments:
            title = a.get("title", a.get("_filename", ""))
            due = a.get("due-date", a.get("date", "TBD"))
            lines.append(f"- **{title}** (due {due}): {course_base}/assignments/{a['_filename']}.html")
        lines.append("")

    for lec in lectures:
        week = lec.get("week", "?")
        title = lec.get("title", lec["_folder"])
        folder = lec["_folder"]
        date = lec.get("date", "TBD")
        lec_base = f"{course_base}/lectures/{folder}"

        lines.append(f"## Topic: Week {week} — {title}")
        lines.append("")
        lines.append(f"*Date: {date}*")
        lines.append("")
        lines.append(f"- Slides: {lec_base}/slides.html")
        lines.append(f"- Notes: {lec_base}/notes.html")
        lines.append(f"- Handout (PDF): {lec_base}/slides-handout.pdf")
        if lec.get("_has_assignment"):
            lines.append(f"- Assignment: {lec_base}/assignment.html")
        if lec.get("_has_exam"):
            lines.append(f"- Sample exam: {lec_base}/exam.html")

        topics = lec.get("topics")
        if isinstance(topics, list) and topics:
            lines.append("")
            lines.append("**Topics covered:**")
            for t in topics:
                lines.append(f"- {t}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by `scripts/generate-moodle-setup.py`. Do not hand-edit.*")
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("course_dir", type=Path, help="Path to courses/<course-id>/")
    p.add_argument("--term", default="", help="Term label (e.g. 'Summer 2026')")
    p.add_argument(
        "--site-url",
        default="https://papa-puma.github.io/smaf",
        help="Base GitHub Pages URL (no trailing slash)",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path (default: <course_dir>/MOODLE-SETUP.md)",
    )
    args = p.parse_args()

    if not args.course_dir.is_dir():
        print(f"Course directory not found: {args.course_dir}", file=sys.stderr)
        return 2

    course_id = args.course_dir.name
    metadata_path = args.course_dir / "_metadata.yml"
    course_title = course_id
    term = args.term
    if metadata_path.exists():
        meta_text = metadata_path.read_text(encoding="utf-8")
        title_match = re.search(r"^\s*title:\s*\"?([^\"\n]+)\"?", meta_text, re.MULTILINE)
        term_match = re.search(r"^\s*term:\s*\"?([^\"\n]+)\"?", meta_text, re.MULTILINE)
        if title_match:
            course_title = title_match.group(1).strip()
        if not term and term_match:
            term = term_match.group(1).strip()

    lectures = discover_lectures(args.course_dir)
    assignments = discover_course_assignments(args.course_dir)
    if not lectures:
        print(f"No lectures found under {args.course_dir / 'lectures'}", file=sys.stderr)

    output = args.output or (args.course_dir / "MOODLE-SETUP.md")
    output.write_text(
        render_checklist(course_id, course_title, term, args.site_url, lectures, assignments),
        encoding="utf-8",
    )
    print(f"Wrote {output} ({len(lectures)} lecture(s), {len(assignments)} assignment(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

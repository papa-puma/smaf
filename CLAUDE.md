# CLAUDE.md — Conventions for AI Assistants

This file is read first by any AI assistant (Claude Code, Cursor, Continue.dev) operating on this repository. It is the **canonical specification** for all four supported workflows.

## Repository identity

- **Owner:** Institute of Strategic Management and Finance (SMF), Ulm University.
- **Visibility:** Private GitHub repo. Solutions and exam keys may live in-tree.
- **Student-facing surface:** GitHub Pages site, linked from Moodle. Never expose solutions in deployed output.

## Folder layout (must match exactly)

```
courses/<course-id>/
├── _metadata.yml
├── index.qmd
├── syllabus.qmd
├── gradebook.qmd
├── grades.csv
├── MOODLE-SETUP.md             # generated, do not hand-edit
└── lectures/
    ├── _metadata.yml
    └── lecture-NN-<slug>/
        ├── slides.qmd
        ├── assignment.qmd      # optional
        ├── exam.qmd            # optional
        └── images/
```

Rules:

- Course IDs are kebab-case, lowercase: `research-in-finance`, `behavioral-finance`.
- Lecture folders are `lecture-NN-<slug>/` where NN is zero-padded (`01`, `02`, …, `12`).
- Slug is kebab-case ASCII derived from the title (drop punctuation, replace spaces with `-`, lowercase).

## Required YAML front-matter for `slides.qmd`

```yaml
---
title: "Lecture 01: Introduction to Research in Finance"
subtitle: "Course overview and methodology"
date: 2026-04-21
week: 1
topics:
  - Course logistics
  - What is "research in finance"?
  - Empirical vs theoretical methods
authors:
  - "Prof. Dr. Andre Guettler"
---
```

The `date`, `week`, `title`, and `topics` fields are read by Quarto listings to populate the syllabus timetable and course homepage. **Do not skip them.**

## Workflow A — Create a new lecture

Trigger: a prompt of the form *"Create Lecture NN for the `<course-id>` course titled '<Title>'. Topics: …"*.

Steps:

1. **Verify course exists** — `courses/<course-id>/` must exist. If not, ask the user whether to scaffold the course first (Workflow E).
2. **Pick lecture number** — if not specified, list `courses/<course-id>/lectures/lecture-NN-*/` folders and pick the next integer.
3. **Slugify title** — lowercase, ASCII, kebab-case, max 6 words.
4. **Folder name** — `lecture-NN-<slug>/`.
5. **Copy templates** — copy `_templates/slides.qmd` to the new folder. If user asked for assignment / exam, also copy those templates.
6. **Fill front-matter** — write `title`, `subtitle` (if given), `date` (if given), `week` (week number = lecture number unless user says otherwise), `topics` (list from prompt).
7. **Stub topic sections** — for each topic, add `## <Topic>` followed by a placeholder bullet list.
8. **Do NOT edit the syllabus** — it auto-updates via Quarto listings.
9. **Do NOT manually update navbar / index** — the listing covers it.

## Workflow B — Update existing content

Trigger: a prompt that names an existing file or course element to modify.

Steps:

1. **Locate the target file** using glob (`courses/**/lecture-*/slides.qmd` etc.). Confirm with user if ambiguous.
2. **Read** the file before editing.
3. **Edit in place** — preserve YAML front-matter structure, preserve callout blocks, preserve solution gating in exams.
4. **Date shifts**: when asked to "shift all dates by N days", read every `slides.qmd` in the named course's `lectures/`, parse `date:`, add the offset, write back.
5. **Cross-file consistency** — if updating a topic, also check `assignment.qmd` and `exam.qmd` in the same lecture folder; ask the user before propagating.
6. **Never silently rename folders** — folder renames break URLs already pasted into Moodle. If a rename is needed, flag it explicitly to the user.

## Workflow C — Convert a PDF into a Quarto lecture

Trigger: a prompt referencing a PDF in `inputs/` (or a path the user provides).

Steps:

1. **Read the PDF** with the `Read` tool. For PDFs over 10 pages, paginate with the `pages` parameter (max 20 pages per call).
2. **Extract structure**:
   - Top-level headings → `# <slide title>` (slide separator) or `##` for sub-slides.
   - Bullet points → `-` lists.
   - Numbered lists → `1.` lists.
   - Inline math → `$…$`. Display math → `$$…$$`.
   - Tables → Markdown pipe tables.
   - Figures and complex diagrams → leave a TODO marker: `<!-- TODO: figure from PDF p.<n> — describe and recreate or import as image -->`.
3. **Map to slide template** — copy `_templates/slides.qmd`, fill front-matter (title, date, week, topics inferred from headings).
4. **Place output** — at `courses/<course-id>/lectures/lecture-NN-<slug>/slides.qmd` (use Workflow A's numbering rules).
5. **Report TODOs** — summarize at end of conversion how many figures/tables need manual review and where they are.

Heuristics:

- Page numbers, footers, and running headers in the PDF should be **stripped**, not converted.
- Multiple consecutive bullet slides with the same title → consolidate into one slide with all bullets.
- "Speaker notes" sections in the PDF → wrap in `::: notes` blocks.

## Workflow D — Regenerate the Moodle setup checklist

Trigger: *"Regenerate the Moodle setup file for `<course-id>` for the `<term>` term."*

Steps:

1. Run `python scripts/generate-moodle-setup.py courses/<course-id> --term "<term>"`.
2. The script walks the course folder, reads each lecture's front-matter, and emits `courses/<course-id>/MOODLE-SETUP.md`.
3. Confirm the file was generated and report its location.

If Python is unavailable, generate the file directly: read each `slides.qmd` front-matter, emit a Moodle topic per lecture with the URL pattern `https://<site-url>/courses/<course-id>/lectures/lecture-NN-<slug>/slides.html`.

## Workflow E — Scaffold a new course

Trigger: *"Scaffold a new course called `<course-id>` titled '<Title>', instructor '<Name>', term '<Term>'."*

Steps:

1. Copy `_templates/new-course/` to `courses/<course-id>/`.
2. Fill `_metadata.yml` (course title, term, instructor).
3. Add a navbar entry to root `_quarto.yml` for the new course.
4. Do NOT create any lectures — user will trigger Workflow A separately.

## General rules

- **Read before editing.** Always.
- **Preserve YAML front-matter.** Don't reorder fields without reason.
- **Solutions: false is the default.** Never flip `solutions: true` in committed files.
- **One source of truth.** The syllabus timetable, course homepage lecture list, and `MOODLE-SETUP.md` are all generated. Don't hand-edit them.
- **No emojis** in lecture content unless the user explicitly asks.
- **Keep slides concise.** A new slide every ~30–60 words. Use `incremental: true` only on lists where pacing matters.
- **Mathematical notation** is LaTeX between `$…$` (inline) or `$$…$$` (display).
- **Citations** use Quarto's `[@key]` syntax with a `references.bib` if/when one is added.

## Style conventions

- **Slide titles**: sentence case, no trailing period.
- **Section headings within slides**: same.
- **Callouts**: prefer Quarto native callouts (`::: {.callout-note title="Learning Objectives"}`).
- **Code chunks**: language-tagged fences (` ```python `, ` ```r `).
- **Speaker notes**: `::: notes` block, written in second person to the speaker.

## When in doubt

Ask the user. Don't invent a topic, a date, an exam question, or a citation. Fill placeholders with `[TODO]` or `[TBD]` and surface them in your reply.

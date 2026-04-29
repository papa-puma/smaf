# SMF Teaching Repository

> Source-of-truth repository for all teaching materials of the **Institute of Strategic Management and Finance (SMF)**, Faculty of Mathematics and Economics, **Ulm University**.

This repository is the authoring system for slides, syllabi, assignments, exams, and gradebook data for one or more SMF courses. All content is **pure Markdown via [Quarto](https://quarto.org)**, branded for Ulm/SMF, rendered with one command, and deployed to GitHub Pages on every push to `main`. **Moodle is the student entry point** — Moodle pages just link to the rendered URLs hosted on GitHub Pages.

## What's inside

| Path | Purpose |
|---|---|
| `_quarto.yml` | Site-wide Quarto config (theme, formats, navbar) |
| `_brand.yml` | Ulm/SMF brand tokens (colors, fonts, logos) |
| `_extensions/ulm-academic/` | Custom Quarto extension — reveal.js theme + format defaults |
| `_templates/` | Master scaffolds (`slides.qmd`, `assignment.qmd`, `exam.qmd`, new-course) |
| `assets/` | Logos, shared images, SCSS partials, PDF preamble |
| `courses/<course-id>/` | One folder per course |
| `courses/<course-id>/lectures/lecture-NN-slug/` | One folder per lecture |
| `scripts/` | Helper scripts (Moodle setup generator, optional iCal export) |
| `.github/workflows/` | CI: render + deploy to GH Pages |
| `CLAUDE.md` | Conventions for AI assistants (Cursor / Continue / Claude Code) |

## Initial setup

### 1. Install Quarto

- **Windows:** `winget install --id Posit.Quarto` (or download from <https://quarto.org/docs/get-started/>)
- Verify: `quarto --version` (must be ≥ 1.5)

### 2. Install VS Code extensions (auto-prompted)

The repo's `.vscode/extensions.json` recommends Quarto, YAML, and Spell Checker. VS Code prompts on first open.

### 3. Drop the logos in

Place these files (SVG preferred):

- `assets/logos/uulm.svg` — Ulm University logo
- `assets/logos/smf.svg` — SMF institute logo

The Ulm logo is available from the official site: <https://www.uni-ulm.de/_assets/a92153751098915699a1afa17e77f864/Images/logo-uni-ulm.svg>

### 4. First render

From the repo root:

```bash
quarto preview
```

Opens a live-reload preview at `http://localhost:4200`. Edit any `.qmd` file and the browser refreshes automatically.

For a one-shot full build:

```bash
quarto render
```

Output lands in `_site/`.

### 5. Push to GitHub (private repo)

```bash
git init
git add .
git commit -m "Initial scaffold"
gh repo create papa-puma/smaf --private --source=. --push
```

Then in the GitHub UI: **Settings → Pages → Source: `gh-pages` branch**. The first push to `main` will run `.github/workflows/publish.yml`, deploy the site, and Pages will go live.

## The four workflows

This repo is designed to be driven from any AI editor (Cursor, Continue.dev, Claude Code). All conventions are encoded in [`CLAUDE.md`](CLAUDE.md). Use plain English prompts — the AI reads `CLAUDE.md` and acts deterministically.

### Workflow A — Create a new lecture (one prompt)

> Create Lecture 03 for the research-in-finance course titled "Capital Structure Theory". Topics: Modigliani-Miller theorem, trade-off theory, pecking order theory. Schedule on 2026-05-12. Include assignment and exam.

The AI:

1. Picks the next lecture number (or uses the one you give).
2. Slugifies the title → `lecture-03-capital-structure-theory/`.
3. Copies the master templates and fills in front-matter (`title`, `subtitle`, `date`, `week`, `topics`).
4. Adds `## <Topic>` section stubs for each topic.
5. (Optional) generates `assignment.qmd` and `exam.qmd`.

The syllabus timetable updates **automatically** because it's a Quarto listing reading lecture front-matter. No manual index editing.

### Workflow B — Update existing content

> Add a section on "Modigliani-Miller with corporate taxes" between sections 2 and 3 of Lecture 03 slides.
> Replace question 2 of the Lecture 03 assignment with a problem on weighted average cost of capital.
> Shift all lecture dates in research-in-finance forward by 7 days for the new term.
> Update the syllabus deadline to 2026-07-15.

The AI edits in place and produces a clean git diff for review.

### Workflow C — Convert a PDF lecture into a Quarto lecture

1. Drop the PDF in `inputs/old-lecture-04.pdf` (folder is gitignored).
2. Prompt:

> Convert this PDF (`inputs/old-lecture-04.pdf`) into Lecture 04 of the research-in-finance course. Title: "Behavioral Corporate Finance".

The AI extracts headings, bullets, and math; populates `_templates/slides.qmd`; flags unclear figures with `<!-- TODO: figure from PDF p.7 -->` markers for your review.

### Workflow D — Regenerate the Moodle setup checklist

> Regenerate the Moodle setup file for research-in-finance for the summer 2026 term.

Or directly:

```bash
python scripts/generate-moodle-setup.py courses/research-in-finance --term "Summer 2026"
```

Produces `courses/research-in-finance/MOODLE-SETUP.md` — a copy-paste checklist of section titles + GH Pages URLs to drop into Moodle once.

## Solution gating (instructor vs student renders)

Every `exam.qmd` ships with `solutions: false` in its front-matter. Solution blocks are wrapped:

```markdown
::: {.content-visible when-meta="solutions"}
**Solution:** …
:::
```

- **Student-facing build** (deployed to GH Pages by the GitHub Actions workflow) always runs with `solutions: false` — solutions are stripped.
- **Instructor build** (local only):
  ```bash
  quarto render courses/research-in-finance/lectures/lecture-01-intro/exam.qmd --metadata solutions:true
  ```

## Daily workflow

```bash
# 1. Pull latest
git pull

# 2. Live preview
quarto preview

# 3. Edit content (or prompt your AI assistant)

# 4. Commit + push
git add .
git commit -m "Add lecture 04 on behavioral finance"
git push  # CI deploys to GH Pages
```

## Adding a new course

```
> Scaffold a new course called "behavioral-finance" with title "Behavioral Finance", instructor "Prof. Dr. Andre Guettler", term "Winter 2026/27".
```

The AI copies `_templates/new-course/` into `courses/behavioral-finance/` and updates the navbar in `_quarto.yml`.

## Branding

All Ulm/SMF brand tokens live in **two places only**:

1. `_brand.yml` — colors, fonts, logos.
2. `_extensions/ulm-academic/theme.scss` — reveal.js slide theme overrides.

Edit those once and the entire repo restyles.

| Token | Hex |
|---|---|
| Ulm blue | `#7D9AAA` |
| Ulm dark gray | `#575756` |
| Accent beige | `#A9A28D` |

## Repository conventions

See [`CLAUDE.md`](CLAUDE.md) for the canonical specification. Key rules:

- Lecture folders are `lecture-NN-slug/` (zero-padded, kebab-case slug).
- Every `slides.qmd` has YAML front-matter with at minimum: `title`, `date`, `week`, `topics`.
- The syllabus timetable is **never** edited by hand.
- Exams default to `solutions: false`.
- The repo is **private**.

## Troubleshooting

- **Preview doesn't refresh:** kill `quarto preview` and re-run.
- **PDF render fails:** install TinyTeX once with `quarto install tinytex`.
- **Listings table empty:** the lecture folder needs at least `slides.qmd` with `date:` in YAML.
- **Theme looks wrong:** the custom extension lives at `_extensions/ulm-academic/`. Check `theme:` in `_quarto.yml` references it correctly.

## License

Source files: see `LICENSE` (to be added). Course content: © Institute of Strategic Management and Finance, Ulm University.

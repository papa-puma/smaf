# SMF Teaching Repository

> Source-of-truth repository for all teaching materials of the **Institute of Strategic Management and Finance (SMF)**, Faculty of Mathematics and Economics, **Ulm University**.

This repo authors slides, syllabi, assignments, exams, and gradebook data for SMF courses as **pure Markdown via [Quarto](https://quarto.org)**. One command renders everything; CI deploys to GitHub Pages on every push to `main`. **Moodle is the student entry point** — Moodle pages just link to the rendered URLs hosted on GitHub Pages.

The deployed site lives at **<https://papa-puma.github.io/smaf/>**.

---

## What's inside

| Path | Purpose |
|---|---|
| `_quarto.yml` | Site-wide Quarto config (theme, formats, navbar, pre-render hook) |
| `_brand.yml` | Brand tokens (colors, fonts, logos) |
| `_extensions/ulm-academic/` | Custom Quarto extension — reveal.js theme |
| `_templates/` | Master scaffolds (`slides.qmd`, `assignment.qmd`, `exam.qmd`, new-course) |
| `assets/` | Logos, shared images, SCSS partials, PDF preamble |
| `courses/<course-id>/` | One folder per course — **never duplicated per semester** |
| `courses/<course-id>/schedule.yml` | Per-semester data (dates, deadlines, term, exam id) — the only file you edit when rolling over to a new term |
| `courses/<course-id>/lectures/lecture-NN-slug/` | One folder per lecture — content is stable across semesters |
| `scripts/apply-schedule.py` | Pre-render hook: injects `schedule.yml` values into Quarto metadata |
| `scripts/generate-moodle-setup.py` | Generates `MOODLE-SETUP.md` (the per-term checklist for Moodle) |
| `.github/workflows/publish.yml` | CI: render + deploy to GH Pages |
| `CLAUDE.md` | Conventions for AI assistants (Cursor / Continue / Claude Code) |

---

## A. First-time setup (≈ 15 minutes)

### 1. Install tools

| Tool | Why | Install |
|---|---|---|
| **Quarto** ≥ 1.5 | Renders the site | Windows: `winget install --id Posit.Quarto` · macOS: `brew install --cask quarto` · or <https://quarto.org/docs/get-started/> |
| **Python** ≥ 3.11 + `pyyaml` | Pre-render hook + Moodle generator | `pip install pyyaml pandas matplotlib` |
| **R + RStudio** | Course content (live coding in lectures) | <https://cran.r-project.org/> + <https://posit.co/download/rstudio-desktop> |
| **TinyTeX** (one-off) | PDF rendering | `quarto install tinytex` |

Verify:

```bash
quarto --version          # ≥ 1.5
python -c "import yaml"   # silent = success
```

### 2. Clone & render

```bash
git clone https://github.com/papa-puma/smaf.git
cd smaf
quarto preview
```

`quarto preview` opens a live-reload preview at `http://localhost:4200`. Edit any `.qmd` file and the browser refreshes. For a one-shot full build: `quarto render` (output lands in `_site/`).

### 3. VS Code extensions

Open the repo in VS Code; it auto-prompts to install the recommended extensions (Quarto, YAML, Spell Checker) from `.vscode/extensions.json`.

---

## B. Day-one workflows (every TA needs these)

### B1. Roll over to a new semester — **the most common task**

Slides do **not** change between semesters. The only thing that changes is the per-semester data: term string, exam id, registration deadline, lecture dates, venue, assignment deadlines.

Edit a single file, `courses/<course-id>/schedule.yml`:

```yaml
semester: "Summer 2026"
exam-id: "13337"
registration-deadline: 2026-04-30
default-venue: "Helmholtzstraße 22, Ulm"
default-time: "Wednesdays 14:15–15:45"

lectures:
  lecture-01-basics:        { week: 1, date: 2026-04-22 }
  lecture-02-data-handling: { week: 2, date: 2026-04-29 }
  ...

assignments:
  assignment-1-problem-set:    { deadline: 2026-07-13, weight: 50 }
  assignment-2-referee-report: { deadline: 2026-07-27, weight: 50 }
```

Then:

```bash
quarto render                                                # pre-render hook applies schedule.yml automatically
python scripts/generate-moodle-setup.py courses/<course-id>  # regenerate Moodle checklist
git add -A && git commit -m "Roll over to Summer 2026"
git push                                                     # CI deploys
```

The pre-render hook (`scripts/apply-schedule.py`) reads `schedule.yml` and injects all dates / venue / deadline strings into Quarto metadata that the qmd files already reference via `{{< meta key >}}` shortcodes. **Do not edit slides.qmd files for a roll-over.**

### B2. Update lecture content

Just edit `courses/<course-id>/lectures/lecture-NN-<slug>/slides.qmd`. Slide content is stable across semesters — feel free to fix a typo, replace a citation, add a new section, etc.

```bash
quarto preview      # see changes live
git add . && git commit -m "Lecture 02: clarify ggplot pipeline" && git push
```

### B3. Add a new lecture

Use the AI workflow (Workflow A in [`CLAUDE.md`](CLAUDE.md)) or do it manually:

```bash
# 1. Copy the template
cp -r _templates/slides.qmd courses/<course-id>/lectures/lecture-06-<slug>/slides.qmd

# 2. Edit front-matter (title, subtitle, topics — NO date/week, those go in schedule.yml)

# 3. Add the lecture to schedule.yml:
#       lectures:
#         lecture-06-<slug>: { week: 6, date: 2026-05-27 }

# 4. Render and commit.
```

The course homepage and syllabus listings auto-update.

### B4. Add a new course

Prompt the AI (Workflow E in `CLAUDE.md`) or copy `_templates/new-course/` to `courses/<new-course-id>/`. Fill in the static fields in the new `_metadata.yml`, create a `schedule.yml`, and add a navbar entry to `_quarto.yml`.

### B5. Convert a PDF lecture

Drop the PDF in `inputs/` (gitignored) and prompt the AI (Workflow C in `CLAUDE.md`):

> Convert this PDF (`inputs/old-lecture-04.pdf`) into Lecture 04 of `<course-id>` titled "Behavioral Corporate Finance".

The AI extracts headings, bullets, and math; populates `_templates/slides.qmd`; flags unclear figures with `<!-- TODO: figure from PDF p.7 -->` markers for your review.

### B6. Regenerate the Moodle setup checklist

```bash
python scripts/generate-moodle-setup.py courses/<course-id>
```

Produces `courses/<course-id>/MOODLE-SETUP.md` — a copy-paste checklist of Moodle topic titles + GH Pages URLs. **Re-running after content edits does NOT require updating Moodle** — the URLs are stable. Only the per-term roll-over (B1) creates a new Moodle-setup task.

### B7. Update grades

Edit `courses/<course-id>/grades.csv`, push. The `gradebook.qmd` page re-renders with new headline numbers, the score histogram, and the per-component breakdown.

---

## C. Less-frequent workflows

### C1. Add or extend the bibliography (`references.bib`)

A shared bibliography lives at the repo root: [`references.bib`](references.bib). It is wired into every Research-in-Finance lecture via `bibliography: ../../../../references.bib` in `courses/research-in-finance/lectures/_metadata.yml`, and into the syllabus via the qmd front-matter. New courses cite from the same file; adjust the relative path per depth.

Citation syntax:

- `[@key]` → "(Author, Year)" parenthetical.
- `@key` → "Author (Year)" textual.
- `[-@key]` → "(Year)" — author suppressed.

Each lecture ends with a `## References` heading containing `::: {#refs} :::`; Quarto auto-fills it with the formatted entries that appear cited above.

**Adding a new entry**: append a BibTeX block to `references.bib` and cite it from any qmd. Quarto picks it up on next render — no further config.

### C2. Archive a finished semester as a git tag

At the end of each term, capture the rendered state for posterity:

```bash
git tag -a winter-2025-26 -m "Final state, Winter 2025/2026"
git push origin winter-2025-26
```

To revisit a past semester's `schedule.yml`, slides, or grades:

```bash
git checkout winter-2025-26     # or browse on GitHub at /tree/winter-2025-26
```

**Naming convention:** lower-cased semester slug — `winter-2026-27`, `summer-2027`.

### C3. Add lecture recordings or external readings

Put them in `schedule.yml` under the relevant lecture:

```yaml
lecture-01-basics:
  week: 1
  date: 2026-04-22
  recording: "https://uni-ulm.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=…"
  readings:
    - title: "Tidy Finance with R, ch. 1"
      url:   "https://www.tidy-finance.org/r/introduction-to-tidy-finance.html"
```

`apply-schedule.py` injects `recording` and `readings` into the lecture's `_metadata.yml`, so any `{{< meta recording >}}` shortcode in the slides resolves at render time.

### C4. Run the instructor build (with solutions)

Every `exam.qmd` ships with `solutions: false` in its front-matter. Solution blocks are wrapped:

```markdown
::: {.content-visible when-meta="solutions"}
**Solution:** …
:::
```

- **Student-facing build** (deployed to GH Pages by `publish.yml`) always runs with `solutions: false` — solutions are stripped.
- **Instructor build** (local only):
  ```bash
  quarto render courses/<course-id>/lectures/lecture-NN-<slug>/exam.qmd --metadata solutions:true
  ```

### C5. Branding adjustments

All brand tokens live in two files:

1. `_brand.yml` — colors, fonts, logos.
2. `_extensions/ulm-academic/theme.scss` — reveal.js slide theme overrides.

To replace the placeholder Ulm logo with a real SMF logo:

1. Drop the SVG at `assets/logos/smf.svg`.
2. Update `_quarto.yml` (`navbar.logo`), `_brand.yml` (`logo:`), and the `lectures/_metadata.yml` (`logo:` under `revealjs:`).

### C6. Author rich slide content (tables, figures, diagrams, images, code) and tweak the theme

Quarto markdown for slides is the same syntax that drives the HTML notes and PDF handout. Anything below renders in all four output formats (revealjs slides, notes html, pdf handout, pptx) unless noted.

#### Tables

Use Markdown pipe tables — simple and portable:

```markdown
| Method   | When to use                  |
|----------|------------------------------|
| t-test   | Compare two means, normal    |
| Wilcoxon | Compare medians, non-normal  |
```

For tables with more layout (merged cells, multi-line content), drop into HTML tables; they still render in every format. Programmatic tables in R use `knitr::kable()` or `gt::gt()` inside an executed `{r}` chunk.

#### Figures and images

Drop the file into the lecture's `images/` folder, then reference inline:

```markdown
![Identification strategy schematic](images/iv-diagram.png){width=70% fig-align="center"}
```

Knobs:

- `width=` accepts `%`, `px`, or `em` (e.g. `width=480px`).
- `fig-align=` is `"center"`, `"left"`, or `"right"`.
- For full-bleed images on a slide, set `width=100%` and put the image alone on its own slide.
- SVGs are preferred for diagrams (sharp at any zoom); PNG/JPG for screenshots and photos.

#### Diagrams (Mermaid, Graphviz)

Quarto renders [Mermaid](https://mermaid.js.org/) and Graphviz natively — no extra install:

````markdown
```{mermaid}
flowchart LR
  Data --> Cleansing --> Analysis --> Write-up
  Analysis --> Tables
  Analysis --> Figures
```
````

````markdown
```{dot}
//| label: fig-causal
digraph {
  rankdir=LR;
  X -> Y; Z -> X; Z -> Y;
}
```
````

For more elaborate plots/charts, generate them inside an executed `{r}` or `{python}` chunk and let the figure embed automatically.

#### Code blocks (highlighted, executed, or both)

Language-tagged fences for **highlighting only** (no execution):

````markdown
```r
library(tidyverse)
mtcars |> filter(mpg > 25)
```
````

Wrap the language in braces `{r}` / `{python}` to **execute** the chunk and embed its output:

````markdown
```{r}
#| echo: true
#| fig-cap: "MPG distribution"
library(ggplot2)
ggplot(mtcars, aes(mpg)) + geom_histogram(bins = 20)
```
````

`#|` lines configure the chunk: `echo` (show code), `eval` (run it), `fig-cap`, `fig-width`, etc. See <https://quarto.org/docs/computations/execution-options.html>.

#### Two-column layouts

```markdown
::: {.columns}
::: {.column width="55%"}
Left side: explanation text, equations, narrative.
:::
::: {.column width="45%"}
![Right side: figure](images/diagram.png){width=100%}
:::
:::
```

#### Callouts

```markdown
::: {.callout-note title="Learning objective"}
By the end of this slide you can …
:::
```

Top-level callouts on a slide are pinned to a fixed bottom band by the SMF theme. Available variants: `callout-note`, `callout-tip`, `callout-warning`, `callout-important`, `callout-caution` (all rendered in the same monochrome style).

#### Speaker notes

```markdown
::: notes
What you say while presenting; never shown on the slide. Press **S** in
revealjs for the speaker view.
:::
```

#### Incremental reveal

```markdown
::: incremental
- First bullet appears on click
- Then this one
- Then this one
:::
```

#### Math

Inline `$E[r_i] = \beta_i \cdot \lambda$`, display:

```markdown
$$
\hat{\beta} = (X'X)^{-1} X'y
$$
```

Quarto compiles math via MathJax in HTML / revealjs and natively in PDF.

#### Tweaking the theme

| Where | What it controls |
|---|---|
| `_extensions/ulm-academic/theme.scss` | reveal.js slide theme (slide background, headings, callouts, tables, code) |
| `assets/styles/html.scss` | HTML website pages (course homepage, syllabus, notes view) |
| `_brand.yml` | brand colour palette and font tokens (read by Quarto's brand layer) |
| `assets/styles/pptx-reference.pptx` | PowerPoint export — regenerate with `python scripts/build-pptx-reference.py` |
| `courses/<id>/lectures/_metadata.yml` | per-format options: footer text, slide size, transitions, slide-level |

After SCSS edits, `quarto preview` hot-reloads. For a big colour change, edit the palette tokens at the top of `theme.scss` and `html.scss` together so slides and website match.

The full Quarto reveal.js reference: <https://quarto.org/docs/presentations/revealjs/>. For inline-execution computations: <https://quarto.org/docs/computations/>.

---

## D. Repository conventions

- **One folder per course, ever.** `courses/<course-id>/` lives forever. Never copy it into `courses/<course-id>-summer-2026/`. Use git tags (C2) for historical snapshots.
- **`schedule.yml` is the only file you edit on a semester roll-over.** All other content is stable.
- **Lecture folders** are `lecture-NN-<slug>/` (zero-padded NN, kebab-case slug).
- **Required front-matter** for `slides.qmd`: `title`, `subtitle`, `topics`. **No** `date`, `week`, or `authors` — those come from the cascade.
- **Listings auto-update.** The course homepage and syllabus timetable are Quarto listings reading lecture metadata. Do **not** hand-edit them.
- **Auto-generated files** (gitignored): `courses/*/lectures/lecture-*/_metadata.yml`. Hand-edited at course level: `courses/<id>/_metadata.yml` (which has a managed block at the bottom — leave it alone).
- **Solutions default to `false`.** Never flip to `true` in committed files.
- **No emojis** in lecture content unless explicitly asked.
- **LaTeX math:** `$…$` (inline), `$$…$$` (display).

---

## E. Reference: AI-assisted workflows

The repo is designed for prompt-driven editing in Cursor, Continue.dev, or Claude Code. Conventions for AI assistants live in [`CLAUDE.md`](CLAUDE.md). The five canonical workflows:

| | Trigger phrase |
|---|---|
| **A. Create a new lecture** | *"Create Lecture NN for the `<course-id>` course titled '…'. Topics: …"* |
| **B. Update existing content** | *"Add a section on '…' to Lecture 03 slides."* / *"Replace question 2 of …"* |
| **C. Convert a PDF lecture** | *"Convert this PDF (`inputs/…`) into Lecture NN of `<course-id>`. Title: '…'."* |
| **D. Regenerate the Moodle checklist** | *"Regenerate the Moodle setup file for `<course-id>` for the `<term>` term."* |
| **E. Scaffold a new course** | *"Scaffold a new course called `<id>` titled '…', instructor '…', term '…'."* |

The AI reads `CLAUDE.md` and acts deterministically.

---

## Daily workflow

```bash
git pull
quarto preview                  # live preview at localhost:4200
# … edit content (manually or via AI prompt) …
git add . && git commit -m "Lecture 04: refine identification slide"
git push                        # CI renders + deploys to GH Pages (~3 min)
```

---

## Troubleshooting

- **Preview doesn't refresh** — kill `quarto preview` and re-run.
- **PDF render fails** — install TinyTeX once: `quarto install tinytex`.
- **Listings table empty** — the lecture folder needs `slides.qmd` with `title:` and an entry in `schedule.yml`.
- **Theme looks wrong** — check `theme:` in `courses/<id>/lectures/_metadata.yml` references the extension correctly.
- **`{{< meta key >}}` shows up literally** in the rendered output — usually means `apply-schedule.py` didn't run (the pre-render hook is wired in `_quarto.yml`); run it manually with `python scripts/apply-schedule.py` and re-render.
- **`ImportError: yaml`** — `pip install pyyaml`.

---

## License

Source files: see `LICENSE` (to be added). Course content: © Institute of Strategic Management and Finance, Ulm University.

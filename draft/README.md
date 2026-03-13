# Manuscript Drafts

## Folder structure

| Folder | Purpose |
|---|---|
| `local/` | **Working copy** — edit here, compile here, commit via git. |
| `overleaf/` | **Read-only Overleaf mirror** — download from Overleaf and drop files here. Do not edit directly. |
| `archive/` | Older dated drafts kept for reference. |

---

## Daily workflow

### 1. Pull latest from Overleaf

Always start here to make sure you're diffing against the current Overleaf state.

**Option A — manual download (simplest):**

1. Open the Overleaf project in a browser.
2. **Menu → Download → Source** → save the zip.
3. Unzip and copy the changed files into `draft/overleaf/`:
   ```bash
   cp /path/to/download/main.tex draft/overleaf/main.tex
   cp /path/to/download/references.bib draft/overleaf/references.bib   # if changed
   ```

**Option B — Overleaf git bridge:**

The `overleaf` remote is already configured for this project.

```bash
# Pull latest Overleaf commits into draft/overleaf/
git subtree pull --prefix=draft/overleaf overleaf master --squash
```

---

### 2. Compile local draft

Run from the repo root (or `cd draft/local` first):

```bash
cd draft/local
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex    # second pass resolves cross-references
open main.pdf
```

Auxiliary files (`main.aux`, `main.bbl`, `main.log`, `main.out`, `main.spl`) are gitignored — only `main.tex`, `main.pdf`, and `.bst`/`.bib`/`.sty` support files are tracked.

---

### 3. Compare local draft to Overleaf version (latexdiff)

**Prerequisites:** `latexdiff` ships with most TeX distributions.
Check with `which latexdiff`; install via `brew install latexdiff` if missing.

#### 3a. Generate the diff

Run from the repo root:

```bash
latexdiff draft/overleaf/main.tex draft/local/main.tex > draft/local/main_diff.tex
```

#### 3b. Compile the diff PDF

```bash
cd draft/local
pdflatex main_diff.tex
bibtex main_diff
pdflatex main_diff.tex
pdflatex main_diff.tex
open main_diff.pdf
```

The diff PDF highlights **additions in blue** and **deletions in red**. Review it before pushing changes back to Overleaf.

> **Tip:** if the diff fails to compile (common with complex macros), try the `--flatten` flag to inline `\input`/`\include` files first:
> ```bash
> latexdiff --flatten draft/overleaf/main.tex draft/local/main.tex > draft/local/main_diff.tex
> ```

---

### 4. Push reviewed changes to Overleaf

After reviewing the diff and confirming the local version is ready:

**Option A — manual upload (simplest):**

1. Open the Overleaf project in a browser.
2. Click **Upload** (top-left file tree) → upload `draft/local/main.tex`.
3. Upload any updated `.bib` file if references changed.
4. Compile on Overleaf to confirm it builds cleanly.

**Option B — Overleaf git bridge:**

```bash
# Push local changes from draft/local/
git subtree push --prefix=draft/local overleaf master
```

---

## Commit convention

```
git add draft/local/main.tex draft/local/references.bib
git commit -m "draft: <brief description of changes>"
```

Keep `main_diff.tex` and compiled aux files out of commits (they are gitignored).

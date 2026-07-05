# Manuscript Drafts

The manuscript is written and edited **directly on Overleaf**. This folder keeps a
local, read-only mirror of the Overleaf project so you can read, grep, and diff the
current source alongside the code and figures.

## Folder structure

| Folder | Purpose |
|---|---|
| `overleaf/` | **Read-only mirror of the Overleaf project.** Refreshed by pulling from the `overleaf` git remote. Do not edit here — edits go on Overleaf. |
| `archive/` | Older dated drafts kept for reference. |

The `overleaf/` mirror is gitignored (manuscript files are tracked on Overleaf, not in
this repo), so refreshing it never shows up as a change in `git status`.

---

## Pull the latest from Overleaf

The `overleaf` git remote is already configured for this project.

```bash
# from the repo root
git fetch overleaf master
git archive overleaf/master | tar -x -C draft/overleaf/
```

This unpacks the exact current Overleaf snapshot into `draft/overleaf/`. It touches only
that folder — it does **not** merge into the `main` code branch and does not push anything.

**Verify it matches the remote (optional):**

```bash
diff <(git show overleaf/master:main.tex) draft/overleaf/main.tex && echo "in sync"
```

**Alternatives:**

- *Manual download:* Overleaf **Menu → Download → Source**, unzip, and copy the files into
  `draft/overleaf/`.
- *Subtree:* `git subtree pull --prefix=draft/overleaf overleaf master --squash`.

---

## Edit the manuscript

Edit on Overleaf in the browser. When you want the changes reflected locally (for reading,
searching, or comparing against the code/figures), re-run the pull above.

---

## Compare against an older version (latexdiff)

To see what changed between an archived draft and the current Overleaf source:

```bash
latexdiff draft/archive/<older_main>.tex draft/overleaf/main.tex > /tmp/main_diff.tex
```

Compile `/tmp/main_diff.tex` to get a PDF with additions in blue and deletions in red.
If it fails on complex macros, add `--flatten` to inline `\input`/`\include` files first.
`latexdiff` ships with most TeX distributions (`brew install latexdiff` if missing).

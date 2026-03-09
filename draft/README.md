# Manuscript Drafts

## Folder structure

| Folder | Purpose |
|---|---|
| `overleaf/` | **Read-only mirror** of the current Overleaf project. Copy files from Overleaf here to keep a local snapshot. Do not edit directly. |
| `local/` | **Working copy** for local edits. Push changes via git. Periodically diff against `overleaf/` to reconcile. |
| `archive/` | Older dated drafts kept for reference. |

## Workflow

1. **Download** the latest `.tex` / `.bib` from Overleaf → replace files in `overleaf/`.
2. **Diff** `overleaf/` vs `local/` to see what changed:
   ```bash
   diff draft/overleaf/main.tex draft/local/main.tex
   ```
3. **Merge** Overleaf changes into `local/` as needed.
4. **Edit** in `local/` and commit + push via git.
5. **Upload** `local/main.tex` back to Overleaf when ready to share.

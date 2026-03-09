"""
sync_bib.py
===========
Export the Zotero group library (5747618 / berm-review) to BibTeX and
write it to draft/local/local.bib, keeping the LaTeX draft in sync with
the canonical Zotero collection.

Usage:
    python zotero/scripts/sync_bib.py          # default → draft/local/local.bib
    python zotero/scripts/sync_bib.py --dry-run  # print stats without writing
"""

import argparse
from pathlib import Path
from zotero_client import ZoteroClient


def main():
    parser = argparse.ArgumentParser(description="Sync Zotero group library → local.bib")
    parser.add_argument("--out", type=str, default=None,
                        help="Output .bib path (default: draft/local/local.bib)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print stats without writing the file")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent
    out_path = Path(args.out) if args.out else project_root / "draft" / "local" / "local.bib"

    zot = ZoteroClient()
    print(f"Exporting BibTeX from group {zot.group_id} …")

    bib_text = zot.group_bibtex()

    # Count entries
    n_entries = bib_text.count("\n@")
    if not bib_text.startswith("\n") and bib_text.startswith("@"):
        n_entries += 1
    print(f"  {n_entries} BibTeX entries retrieved")

    if args.dry_run:
        print("  (dry run — file not written)")
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(bib_text, encoding="utf-8")
    print(f"  Written to {out_path}")


if __name__ == "__main__":
    main()

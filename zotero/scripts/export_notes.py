"""
export_notes.py
===============
Export notes, tags, and metadata from the Zotero group library to
CSV and JSON files in zotero/exports/.

Usage:
    python zotero/scripts/export_notes.py
"""

import csv
import json
from pathlib import Path
from zotero_client import ZoteroClient


def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    export_dir = project_root / "zotero" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    zot = ZoteroClient()
    print(f"Fetching items from group {zot.group_id} …")
    items = zot.group_items_top()
    print(f"  {len(items)} top-level items")

    # ── Export metadata CSV ───────────────────────────────────────────────────
    csv_path = export_dir / "zotero_items.csv"
    fieldnames = [
        "key", "itemType", "title", "creators", "date",
        "publicationTitle", "DOI", "url", "tags", "abstractNote",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for it in items:
            d = it["data"]
            row = {
                "key": d.get("key", ""),
                "itemType": d.get("itemType", ""),
                "title": d.get("title", ""),
                "creators": "; ".join(
                    f"{c.get('lastName', '')}, {c.get('firstName', '')}"
                    for c in d.get("creators", [])
                ),
                "date": d.get("date", ""),
                "publicationTitle": d.get("publicationTitle", ""),
                "DOI": d.get("DOI", ""),
                "url": d.get("url", ""),
                "tags": "; ".join(t.get("tag", "") for t in d.get("tags", [])),
                "abstractNote": d.get("abstractNote", ""),
            }
            writer.writerow(row)
    print(f"  Metadata → {csv_path}")

    # ── Export child notes ────────────────────────────────────────────────────
    all_children = zot.group_items_all()
    notes = [
        it for it in all_children
        if it["data"].get("itemType") == "note"
    ]
    notes_path = export_dir / "zotero_notes.csv"
    with open(notes_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["parentItem", "key", "note"])
        writer.writeheader()
        for n in notes:
            writer.writerow({
                "parentItem": n["data"].get("parentItem", ""),
                "key": n["data"].get("key", ""),
                "note": n["data"].get("note", ""),
            })
    print(f"  Notes ({len(notes)}) → {notes_path}")

    # ── Export full JSON ──────────────────────────────────────────────────────
    json_path = export_dir / "zotero_library.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([it["data"] for it in items], f, indent=2, ensure_ascii=False)
    print(f"  Full JSON → {json_path}")


if __name__ == "__main__":
    main()

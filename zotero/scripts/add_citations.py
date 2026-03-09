"""
add_citations.py
================
Add new references to the Zotero group library (berm-review) via the REST API.

References are defined as dicts with standard Zotero item fields.
Run this script to push new citations found during writing.

Usage:
    python zotero/scripts/add_citations.py

Edit the NEW_ITEMS list at the bottom of this file to add references.
"""

import json
from zotero_client import ZoteroClient


def add_items(items: list[dict]):
    """Push a list of Zotero item dicts to the group library."""
    zot = ZoteroClient()
    print(f"Adding {len(items)} item(s) to group {zot.group_id} …")
    result = zot.add_to_group(items)

    success = result.get("success", {})
    failed = result.get("failed", {})
    unchanged = result.get("unchanged", {})

    print(f"  Success: {len(success)}, Failed: {len(failed)}, Unchanged: {len(unchanged)}")
    if failed:
        for idx, err in failed.items():
            print(f"  FAILED [{idx}]: {err.get('message', err)}")
    return result


# ── Example: add new references here ─────────────────────────────────────────
# Each dict must include 'itemType' at minimum. See:
# https://www.zotero.org/support/dev/web_api/v3/types_and_fields

NEW_ITEMS = [
    # Example (uncomment and edit):
    # {
    #     "itemType": "journalArticle",
    #     "title": "Example paper title",
    #     "creators": [
    #         {"creatorType": "author", "firstName": "Jane", "lastName": "Doe"},
    #         {"creatorType": "author", "firstName": "John", "lastName": "Smith"},
    #     ],
    #     "publicationTitle": "Journal of Examples",
    #     "volume": "42",
    #     "pages": "1-15",
    #     "date": "2025",
    #     "DOI": "10.1234/example.2025",
    # },
]


if __name__ == "__main__":
    if not NEW_ITEMS:
        print("No items to add. Edit NEW_ITEMS in this script first.")
    else:
        add_items(NEW_ITEMS)

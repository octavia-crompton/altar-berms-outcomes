"""
move_to_group.py
================
Move items from your personal Zotero library to the berm-review group library.

Searches your personal library by title (substring match) and copies
matching items to the group. Does NOT delete from personal library
(add --delete-personal to remove after copying).

Usage:
    python zotero/scripts/move_to_group.py "keyword in title"
    python zotero/scripts/move_to_group.py "keyword" --delete-personal
"""

import argparse
import json
from zotero_client import ZoteroClient


def main():
    parser = argparse.ArgumentParser(
        description="Copy items from personal library to group library"
    )
    parser.add_argument("query", help="Substring to match in item titles")
    parser.add_argument("--delete-personal", action="store_true",
                        help="Delete matching items from personal library after copying")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print matches without making changes")
    args = parser.parse_args()

    zot = ZoteroClient()
    query_lower = args.query.lower()

    # Fetch personal library items
    print(f"Searching personal library for '{args.query}' …")
    personal_items = zot.user_items_top(q=args.query)
    matches = [
        it for it in personal_items
        if query_lower in it["data"].get("title", "").lower()
    ]
    print(f"  Found {len(matches)} matching item(s)")

    if not matches:
        return

    for it in matches:
        print(f"  • {it['data'].get('title', '(no title)')[:80]}")

    if args.dry_run:
        print("  (dry run — no changes made)")
        return

    # Prepare items for group library (strip keys/version that belong to personal lib)
    group_items = []
    for it in matches:
        d = it["data"].copy()
        d.pop("key", None)
        d.pop("version", None)
        group_items.append(d)

    print(f"\nAdding {len(group_items)} item(s) to group {zot.group_id} …")
    result = zot.add_to_group(group_items)
    success = result.get("success", {})
    failed = result.get("failed", {})
    print(f"  Success: {len(success)}, Failed: {len(failed)}")

    if args.delete_personal and success:
        print(f"\nDeleting {len(matches)} item(s) from personal library …")
        for it in matches:
            key = it["key"]
            version = it["version"]
            url = f"{zot._user_url()}/items/{key}"
            r = zot._session.delete(url, headers={"If-Unmodified-Since-Version": str(version)})
            if r.ok:
                print(f"  Deleted {key}")
            else:
                print(f"  Failed to delete {key}: {r.status_code}")


if __name__ == "__main__":
    main()

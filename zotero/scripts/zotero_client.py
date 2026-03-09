"""
zotero_client.py
================
Shared Zotero REST API client for the Altar Valley berm project.

Reads credentials from the project .env file and provides thin wrappers
around the Zotero v3 REST API for both personal and group library access.

Usage:
    from zotero_client import ZoteroClient
    zot = ZoteroClient()              # reads .env automatically
    items = zot.group_items_top()     # top-level items from the group library
"""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from project root ──────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

API_BASE = "https://api.zotero.org"


class ZoteroClient:
    """Lightweight wrapper around the Zotero REST API v3."""

    def __init__(self, api_key=None, group_id=None, user_id=None):
        self.api_key = api_key or os.environ["ZOTERO_API_KEY"]
        self.group_id = group_id or os.environ["ZOTERO_GROUP_ID"]
        self.user_id = user_id or os.environ.get("ZOTERO_USER_ID", "")
        self._session = requests.Session()
        self._session.headers.update({
            "Zotero-API-Key": self.api_key,
            "Zotero-API-Version": "3",
            "Content-Type": "application/json",
        })

    # ── low-level helpers ─────────────────────────────────────────────────────

    def _get(self, url, params=None):
        """GET with automatic pagination."""
        params = params or {}
        params.setdefault("limit", 100)
        params.setdefault("format", "json")
        all_items = []
        while True:
            r = self._session.get(url, params=params)
            r.raise_for_status()
            batch = r.json()
            all_items.extend(batch)
            # Follow next link if paginated
            links = r.headers.get("Link", "")
            if 'rel="next"' in links:
                # Parse next URL
                for part in links.split(","):
                    if 'rel="next"' in part:
                        url = part.split("<")[1].split(">")[0]
                        params = {}  # URL already has params
                        break
            else:
                break
        return all_items

    def _post(self, url, payload):
        """POST a list of items."""
        r = self._session.post(url, data=json.dumps(payload))
        r.raise_for_status()
        return r.json()

    # ── group library ─────────────────────────────────────────────────────────

    def _group_url(self, path=""):
        return f"{API_BASE}/groups/{self.group_id}{path}"

    def group_items_top(self, **params):
        """Fetch all top-level items (no child attachments/notes)."""
        return self._get(self._group_url("/items/top"), params)

    def group_items_all(self, **params):
        """Fetch all items including children."""
        return self._get(self._group_url("/items"), params)

    def group_collections(self, **params):
        """Fetch all collections in the group library."""
        return self._get(self._group_url("/collections"), params)

    def group_item_count(self):
        """Return total top-level item count."""
        return len(self.group_items_top())

    def add_to_group(self, items):
        """Add a list of item dicts to the group library.

        Each item should be a dict with at least 'itemType' and 'title'.
        See https://www.zotero.org/support/dev/web_api/v3/write_requests
        """
        return self._post(self._group_url("/items"), items)

    # ── personal library ──────────────────────────────────────────────────────

    def _user_url(self, path=""):
        return f"{API_BASE}/users/{self.user_id}{path}"

    def user_items_top(self, **params):
        """Fetch all top-level items from the personal library."""
        return self._get(self._user_url("/items/top"), params)

    def user_collections(self, **params):
        """Fetch all collections in the personal library."""
        return self._get(self._user_url("/collections"), params)

    # ── BibTeX export ─────────────────────────────────────────────────────────

    def group_bibtex(self):
        """Export the entire group library as a BibTeX string."""
        url = self._group_url("/items/top")
        r = self._session.get(url, params={"format": "bibtex", "limit": 100})
        r.raise_for_status()
        parts = [r.text]
        # Handle pagination
        while 'rel="next"' in r.headers.get("Link", ""):
            for part in r.headers["Link"].split(","):
                if 'rel="next"' in part:
                    next_url = part.split("<")[1].split(">")[0]
                    break
            r = self._session.get(next_url)
            r.raise_for_status()
            parts.append(r.text)
        return "\n".join(parts)

    # ── convenience ───────────────────────────────────────────────────────────

    def summary(self):
        """Print a quick summary of the group library."""
        items = self.group_items_top()
        types = {}
        for it in items:
            t = it["data"].get("itemType", "unknown")
            types[t] = types.get(t, 0) + 1
        print(f"Group {self.group_id}: {len(items)} top-level items")
        for t, n in sorted(types.items(), key=lambda x: -x[1]):
            print(f"  {t}: {n}")
        return items

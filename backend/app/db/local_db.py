from __future__ import annotations

"""
Local JSON file-based database — replaces Azure CosmosDB.
Stores data in a local 'data/' directory as JSON files.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

_stores: dict = {}


def _get_store_path(container_name: str) -> Path:
    if container_name not in _stores:
        path = DATA_DIR / f"{container_name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("[]", encoding="utf-8")
        _stores[container_name] = path
    return _stores[container_name]


def _load(container_name: str) -> List[dict]:
    path = _get_store_path(container_name)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save(container_name: str, items: List[dict]) -> None:
    path = _get_store_path(container_name)
    path.write_text(json.dumps(items, indent=2, default=str), encoding="utf-8")


def upsert_item(container_name: str, item: dict) -> dict:
    items = _load(container_name)
    item_id = item.get("id")
    for i, existing in enumerate(items):
        if existing.get("id") == item_id:
            items[i] = item
            _save(container_name, items)
            return item
    items.append(item)
    _save(container_name, items)
    return item


def read_item(container_name: str, item_id: str, partition_key: str = None) -> Optional[dict]:
    items = _load(container_name)
    for item in items:
        if item.get("id") == item_id:
            return item
    return None


def query_items(container_name: str, query: str, parameters: Optional[list] = None) -> list:
    """
    Simple query support. Handles the common patterns used in this project:
    - SELECT * FROM c  (return all)
    - SELECT * FROM c WHERE c.field = @value
    """
    items = _load(container_name)

    if parameters:
        param_map = {p["name"]: p["value"] for p in parameters}
        # Parse simple WHERE clauses like "c.cv_id = @cv_id"
        if "WHERE" in query.upper():
            filtered = items
            for name, value in param_map.items():
                field = name.lstrip("@")
                filtered = [item for item in filtered if item.get(field) == value]
            return filtered

    return items


def delete_item(container_name: str, item_id: str, partition_key: str = None) -> None:
    items = _load(container_name)
    items = [item for item in items if item.get("id") != item_id]
    _save(container_name, items)

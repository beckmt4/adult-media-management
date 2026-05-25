#!/usr/bin/env python3
import argparse
import csv
import os
from typing import Any

from stash_inbox_organizer import DEFAULT_API_KEY, DEFAULT_STASH_URL, gql
from stash_manual_review import DEFAULT_CSV, FIND_TAG


FIND_STUDIO = """
query FindStudio($name: String!) {
  findStudios(studio_filter:{name:{value:$name, modifier:EQUALS}}, filter:{per_page:10}) {
    studios { id name }
  }
}
"""

STUDIO_CREATE = """
mutation StudioCreate($input: StudioCreateInput!) {
  studioCreate(input:$input) { id name }
}
"""

SCENE_UPDATE = """
mutation SceneUpdate($input: SceneUpdateInput!) {
  sceneUpdate(input:$input) {
    id
    title
    date
    code
    studio { id name }
  }
}
"""

BULK_SCENE_UPDATE = """
mutation BulkSceneUpdate($input: BulkSceneUpdateInput!) {
  bulkSceneUpdate(input:$input) { id }
}
"""


def find_tag(url: str, api_key: str, tag_name: str) -> str:
    data = gql(url, api_key, FIND_TAG, {"name": tag_name})
    tags = data["findTags"]["tags"]
    if not tags:
        return ""
    return tags[0]["id"]


def ensure_studio(url: str, api_key: str, studio_name: str) -> str:
    data = gql(url, api_key, FIND_STUDIO, {"name": studio_name})
    studios = data["findStudios"]["studios"]
    if studios:
        return studios[0]["id"]
    created = gql(url, api_key, STUDIO_CREATE, {"input": {"name": studio_name}})
    return created["studioCreate"]["id"]


def read_rows(csv_path: str) -> list[dict[str, str]]:
    with open(csv_path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def normalize(value: str) -> str:
    return (value or "").strip()


def build_scene_input(
    url: str,
    api_key: str,
    row: dict[str, str],
) -> dict[str, Any] | None:
    title = normalize(row.get("reviewed_title", ""))
    date = normalize(row.get("reviewed_date", ""))
    studio_name = normalize(row.get("reviewed_studio", ""))
    code = normalize(row.get("reviewed_code", ""))

    if not title or not date:
        return None

    scene_input: dict[str, Any] = {
        "id": row["scene_id"],
        "title": title,
        "date": date,
    }
    if code:
        scene_input["code"] = code
    if studio_name:
        scene_input["studio_id"] = ensure_studio(url, api_key, studio_name)
    return scene_input


def clear_review_tags(url: str, api_key: str, scene_ids: list[str], tag_ids: list[str]) -> None:
    if not scene_ids or not tag_ids:
        return
    gql(
        url,
        api_key,
        BULK_SCENE_UPDATE,
        {
            "input": {
                "ids": scene_ids,
                "tag_ids": {"ids": tag_ids, "mode": "REMOVE"},
            }
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply reviewed manual metadata back into Stash scenes.")
    parser.add_argument("--url", default=DEFAULT_STASH_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--apply", action="store_true", help="Write changes to Stash. Default is dry-run.")
    parser.add_argument(
        "--status-value",
        default="ready",
        help="Only rows with this status are applied. Default: ready",
    )
    args = parser.parse_args()

    rows = read_rows(args.csv)
    candidates: list[tuple[dict[str, str], dict[str, Any]]] = []
    skipped = 0
    for row in rows:
        if normalize(row.get("status", "")).lower() != args.status_value.lower():
            skipped += 1
            continue
        scene_input = build_scene_input(args.url, args.api_key, row)
        if not scene_input:
            skipped += 1
            continue
        candidates.append((row, scene_input))

    print(f"Found {len(candidates)} reviewed rows ready to apply.")
    print(f"Skipped {skipped} rows.")
    for row, scene_input in candidates[:20]:
        print(f"{row['scene_id']} -> {scene_input.get('title')} ({scene_input.get('date')})")

    if not args.apply:
        print("Dry run only. Mark rows with status=ready and re-run with --apply to update Stash.")
        return 0

    manual_review_tags = [
        "[Manual Review]",
        "[Manual Review: JAV]",
        "[Manual Review: No Date]",
        "[Manual Review: Multi-File]",
        "[Manual Review: No Title]",
    ]
    tag_ids = [tag_id for tag_id in (find_tag(args.url, args.api_key, name) for name in manual_review_tags) if tag_id]

    applied_ids: list[str] = []
    failures = 0
    for row, scene_input in candidates:
        try:
            gql(args.url, args.api_key, SCENE_UPDATE, {"input": scene_input})
            applied_ids.append(row["scene_id"])
        except Exception as exc:
            failures += 1
            print(f"error update {row['scene_id']}: {exc}")

    clear_review_tags(args.url, args.api_key, applied_ids, tag_ids)
    print(f"Applied {len(applied_ids)} scene metadata updates.")
    print(f"Failed {failures} scene metadata updates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

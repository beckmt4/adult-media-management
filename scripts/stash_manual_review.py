#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
from typing import Any

from stash_inbox_organizer import (
    DEFAULT_API_KEY,
    DEFAULT_DUPLICATE_STATE,
    DEFAULT_STASH_URL,
    SCENE_QUERY,
    collect_candidates,
    gql,
    infer_date,
    infer_studio_and_title,
    load_state,
)


DEFAULT_TAG_NAME = "[Manual Review]"
DEFAULT_JAV_TAG = "[Manual Review: JAV]"
DEFAULT_NO_DATE_TAG = "[Manual Review: No Date]"
DEFAULT_MULTI_FILE_TAG = "[Manual Review: Multi-File]"
DEFAULT_NO_TITLE_TAG = "[Manual Review: No Title]"
DEFAULT_CSV = "scripts/stash_manual_review.csv"
DEFAULT_JSON = "scripts/stash_manual_review.json"
JAV_CODE_RE = re.compile(r"\b([A-Z]{2,6})[-_]?(\d{2,5})\b", re.I)

FIND_TAG = """
query FindTag($name: String!) {
  findTags(tag_filter:{name:{value:$name, modifier:EQUALS}}, filter:{per_page:10}) {
    tags { id name }
  }
}
"""

TAG_CREATE = """
mutation TagCreate($input: TagCreateInput!) {
  tagCreate(input:$input) { id name }
}
"""

BULK_SCENE_UPDATE = """
mutation BulkSceneUpdate($input: BulkSceneUpdateInput!) {
  bulkSceneUpdate(input:$input) { id }
}
"""

SCENE_UPDATE = """
mutation SceneUpdate($input: SceneUpdateInput!) {
  sceneUpdate(input:$input) { id code }
}
"""


def ensure_tag(url: str, api_key: str, tag_name: str) -> str:
    data = gql(url, api_key, FIND_TAG, {"name": tag_name})
    tags = data["findTags"]["tags"]
    if tags:
        return tags[0]["id"]
    created = gql(
        url,
        api_key,
        TAG_CREATE,
        {"input": {"name": tag_name, "description": "Inbox scenes requiring manual metadata review"}},
    )
    return created["tagCreate"]["id"]


def detect_jav_code(path: str) -> str:
    match = JAV_CODE_RE.search(path.upper())
    if not match:
        return ""
    return f"{match.group(1).upper()}-{match.group(2)}"


def unresolved_reason(scene: dict[str, Any], resolved_duplicates: dict[str, Any]) -> str:
    if scene["id"] in resolved_duplicates:
        return "resolved duplicate"
    files = scene.get("files") or []
    if len(files) != 1:
        return "multi-file or already-linked duplicate"
    path = files[0]["path"]
    jav_code = detect_jav_code(path)
    guessed_date = infer_date(path)
    guessed_studio, guessed_title = infer_studio_and_title(path)
    if not guessed_date:
        if jav_code:
            return "jav code / metadata lookup"
        return "no parseable date"
    if not guessed_title:
        return "no parseable title"
    if "megapack" in path.lower():
        return "megapack item"
    if ".jav." in path.lower() or "jav" in os.path.basename(path).lower():
        return "jav code / metadata needed"
    if "yurievij" in path.lower():
        return "date-prefix release / metadata needed"
    if not guessed_studio:
        return "no parseable studio"
    return "manual metadata review"


def export_rows(csv_path: str, json_path: str, rows: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "scene_id",
                "status",
                "action",
                "reason",
                "lookup_key",
                "path",
                "jav_code",
                "guessed_studio",
                "guessed_title",
                "guessed_date",
                "reviewed_studio",
                "reviewed_title",
                "reviewed_date",
                "reviewed_code",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Flag unresolved inbox scenes for manual review.")
    parser.add_argument("--url", default=DEFAULT_STASH_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--state-path", default=DEFAULT_DUPLICATE_STATE)
    parser.add_argument("--tag-name", default=DEFAULT_TAG_NAME)
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--json", default=DEFAULT_JSON)
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    state = load_state(args.state_path)
    data = gql(args.url, args.api_key, SCENE_QUERY, {"filter": {"per_page": args.limit}})
    candidates, _ = collect_candidates(
        data,
        scene_root="/data/scenes",
        movie_root="/data/movies",
        infer_from_filename=True,
        resolved_duplicates=state["resolved_duplicates"],
    )
    candidate_ids = {c.scene_id for c in candidates}

    review_rows: list[dict[str, Any]] = []
    review_ids: list[str] = []
    subgroup_ids: dict[str, list[str]] = {
        DEFAULT_JAV_TAG: [],
        DEFAULT_NO_DATE_TAG: [],
        DEFAULT_MULTI_FILE_TAG: [],
        DEFAULT_NO_TITLE_TAG: [],
    }
    code_updates = 0
    for scene in data["findScenes"]["scenes"]:
        if scene["id"] in candidate_ids or scene["id"] in state["resolved_duplicates"]:
            continue
        if not any(f["path"].startswith("/downloads/") for f in scene.get("files") or []):
            continue
        path = (scene.get("files") or [{}])[0].get("path", "")
        guessed_studio, guessed_title = infer_studio_and_title(path)
        guessed_date = infer_date(path)
        jav_code = detect_jav_code(path)
        reason = unresolved_reason(scene, state["resolved_duplicates"])
        review_rows.append(
            {
                "scene_id": scene["id"],
                "status": "pending",
                "action": "",
                "reason": reason,
                "lookup_key": jav_code or guessed_title or os.path.basename(path),
                "path": path,
                "jav_code": jav_code,
                "guessed_studio": guessed_studio,
                "guessed_title": guessed_title,
                "guessed_date": guessed_date,
                "reviewed_studio": guessed_studio,
                "reviewed_title": guessed_title,
                "reviewed_date": guessed_date,
                "reviewed_code": jav_code,
                "notes": "",
            }
        )
        review_ids.append(scene["id"])
        if reason == "jav code / metadata lookup":
            subgroup_ids[DEFAULT_JAV_TAG].append(scene["id"])
            subgroup_ids[DEFAULT_NO_DATE_TAG].append(scene["id"])
        elif reason == "no parseable date":
            subgroup_ids[DEFAULT_NO_DATE_TAG].append(scene["id"])
        elif reason == "no parseable title":
            subgroup_ids[DEFAULT_NO_TITLE_TAG].append(scene["id"])
        elif reason == "multi-file or already-linked duplicate":
            subgroup_ids[DEFAULT_MULTI_FILE_TAG].append(scene["id"])

        if jav_code and not scene.get("code"):
            gql(
                args.url,
                args.api_key,
                SCENE_UPDATE,
                {"input": {"id": scene["id"], "code": jav_code}},
            )
            code_updates += 1

    tag_id = ensure_tag(args.url, args.api_key, args.tag_name)
    if review_ids:
        gql(
            args.url,
            args.api_key,
            BULK_SCENE_UPDATE,
            {
                "input": {
                    "ids": review_ids,
                    "tag_ids": {"ids": [tag_id], "mode": "ADD"},
                }
            },
        )

    for subgroup_name, ids in subgroup_ids.items():
        if not ids:
            continue
        subgroup_tag_id = ensure_tag(args.url, args.api_key, subgroup_name)
        gql(
            args.url,
            args.api_key,
            BULK_SCENE_UPDATE,
            {
                "input": {
                    "ids": ids,
                    "tag_ids": {"ids": [subgroup_tag_id], "mode": "ADD"},
                }
            },
        )

    export_rows(args.csv, args.json, review_rows)
    print(f"Tagged {len(review_ids)} scenes with {args.tag_name}.")
    print(f"Updated code on {code_updates} scenes.")
    print(f"Wrote {args.csv}")
    print(f"Wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

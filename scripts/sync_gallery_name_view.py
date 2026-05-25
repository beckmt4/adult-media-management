#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from gallery_tools import (
    JsonLogger,
    StashClient,
    ensure_relative_symlink,
    fail_if_no_api_key,
    first_letter_bucket,
    parse_common_args,
    resolve_targets,
    safe_name,
)


def main() -> int:
    p = parse_common_args("Sync by-name performer gallery view as relative symlinks to canonical id folders.")
    p.add_argument("--delete-broken-links", action="store_true")
    args = p.parse_args()

    if not args.execute and not args.dry_run:
        args.dry_run = True
    execute = args.execute and not args.dry_run

    fail_if_no_api_key(args.stash_api_key)
    client = StashClient(args.stash_url, args.stash_api_key)

    root = Path(args.gallery_root)
    id_root = root / "id"
    by_name_root = root / "by-name"
    manifest_root = root / "manifest"
    logs_root = root / "logs"

    logger = JsonLogger(logs_root / "name_view_sync.log", dry_run=not execute)
    targets = resolve_targets(client, args.target_performer_id, args.target_performer_name, args.all)
    if not targets:
        raise SystemExit("No target performers resolved. Use --all or target args.")

    if execute:
        by_name_root.mkdir(parents=True, exist_ok=True)
        manifest_root.mkdir(parents=True, exist_ok=True)

    manifest_path = manifest_root / "name_view_links.jsonl"
    generated: list[dict] = []

    for t in targets:
        pid = str(t["id"])
        name = t["name"]
        canonical = id_root / pid
        safe = safe_name(name, pid)
        letter = first_letter_bucket(safe)
        link = by_name_root / letter / f"{safe} [{pid}]"

        rel = os.path.relpath(canonical, start=link.parent)
        if link.exists() or link.is_symlink():
            if link.is_symlink() and os.readlink(link) == rel:
                logger.emit("keep", "name_view_link_current", source=str(link), destination=rel, performer_id=pid, performer_name=name)
            else:
                logger.emit("replace", "name_view_link_update", source=str(link), destination=rel, performer_id=pid, performer_name=name)
                if execute:
                    if link.is_dir() and not link.is_symlink():
                        for pth in link.rglob("*"):
                            logger.emit("manual_review", "non_generated_dir_in_by_name", source=str(pth))
                        link.rmdir()
                    else:
                        link.unlink()
        else:
            logger.emit("create", "name_view_link_new", source=str(link), destination=rel, performer_id=pid, performer_name=name)

        ok = ensure_relative_symlink(link, canonical, logger, execute)
        if not ok:
            logger.emit(
                "manual_review",
                "name_view_symlink_permission_denied",
                source=str(link),
                destination=rel,
                performer_id=pid,
                performer_name=name,
            )

        generated.append({
            "performer_id": pid,
            "performer_name": name,
            "link_path": str(link.relative_to(root)),
            "target_path": rel,
            "generated_by": "sync_gallery_name_view.py",
            "last_seen_at": datetime.utcnow().isoformat() + "Z",
        })

    if args.delete_broken_links and by_name_root.exists():
        for p in by_name_root.rglob("*"):
            if p.is_symlink() and not p.exists():
                logger.emit("delete", "broken_symlink", source=str(p))
                if execute:
                    p.unlink()

    with manifest_path.open("w", encoding="utf-8") as fh:
        for row in generated:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote manifest: {manifest_path}")
    print(f"Wrote log: {logger.log_path}")
    print(f"Generated links: {len(generated)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

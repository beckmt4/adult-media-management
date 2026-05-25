#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from gallery_tools import (
    JsonLogger,
    StashClient,
    ensure_relative_symlink,
    fail_if_no_api_key,
    first_letter_bucket,
    is_image_asset,
    is_support_file,
    move_or_quarantine,
    parse_common_args,
    resolve_targets,
    safe_name,
)


def main() -> int:
    p = parse_common_args("Migrate performer gallery layout to canonical id/<performer_id> structure.")
    p.add_argument("--legacy-root", required=True)
    p.add_argument("--quarantine", action="store_true")
    p.add_argument("--delete-empty", action="store_true")
    p.add_argument("--delete-broken-links", action="store_true")
    p.add_argument("--delete-duplicates", action="store_true")
    args = p.parse_args()

    if not args.execute and not args.dry_run:
        args.dry_run = True
    execute = args.execute and not args.dry_run

    fail_if_no_api_key(args.stash_api_key)
    client = StashClient(args.stash_url, args.stash_api_key)

    root = Path(args.gallery_root)
    legacy = Path(args.legacy_root)
    id_root = root / "id"
    by_name_root = root / "by-name"
    manifest_root = root / "manifest"
    logs_root = root / "logs"
    quarantine_root = root / "quarantine" / datetime.now().strftime("%Y%m%d-%H%M%S")

    log_path = logs_root / "gallery_migration.log"
    logger = JsonLogger(log_path, dry_run=not execute)

    targets = resolve_targets(client, args.target_performer_id, args.target_performer_name, args.all)
    if not targets:
        raise SystemExit("No target performers resolved. Use --all or --target-performer-id/--target-performer-name")

    report: dict = {
        "summary": {"targets": len(targets), "moves": 0, "quarantined": 0, "deleted": 0, "manual_review": 0},
        "targets": [],
        "issues": [],
    }

    if execute:
        for d in (id_root, by_name_root, manifest_root, logs_root):
            d.mkdir(parents=True, exist_ok=True)

    for t in targets:
        pid = str(t["id"])
        pname = t["name"]
        safe = safe_name(pname, pid)
        letter = first_letter_bucket(safe)
        canonical = id_root / pid
        legacy_candidates = [
            legacy / pid,
            legacy / letter / safe,
            legacy / safe,
        ]

        target_report = {
            "performer_id": pid,
            "performer_name": pname,
            "canonical_dir": str(canonical),
            "legacy_candidates": [str(c) for c in legacy_candidates],
            "moved": [],
            "quarantined": [],
            "deleted": [],
            "issues": [],
        }

        if execute:
            canonical.mkdir(parents=True, exist_ok=True)

        for candidate in legacy_candidates:
            if not candidate.exists() or candidate.resolve() == canonical.resolve():
                continue
            if candidate.is_file():
                move_or_quarantine(
                    candidate,
                    canonical / candidate.name,
                    logger,
                    "migrate_legacy_file_to_id",
                    execute,
                    quarantine_root if args.quarantine else None,
                    allow_delete_duplicates=args.delete_duplicates,
                )
                report["summary"]["moves"] += 1
                target_report["moved"].append(str(candidate))
                continue

            for child in candidate.rglob("*"):
                if not child.is_file():
                    continue
                if not (is_image_asset(child) or is_support_file(child)):
                    target_report["issues"].append(f"unknown_file_type:{child}")
                    report["summary"]["manual_review"] += 1
                    if args.quarantine:
                        q = quarantine_root / pid / child.name
                        move_or_quarantine(child, q, logger, "unknown_file_quarantine", execute)
                        report["summary"]["quarantined"] += 1
                        target_report["quarantined"].append(str(child))
                    continue
                move_or_quarantine(
                    child,
                    canonical / child.name,
                    logger,
                    "migrate_name_folder_to_id_folder",
                    execute,
                    quarantine_root / pid if args.quarantine else None,
                    allow_delete_duplicates=args.delete_duplicates,
                )
                report["summary"]["moves"] += 1
                target_report["moved"].append(str(child))

            if args.delete_empty and candidate.exists():
                for d in sorted([x for x in candidate.rglob("*") if x.is_dir()], key=lambda x: len(x.parts), reverse=True):
                    if any(d.iterdir()):
                        continue
                    logger.emit("delete", "delete_empty_dir", source=str(d))
                    if execute:
                        d.rmdir()
                    report["summary"]["deleted"] += 1
                    target_report["deleted"].append(str(d))
                if candidate.exists() and candidate.is_dir() and not any(candidate.iterdir()):
                    logger.emit("delete", "delete_empty_dir", source=str(candidate))
                    if execute:
                        candidate.rmdir()
                    report["summary"]["deleted"] += 1
                    target_report["deleted"].append(str(candidate))

        link = by_name_root / letter / f"{safe} [{pid}]"
        ok = ensure_relative_symlink(link, canonical, logger, execute)
        if not ok:
            target_report["issues"].append("by_name_symlink_permission_denied")
            report["summary"]["manual_review"] += 1
        report["targets"].append(target_report)

    manifest = manifest_root / "migration_report.json"
    out_report = Path(args.report) if args.report else manifest
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote report: {out_report}")
    print(f"Wrote log: {log_path}")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

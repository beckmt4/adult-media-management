#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

from gallery_tools import StashClient, fail_if_no_api_key, first_letter_bucket, parse_common_args, resolve_targets, safe_name


def main() -> int:
    p = parse_common_args("Validate canonical performer gallery layout and by-name links.")
    args = p.parse_args()

    fail_if_no_api_key(args.stash_api_key)
    client = StashClient(args.stash_url, args.stash_api_key)
    targets = resolve_targets(client, args.target_performer_id, args.target_performer_name, args.all)
    if not targets:
        raise SystemExit("No target performers resolved.")

    root = Path(args.gallery_root)
    id_root = root / "id"
    by_name_root = root / "by-name"

    q_gallery = """
    query($code: String!) {
      findGalleries(gallery_filter:{code:{value:$code, modifier:EQUALS}}, filter:{per_page:10}) {
        galleries { id code image_count }
      }
    }
    """

    rows = []
    failed = 0
    for t in targets:
        pid = str(t["id"])
        name = t["name"]
        safe = safe_name(name, pid)
        letter = first_letter_bucket(safe)

        canonical = id_root / pid
        link = by_name_root / letter / f"{safe} [{pid}]"
        link_ok = link.is_symlink() and link.exists()
        link_target_ok = False
        if link.is_symlink():
            rel = os.readlink(link)
            tgt = (link.parent / rel).resolve()
            link_target_ok = tgt == canonical.resolve() and tgt.exists()

        file_count = 0
        if canonical.exists():
            file_count = sum(1 for p in canonical.rglob("*") if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"})

        code = f"actress-library-performer-{pid}"
        g = client._gql(q_gallery, {"code": code}).get("findGalleries", {}).get("galleries", [])
        gallery_id = g[0]["id"] if g else ""
        gallery_image_count = g[0]["image_count"] if g else 0

        issues = []
        if not canonical.exists():
            issues.append("canonical_missing")
        if not link_ok:
            issues.append("by_name_link_missing_or_broken")
        if not link_target_ok:
            issues.append("by_name_link_target_invalid")
        if file_count > 0 and gallery_image_count <= 0:
            issues.append("stash_gallery_missing_or_empty")

        if issues:
            failed += 1

        rows.append({
            "pass": len(issues) == 0,
            "performer_id": pid,
            "performer_name": name,
            "canonical_path": str(canonical),
            "canonical_path_exists": canonical.exists(),
            "canonical_file_count": file_count,
            "by_name_link": str(link),
            "by_name_link_exists": link_ok,
            "by_name_link_target_valid": link_target_ok,
            "stash_gallery_id": gallery_id,
            "stash_gallery_image_count": gallery_image_count,
            "issues": issues,
        })

    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Wrote report: {args.report}")

    print(json.dumps({"total": len(rows), "failed": failed, "passed": len(rows) - failed}, indent=2))
    for r in rows:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"{status} id={r['performer_id']} name={r['performer_name']} files={r['canonical_file_count']} gallery_images={r['stash_gallery_image_count']} issues={','.join(r['issues'])}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

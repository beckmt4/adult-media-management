#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_name(name: str, performer_id: str | int | None = None) -> str:
    text = (name or "").strip()
    text = re.sub(r'[<>:"/\\|?*]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip(' .')
    if not text:
        if performer_id is None:
            return "Unknown Performer"
        return f"Unknown Performer [{performer_id}]"
    return text


def first_letter_bucket(name: str) -> str:
    if not name:
        return "#"
    ch = name[0].upper()
    return ch if ch.isalpha() else "#"


@dataclass
class StashClient:
    url: str
    api_key: str
    timeout: int = 60

    def _gql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {"query": query, "variables": variables or {}}
        headers: dict[str, str] = {
            "ApiKey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Request failed: {exc}") from exc
        if data.get("errors"):
            raise RuntimeError(f"GraphQL errors: {data['errors']}")
        return data.get("data", {})

    def find_performer(self, performer_id: str) -> dict[str, Any] | None:
        q = """
        query FindPerformer($id: ID!) {
          findPerformer(id: $id) {
            id
            name
          }
        }
        """
        return self._gql(q, {"id": performer_id}).get("findPerformer")

    def find_performer_by_name(self, name: str) -> dict[str, Any] | None:
        q = """
        query FindPerformers($q: String!) {
          findPerformers(filter: {q: $q, per_page: 10}) {
            performers {
              id
              name
            }
          }
        }
        """
        performers = self._gql(q, {"q": name}).get("findPerformers", {}).get("performers", [])
        for p in performers:
            if (p.get("name") or "").lower() == name.lower():
                return p
        return performers[0] if performers else None

    def all_performers(self) -> list[dict[str, Any]]:
        q = """
        query AllPerformers($page: Int!, $per_page: Int!) {
          findPerformers(filter: {page: $page, per_page: $per_page}) {
            performers {
              id
              name
            }
          }
        }
        """
        out: list[dict[str, Any]] = []
        page = 1
        while True:
            chunk = self._gql(q, {"page": page, "per_page": 200}).get("findPerformers", {}).get("performers", [])
            if not chunk:
                break
            out.extend(chunk)
            if len(chunk) < 200:
                break
            page += 1
        return out


class JsonLogger:
    def __init__(self, log_path: Path, dry_run: bool):
        self.log_path = log_path
        self.dry_run = dry_run
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, action: str, reason: str, source: str = "", destination: str = "", **extra: Any) -> None:
        row = {
            "timestamp": now_iso(),
            "action": action,
            "reason": reason,
            "source": source,
            "destination": destination,
            "dry_run": self.dry_run,
        }
        row.update(extra)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_image_asset(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def is_support_file(path: Path) -> bool:
    return path.name in {".nogallery", ".uuid", ".meta.json", ".hashes"} or path.suffix.lower() in {".json", ".yml", ".yaml", ".txt"}


def move_or_quarantine(
    src: Path,
    dst: Path,
    logger: JsonLogger,
    reason: str,
    execute: bool,
    quarantine_root: Path | None = None,
    allow_delete_duplicates: bool = False,
) -> None:
    if src.resolve() == dst.resolve():
        return

    if dst.exists() and src.is_file() and dst.is_file():
        src_hash = sha256_file(src)
        dst_hash = sha256_file(dst)
        if src_hash == dst_hash:
            if allow_delete_duplicates and execute:
                try:
                    src.unlink()
                except PermissionError as exc:
                    logger.emit(
                        "manual_review",
                        "delete_permission_denied",
                        source=str(src),
                        destination=str(dst),
                        error=str(exc),
                    )
                    return
            logger.emit(
                "delete" if allow_delete_duplicates else "keep_duplicate",
                "exact_duplicate",
                source=str(src),
                destination=str(dst),
                sha256=src_hash,
            )
            return
        if quarantine_root is not None:
            qdst = quarantine_root / src.name
            logger.emit("quarantine", "destination_conflict", source=str(src), destination=str(qdst))
            if execute:
                qdst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.move(str(src), str(qdst))
                except PermissionError as exc:
                    logger.emit(
                        "manual_review",
                        "quarantine_move_permission_denied",
                        source=str(src),
                        destination=str(qdst),
                        error=str(exc),
                    )
            return
        logger.emit("skip", "destination_conflict", source=str(src), destination=str(dst))
        return

    logger.emit("move", reason, source=str(src), destination=str(dst))
    if execute:
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dst))
        except PermissionError as exc:
            logger.emit(
                "manual_review",
                "move_permission_denied",
                source=str(src),
                destination=str(dst),
                error=str(exc),
            )


def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def ensure_relative_symlink(link_path: Path, target_path: Path, logger: JsonLogger, execute: bool) -> bool:
    rel = os.path.relpath(target_path, start=link_path.parent)
    if link_path.is_symlink() or link_path.exists():
        if link_path.is_symlink() and os.readlink(link_path) == rel:
            logger.emit("keep", "symlink_current", source=str(link_path), destination=rel)
            return True
        logger.emit("replace", "symlink_update", source=str(link_path), destination=rel)
        if execute:
            if link_path.is_dir() and not link_path.is_symlink():
                shutil.rmtree(link_path)
            else:
                link_path.unlink()
    else:
        logger.emit("create", "symlink_new", source=str(link_path), destination=rel)
    if execute:
        link_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(rel, link_path, target_is_directory=True)
        except PermissionError as exc:
            logger.emit(
                "manual_review",
                "symlink_permission_denied",
                source=str(link_path),
                destination=rel,
                error=str(exc),
            )
            return False
    return True


def parse_common_args(desc: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--gallery-root", required=True)
    p.add_argument("--stash-url", default=os.getenv("STASH_URL", "http://127.0.0.1:9999/graphql"))
    p.add_argument("--stash-api-key", default=os.getenv("STASH_APIKEY", ""))
    p.add_argument("--target-performer-id", action="append", default=[])
    p.add_argument("--target-performer-name", action="append", default=[])
    p.add_argument("--all", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--report", default="")
    return p


def resolve_targets(client: StashClient, ids: list[str], names: list[str], use_all: bool) -> list[dict[str, str]]:
    if use_all:
        return [{"id": str(p["id"]), "name": p.get("name") or ""} for p in client.all_performers()]

    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for pid in ids:
        p = client.find_performer(str(pid))
        if p and str(p["id"]) not in seen:
            out.append({"id": str(p["id"]), "name": p.get("name") or ""})
            seen.add(str(p["id"]))
    for name in names:
        p = client.find_performer_by_name(name)
        if p and str(p["id"]) not in seen:
            out.append({"id": str(p["id"]), "name": p.get("name") or ""})
            seen.add(str(p["id"]))
    return out


def fail_if_no_api_key(api_key: str) -> None:
    if not api_key:
        raise SystemExit("Missing Stash API key. Set --stash-api-key or STASH_APIKEY")

#!/usr/bin/env python3
import argparse
import json
import os
import posixpath
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_STASH_URL = "http://192.168.1.147:9999/graphql"
DEFAULT_API_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJ1aWQiOiJyb290Iiwic3ViIjoiQVBJS2V5IiwiaWF0IjoxNzcyNzU0MTc3fQ."
    "10aU5TzoxuG6GJ-ECsaRQi28SR8xWsn3q5uIBeGebjc"
)
DEFAULT_INBOX_ROOTS = [
    "/downloads/Complete/xxx",
    "/downloads/usenet/_complete/xxx",
]
DEFAULT_SCENE_ROOT = "/data/scenes"
DEFAULT_MOVIE_ROOT = "/data/movies"
DEFAULT_DUPLICATE_STATE = "scripts/stash_inbox_organizer_state.json"
DEFAULT_DUPLICATE_QUARANTINE = "/downloads/_duplicates/already_in_library"


SCENE_QUERY = """
query InboxScenes($filter: FindFilterType) {
  findScenes(scene_filter: {path: {value: "/downloads", modifier: INCLUDES}}, filter: $filter) {
    count
    scenes {
      id
      title
      date
      organized
      studio { name }
      files {
        id
        path
        width
        height
        video_codec
      }
      movies {
        movie { name date }
        scene_index
      }
    }
  }
}
"""


MOVE_MUTATION = """
mutation MoveFiles($input: MoveFilesInput!) {
  moveFiles(input: $input)
}
"""


SCENE_UPDATE_MUTATION = """
mutation SceneUpdate($input: SceneUpdateInput!) {
  sceneUpdate(input: $input) {
    id
    organized
  }
}
"""


INVALID_CHARS = re.compile(r'[<>:"/\\\\|?*]+')
WHITESPACE = re.compile(r"\s+")
RELEASE_GROUP_RE = re.compile(r"(?:-|\[)([A-Za-z0-9][A-Za-z0-9._-]{1,30})\]?$")
BIT_DEPTH_RE = re.compile(r"(?<!\d)(8|10|12)[ -]?bit(?!\d)", re.I)
PROPER_RE = re.compile(r"\b(PROPER|REPACK|RERIP|REMASTERED|EXTENDED|UNCUT)\b", re.I)
SOURCE_RE = re.compile(
    r"\b("
    r"BLURAY|BDRIP|BRRIP|WEB[- .]?DL|WEBRIP|HDTV|DVDRIP|DVDSCR|UHD|REMUX"
    r")\b",
    re.I,
)
DATE_PATTERNS = [
    re.compile(r"(?<!\d)(20\d{2})[.\-_ ](\d{2})[.\-_ ](\d{2})(?!\d)"),
    re.compile(r"(?<!\d)(\d{2})[.\-_ ](\d{2})[.\-_ ](20\d{2})(?!\d)"),
    re.compile(r"(?<!\d)(\d{2})[.\-_ ](\d{2})[.\-_ ](\d{2})(?!\d)"),
]
NOISE_TOKENS = {
    "xxx", "mp4", "mkv", "avi", "wmv", "mov", "webdl", "webrip", "bluray",
    "bdrip", "brrip", "hdtv", "dvdrip", "x264", "x265", "hevc", "h264",
    "aac", "dts", "proper", "repack", "rerip", "extended", "uncut",
    "1080p", "720p", "480p", "2160p", "1440p", "4k", "8k",
}


@dataclass
class Candidate:
    scene_id: str
    file_id: str
    source_path: str
    dest_folder: str
    dest_basename: str
    mark_organized: bool
    reason: str


def gql(url: str, api_key: str, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"ApiKey": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], indent=2))
    return data["data"]


def load_state(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {"resolved_duplicates": {}}
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("resolved_duplicates", {})
    return data


def save_state(path: str, state: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)


def sanitize(value: str) -> str:
    value = value.replace(":", " - ")
    value = INVALID_CHARS.sub(" ", value)
    value = WHITESPACE.sub(" ", value).strip(" .-_")
    return value


def map_codec(codec: str | None) -> str:
    codec = (codec or "").lower()
    mapping = {
        "h264": "AVC",
        "hevc": "HEVC",
        "h265": "HEVC",
        "mpeg4": "XVID",
        "vp9": "VP9",
        "av1": "AV1",
    }
    return mapping.get(codec, codec.upper() if codec else "")


def infer_bit_depth(path: str) -> str:
    match = BIT_DEPTH_RE.search(path)
    return match.group(1) if match else ""


def infer_release_group(path: str) -> str:
    parts = [os.path.basename(path), os.path.basename(os.path.dirname(path))]
    for part in parts:
        part = os.path.splitext(part)[0]
        match = RELEASE_GROUP_RE.search(part)
        if match:
            group = match.group(1).strip("[]")
            if group.lower() not in {"mp4", "mkv", "avi"}:
                return group
    return ""


def split_tokens_from_path(path: str) -> list[str]:
    name = os.path.splitext(os.path.basename(path))[0]
    return [token for token in re.split(r"[.\-_ ]+", name) if token]


def infer_date(path: str) -> str:
    base = os.path.basename(path)
    for pattern in DATE_PATTERNS:
        match = pattern.search(base)
        if not match:
            continue
        groups = match.groups()
        if len(groups[0]) == 4:
            year, month, day = groups
        elif len(groups[2]) == 4:
            day, month, year = groups
        else:
            year = f"20{groups[0]}"
            month = groups[1]
            day = groups[2]
        return f"{year}-{month}-{day}"
    return ""


def infer_studio_and_title(path: str) -> tuple[str, str]:
    tokens = split_tokens_from_path(path)
    if not tokens:
        return "", ""
    studio = sanitize(tokens[0])
    date_index = -1
    for i in range(max(0, len(tokens) - 2)):
        chunk = ".".join(tokens[i:i + 3])
        if infer_date(chunk):
            date_index = i + 3
            break
    title_tokens = tokens[date_index:] if date_index > 0 else tokens[1:]
    filtered = []
    for token in title_tokens:
        lower = token.lower()
        if lower in NOISE_TOKENS:
            break
        if re.fullmatch(r"\\d{3,4}p", lower):
            break
        filtered.append(token)
    title = sanitize(" ".join(filtered))
    return studio, title


def infer_quality_parts(path: str, width: int | None, height: int | None) -> tuple[str, str]:
    source_match = SOURCE_RE.search(path)
    source = source_match.group(1).upper().replace(" ", "").replace(".", "").replace("-", "") if source_match else "WEBDL"
    source_map = {
        "WEBRIP": "WEBRip",
        "WEBDL": "WEBDL",
        "BDRIP": "Bluray",
        "BRRIP": "Bluray",
        "BLURAY": "Bluray",
        "HDTV": "HDTV",
        "DVDRIP": "DVDRip",
        "DVDSCR": "DVDScr",
        "UHD": "UHD",
        "REMUX": "Remux",
    }
    source_title = source_map.get(source, source.title())

    res = "Unknown"
    if height:
        if height >= 4320:
            res = "8K"
        elif height >= 2160:
            res = "2160p"
        elif height >= 1440:
            res = "1440p"
        elif height >= 1080:
            res = "1080p"
        elif height >= 720:
            res = "720p"
        elif height >= 576:
            res = "576p"
        else:
            res = "480p"

    proper_match = PROPER_RE.search(path)
    proper_suffix = f" {proper_match.group(1).title()}" if proper_match else ""
    return f"{source_title}-{res}", f"{source_title}-{res}{proper_suffix}"


def scene_dest(
    scene: dict[str, Any],
    file_obj: dict[str, Any],
    scene_root: str,
    movie_root: str,
    infer_from_filename: bool,
) -> Candidate | None:
    files = scene.get("files") or []
    if len(files) != 1:
        return None

    source_path = file_obj["path"]
    extension = os.path.splitext(source_path)[1]
    title = sanitize(scene.get("title") or "")
    date = scene.get("date") or ""
    studio_name = sanitize((scene.get("studio") or {}).get("name") or "")
    if infer_from_filename and (not title or not date or not studio_name):
        guessed_studio, guessed_title = infer_studio_and_title(source_path)
        title = title or guessed_title
        date = date or infer_date(source_path)
        studio_name = studio_name or guessed_studio
    if not title or not date:
        return None

    codec = map_codec(file_obj.get("video_codec"))
    bit_depth = infer_bit_depth(source_path)
    release_group = sanitize(infer_release_group(source_path))
    quality_title, quality_full = infer_quality_parts(source_path, file_obj.get("width"), file_obj.get("height"))
    codec_segment = f" - {codec}{bit_depth}" if (codec or bit_depth) else ""
    release_segment = f"-{release_group}" if release_group else ""

    movies = scene.get("movies") or []
    if movies:
        movie = movies[0]["movie"]
        movie_title = sanitize(movie.get("name") or title)
        movie_date = movie.get("date") or date
        movie_year = movie_date[:4] if len(movie_date) >= 4 else "Unknown"
        folder = posixpath.join(movie_root, f"{movie_title} ({movie_year})")
        basename = sanitize(f"{movie_title} ({movie_year}) - {quality_title}{codec_segment}{release_segment}") + extension
        return Candidate(scene["id"], file_obj["id"], source_path, folder, basename, True, "movie")

    studio = studio_name or "Unknown Studio"
    folder = posixpath.join(scene_root, studio, f"{title} - {date}")
    basename = sanitize(f"{title} - {date} {quality_full}") + extension
    return Candidate(scene["id"], file_obj["id"], source_path, folder, basename, True, "scene")


def collect_candidates(
    data: dict[str, Any],
    scene_root: str,
    movie_root: str,
    infer_from_filename: bool,
    resolved_duplicates: dict[str, Any],
) -> tuple[list[Candidate], list[tuple[str, str]]]:
    candidates: list[Candidate] = []
    skipped: list[tuple[str, str]] = []
    for scene in data["findScenes"]["scenes"]:
        files = scene.get("files") or []
        if not files:
            skipped.append((scene["id"], "no files"))
            continue
        if not any(file_obj["path"].startswith(root) for root in DEFAULT_INBOX_ROOTS for file_obj in files):
            continue
        if scene["id"] in resolved_duplicates:
            skipped.append((scene["id"], "resolved duplicate"))
            continue
        candidate = scene_dest(scene, files[0], scene_root, movie_root, infer_from_filename)
        if not candidate:
            reason = "missing title/date or multi-file"
            skipped.append((scene["id"], reason))
            continue
        if scene.get("organized") and any(path.startswith("/data/") for path in [f["path"] for f in files]):
            skipped.append((scene["id"], "already organized in library"))
            continue
        candidates.append(candidate)
    return candidates, skipped


def quarantine_candidate(
    url: str,
    api_key: str,
    candidate: Candidate,
    duplicate_quarantine: str,
) -> None:
    gql(
        url,
        api_key,
        MOVE_MUTATION,
        {
            "input": {
                "ids": [candidate.file_id],
                "destination_folder": duplicate_quarantine,
                "destination_basename": os.path.basename(candidate.source_path),
            }
        },
    )


def move_candidate(
    url: str,
    api_key: str,
    candidate: Candidate,
    dry_run: bool,
    state: dict[str, Any],
    state_path: str,
    duplicate_quarantine: str,
) -> str:
    if dry_run:
        return "dry-run"
    try:
        gql(
            url,
            api_key,
            MOVE_MUTATION,
            {
                "input": {
                    "ids": [candidate.file_id],
                    "destination_folder": candidate.dest_folder,
                    "destination_basename": candidate.dest_basename,
                }
            },
        )
    except RuntimeError as exc:
        message = str(exc)
        if "already exists" in message:
            print(f"duplicate {candidate.scene_id}: {message}")
            state["resolved_duplicates"][candidate.scene_id] = {
                "source_path": candidate.source_path,
                "duplicate_target": f"{candidate.dest_folder}/{candidate.dest_basename}",
            }
            save_state(state_path, state)
            try:
                quarantine_candidate(url, api_key, candidate, duplicate_quarantine)
                print(f"quarantined duplicate {candidate.scene_id} -> {duplicate_quarantine}")
            except Exception as quarantine_exc:
                print(f"quarantine failed {candidate.scene_id}: {quarantine_exc}")
            return "duplicate"
        if "sql: no rows in result set" in message:
            print(f"skip move {candidate.scene_id}: {message}")
            return "missing"
        raise
    if candidate.mark_organized:
        gql(
            url,
            api_key,
            SCENE_UPDATE_MUTATION,
            {"input": {"id": candidate.scene_id, "organized": True}},
        )
    return "moved"


def main() -> int:
    parser = argparse.ArgumentParser(description="Organize Stash inbox scenes into library paths.")
    parser.add_argument("--url", default=DEFAULT_STASH_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--scene-root", default=DEFAULT_SCENE_ROOT)
    parser.add_argument("--movie-root", default=DEFAULT_MOVIE_ROOT)
    parser.add_argument("--state-path", default=DEFAULT_DUPLICATE_STATE)
    parser.add_argument("--duplicate-quarantine", default=DEFAULT_DUPLICATE_QUARANTINE)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument(
        "--infer-from-filename",
        action="store_true",
        help="Allow scene title/date/studio fallback parsing from release filenames.",
    )
    parser.add_argument("--apply", action="store_true", help="Perform moves. Default is dry-run.")
    args = parser.parse_args()

    state = load_state(args.state_path)
    data = gql(args.url, args.api_key, SCENE_QUERY, {"filter": {"per_page": args.limit}})
    candidates, skipped = collect_candidates(
        data, args.scene_root, args.movie_root, args.infer_from_filename, state["resolved_duplicates"]
    )

    print(f"Found {len(candidates)} move candidates.")
    for candidate in candidates[:25]:
        print(f"[{candidate.reason}] {candidate.source_path}")
        print(f"  -> {candidate.dest_folder}/{candidate.dest_basename}")

    print(f"Skipped {len(skipped)} scenes.")
    for scene_id, reason in skipped[:25]:
        print(f"skip {scene_id}: {reason}")

    if not args.apply:
        print("Dry run only. Re-run with --apply to move files.")
        return 0

    moved = 0
    failed = 0
    duplicates = 0
    for candidate in candidates:
        try:
            result = move_candidate(
                args.url,
                args.api_key,
                candidate,
                dry_run=False,
                state=state,
                state_path=args.state_path,
                duplicate_quarantine=args.duplicate_quarantine,
            )
            if result == "moved":
                moved += 1
            elif result == "duplicate":
                duplicates += 1
        except Exception as exc:
            failed += 1
            print(f"error move {candidate.scene_id}: {exc}")
    print(f"Moved {moved} scenes.")
    print(f"Resolved duplicates {duplicates}.")
    print(f"Failed {failed} scenes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

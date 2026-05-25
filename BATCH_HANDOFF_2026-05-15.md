# Gallery + Infra Handoff (2026-05-15)

## What Is Complete

### 1) Canonical gallery migration to performer ID layout
- `scripts/gallery_migrate.py` executed against all performers.
- Report summary (execute all):
  - targets: `1952`
  - moves: `4448`
  - deleted: `134`
  - manual_review: `1952`
- Canonical layout in use:
  - `\\192.168.1.147\adult\performer_gallery\id\<performer_id>`

### 2) Path logic updates in plugin code
- Actress Library image storage logic updated to use canonical ID-based directories.
- Related sync/scrape callers updated to pass `stash_performer_id`.

### 3) Validation tooling in place
- Scripts present:
  - `scripts/gallery_tools.py`
  - `scripts/gallery_migrate.py`
  - `scripts/sync_gallery_name_view.py`
  - `scripts/validate_gallery_layout.py`

## What Is Not Complete Yet

### 1) By-name view creation
- `by-name` links fail when run from Windows SMB due to symlink permission policy.
- Validation currently fails every performer with:
  - `by_name_link_missing_or_broken`
  - `by_name_link_target_invalid`

### 2) Stash gallery population for most performers
- Many canonical dirs have files, but Stash gallery counts remain `0`.
- Marica Hase (`4869`) is confirmed with non-zero gallery image count.

## Root Causes

1. Symlink creation attempted from Windows against SMB share.
2. Stash has not fully imported/scanned canonical `id/` content into performer galleries for most performers.

## Current Linux Node Roles (live verified)

- `z4-media-01 (192.168.1.10)`:
  - Utility/monitoring node only
  - containers: `cadvisor`, `node-exporter`
  - no VM stack (`virsh` absent)

- `z4-media-02 (192.168.1.139)`:
  - Active processing node
  - containers: `fileflows`, `subtitle-worker-gpu`, `whisper-asr-webservice`, `cadvisor`, `node-exporter`
  - no VM stack (`virsh` absent)

## Proxmox Recommendation (current)

- Do not migrate these Linux nodes to Proxmox right now.
- Keep current roles; reassess only if VM usage or hypervisor requirements increase.

## Next Actions (in order)

1. Generate `by-name` links from Linux side (not Windows SMB).
2. Trigger Stash metadata scan/import for `/data/performer_gallery/id`.
3. Re-run `scripts/validate_gallery_layout.py --all`.
4. Confirm target performers show:
   - canonical path exists
   - by-name link valid
   - stash gallery image count > 0 (when files exist)

## New Chat Prompt (copy/paste)

Please continue from this exact state.

Known status:
- Canonical performer gallery migration is complete to ID paths:
  - `.../performer_gallery/id/<performer_id>`
- By-name link generation from Windows SMB is blocked by symlink permissions.
- Validation currently fails all performers mostly on by-name link checks.
- Many performers also still show `stash_gallery_missing_or_empty` even when canonical files exist.

Do these steps:
1. Run `sync_gallery_name_view.py` from Linux side (server/container context) using canonical `/data/performer_gallery`.
2. Trigger Stash scan/import for `/data/performer_gallery/id`.
3. Re-run `validate_gallery_layout.py --all`.
4. Return a concise summary:
   - passed/failed counts
   - top remaining failure reasons
   - 7-performer smoke test status:
     - 5234 Kiara Cole
     - 5091 Ember Snow
     - 6152 Lia Lin
     - 5444 Joanna Angel
     - 4955 Penny Pax
     - 4869 Marica Hase
     - 6377 Holly Hendrix

Read first:
- `MASTER_PLAN.md`
- `scripts/reports/gallery_migration_execute_all.json`
- `scripts/reports/validate_all.json`

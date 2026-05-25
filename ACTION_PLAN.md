# Adult Media Stack — Action Plan
**Built:** 2026-05-09 from live audit data  
**Stack:** Stash v0.31.1 · Whisparr v3.3.3 · 40 containers · Unraid 7.2.4

---

## The Actual Numbers

| Metric | Current | Target |
|--------|---------|--------|
| Performers | 1,897 | — |
| Performers with images | 356 (19%) | 1,897 (100%) |
| Performers needing images | **1,541** | 0 |
| Scenes total | 2,930 | — |
| Scenes matched to StashDB | 2,622 (89%) | 2,930 (100%) |
| Scenes missing performer | 196 | 0 |
| Scenes missing studio | 191 | 0 |
| Whisparr queue (active) | **1,001** | Clean |
| Stash plugins installed | 27 (26 enabled) | — |
| Scrapers installed | 21 | — |

**The headline problem:** 81% of performers have zero images. Everything else is secondary to that.

---

## Infrastructure State (updated 2026-05-13)

✅ stash-cdp (headless Chrome) running on port 9222 — wired to Stash's `scraperCDPPath`  
✅ FlareSolverr running on port 8191 — configured in config.ini  
✅ JavDB session cookie configured  
✅ JavLibrary session cookie configured  
✅ TPDB API key configured  
✅ StashDB API key configured  
✅ actress_library v0.1.0 installed, all 8 tasks available  
✅ 89% of scenes already matched to StashDB  
⚠️ scraperCDPPath uses host IP (fragile if IP changes)  
⚠️ 1,001 Whisparr queue items — many at 0MB with status=downloading (stuck)  
✅ `update_stash_profile = true` validated live on performer `Marica Hase`  
✅ SSH access restored to Unraid and used for live plugin execution  
⚠️ IAFD detail pages are still unreliable and remain a secondary source  
⚠️ `javlibrary` now uses the correct AJAX search backend, but the current cookie set is insufficient for that backend and needs a fuller browser cookie header  
✅ `javdb_images` repaired on 2026-05-13 — now yields live images when JAVDB returns a performer page  

## Current Validated State

The actress library path is no longer theoretical.

Validated against the real Stash container on `192.168.1.147`:

- dry-run and non-dry-run `enrich` both succeeded
- dry-run `full_sync` succeeded with `max_per_run=2`
- StashDB image scraping downloaded `38` real images for `Marica Hase`
- the best image was pushed back to Stash as the live performer profile photo
- browser validation succeeded at `http://192.168.1.147:9999/performer/4869/image`

What is still not complete:

- `javlibrary` is now wired correctly, but live search still needs a fuller logged-in cookie set
- JAVDB name coverage still needs work for performers whose current search term returns no actor match
- Whisparr backlog cleanup is still pending
- alternate AI tagging plugins (`ai_tagger`, `AIOverhaul`) are not viable today; live community directories are effectively empty placeholders

---

## Phase 0 — Fix the Two Blockers
*Time: ~30 minutes. Do these first. Everything else depends on them.*

### 0A. Fix Whisparr Import Backlog

The queue shows 1,001 items. Several sampled items have `sizeleft=0MB` with `status=downloading` — the download client finished but Whisparr hasn't processed them. This means completed content isn't making it into Stash.

**Steps:**
1. Open Whisparr → Activity → Queue (`http://192.168.1.147:7070/activity/queue`)
2. Check: how many are "Completed" vs "Downloading" vs "Failed"?
3. Sort by Status — look for items stuck on "Completed, Awaiting Import"
4. Select all stuck items → Manual Import or force re-process
5. Open qBittorrent (`http://192.168.1.147:8080`) — check if torrents are seeding but Whisparr lost track
6. Open SABnzbd (`http://192.168.1.147:8282`) — check for completed but unprocessed jobs
7. In Whisparr: Settings → Download Clients → re-test both clients
8. Run a manual search on a few items to confirm the pipeline is live

**Root cause to investigate:** If filemonitor was running but not started as a Service (task says "Start Library Monitor Service" vs "Monitor as a Plugin"), files may not have been imported. Check filemonitor status.

### 0B. Restore SSH Access

Without SSH, every server operation requires the web UI. That's too slow for the bulk work ahead.

**Steps (all via PowerShell "Run with PowerShell" on a .ps1 file):**

1. Create `generate_ssh_key.ps1` in the workspace:
   ```powershell
   $keyPath = "C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management\.codex-ssh\unraid_new_ed25519"
   ssh-keygen -t ed25519 -f $keyPath -N '""' -C "cowork-claude"
   $pubKey = Get-Content "$keyPath.pub"
   Write-Host "PUBLIC KEY:"
   Write-Host $pubKey
   Write-Host ""
   Write-Host "Run this on Unraid terminal:"
   Write-Host "echo '$pubKey' >> /root/.ssh/authorized_keys"
   ```
2. Run it, get the public key output
3. Open Unraid web terminal (Tools → Terminal opens popup; use it to paste the echo command)
4. Test: create `test_ssh.ps1` to confirm connection works
5. Update `audit_unraid.ps1` to use the new key path

---

## Phase 1 — Validate the Scraping Stack
*Time: 1–2 hours. Don't run bulk jobs until you know what's working.*

The infrastructure exists. What's unknown is whether any of it actually produces results.

### 1A. Quick CDP Validation (5 minutes)

The `scraperCDPPath` points to `http://192.168.1.147:9222/json/version`. Verify it responds:

```
Open in browser: http://192.168.1.147:9222/json/version
```

Should return JSON with Chrome version info. If it doesn't, the stash-cdp container needs a restart.

**While you're there:** Change the scraperCDPPath in Stash settings from the host IP to the container hostname for resilience:
- Stash → Settings → Scraping → Chrome CDP Path
- Change to: `http://stash-cdp:9222/json/version`
- (Both containers are on the `stash-backend` Docker network so this works)

### 1B. Test Each Scraper on One Known Performer

Pick **Marica Hase** (Japanese actress, well-indexed on all sources). In Stash:
- Performers → Marica Hase → Scrape → By Name → test each source in order

| Scraper | Expected | Notes |
|---------|----------|-------|
| TPDB | ✅ Should work | API key present |
| StashDB | ✅ Should work | API key present |
| JavDB | 🔶 Test needed | Needs CDP + session cookie |
| JavLibrary | 🔶 Test needed | Needs CDP + session cookie |
| Boobpedia | 🔶 Test needed | Direct HTTP |
| FreeOnes | 🔶 Test needed | Direct HTTP |
| IAFD | ❌ Known 403 | Skip for now |

**If JavDB/JavLibrary fail:** The session cookies may have expired. They're long-lived but not infinite. You'd need to log in via browser, grab fresh cookies from DevTools → Application → Cookies, and update config.ini.

### 1C. Test FlareSolverr

Navigate to `http://192.168.1.147:8191` — should show FlareSolverr health page. Then confirm actress_library routes through it by checking whether JavDB scraping works with Cloudflare pages. FlareSolverr is an alternative to CDP for Cloudflare bypass — the config.ini has `flaresolverr_url` set, so actress_library can use it for image scraping even if the main Stash scraper uses CDP.

### 1D. Test actress_library Directly

In Stash → Tasks → actress_library:
1. Run **"Import Performer by Name"** → input: `Marica Hase`
   - Expected: creates or enriches the performer with aliases, birthdate, measurements, nationality
2. Run **"Scrape Images for Performer"** → input name: `Marica Hase`
   - Expected: images downloaded to `/data/performer_gallery/marica_hase/`
   - Check: face detection scores appear in logs
   - Check: images visible in Stash performer gallery
3. Review image quality manually

---

## Phase 2 — Performer Enrichment (The Main Work)
*This addresses the 1,541 performers with no images — the headline problem.*

### 2A. Enable Profile Photo Auto-Update

Status: complete on the validated live config.

After validating Phase 1D looks good:

1. Edit `config.ini` — change:
   ```ini
   update_stash_profile = false
   ```
   to:
   ```ini
   update_stash_profile = true
   ```
2. Sync the file to the server:
   - Via SSH (once 0B is done): `scp config.ini root@192.168.1.147:/mnt/container/appdata/stash/stash-plugins/config.ini`
   - Or: paste contents via Unraid terminal
3. Restart the Stash container (Settings → Services or Unraid Docker page) to reload config

### 2B. Bulk Enrichment Strategy

Status: configuration updated locally to `max_per_run = 100`. Large batch run still pending.

With `max_per_run = 25`, each "Enrich All Performers" run processes 25 performers. At 1,541 needing work, that's ~62 runs. Don't do this manually.

**Option A: stash-scheduler (recommended)**
Configure the scheduler plugin to run "Enrich All Performers" nightly. With `max_per_run = 25`, processing ~1,541 performers at 25/run takes ~62 nights. That's too slow.

**Option B: Increase max_per_run**
Change `max_per_run = 25` to `max_per_run = 100` in config.ini. Then runs process 100 performers each time. ~15–16 runs to cover everyone. Keep an eye on rate limits and session validity.

**Option C: Burst run this weekend**
Set `max_per_run = 200`, run "Enrich All Performers" manually 8 times over Saturday/Sunday. Done in a weekend. Risk: session cookies could get flagged or expired. Start with 50 and see how it holds up.

**Recommendation:** Do Option C to get initial coverage, then drop back to stash-scheduler with `max_per_run = 50` for ongoing maintenance.

### 2C. Image Source Priority

The config.ini has `sources = r18,javdb,javlibrary,boobpedia,stashdb`. This is the scraping order for images. Current priority is good for JAV content. For western performers, boobpedia and stashdb are the strongest — you may want `stashdb,boobpedia,r18,javdb,javlibrary` for non-JAV performers. Consider splitting into two runs if your library is mixed.

### 2D. Alias Index Maintenance

After each bulk enrichment run:
1. Run **"Export Alias Index"** — captures all performer name variations
2. Run **"Rebuild Alias Index"** — ensures scene matching uses updated aliases

These are fast (seconds). Add to your post-enrichment checklist.

---

## Phase 3 — Scene Metadata Cleanup
*89% of scenes are already StashDB-matched. Focus on the remaining 11% + performer/studio gaps.*

### 3A. Find the 308 Unmatched Scenes

In Stash → Scenes → filter by "Has StashID: No":
- These are likely: newer releases, edge cases, niche studios, files with bad naming
- Try: Tagger → Scene → search by filename fragment → match to StashDB/TPDB

### 3B. Fix the 196 Scenes with No Performer

These scenes exist in Stash with no performer attached. Many are probably already matched to StashDB — the performers just haven't been linked.

**Approach:**
1. Filter Scenes → no performers
2. For each: use Auto-Tag (Stash built-in) to match by filename
3. Or: use the sceneMatcher plugin — it's installed (v1.1.0) and designed for this
4. Run Auto Tag from Stash → Tasks → Auto Tag → Performers

### 3C. Fix the 191 Scenes with No Studio

Same approach: Auto Tag → Studios. Studio names in filenames often match the Stash studio list.

### 3D. mcMetadata — Export to Media Server

Once scene metadata and performer images are clean:
1. Go to Stash → Tasks → mcMetadata → **"Bulk Update Scenes"**
   - Generates NFO files alongside each video
   - Renames files using configured template
   - Copies performer images to media server performer folders
2. Run **"Bulk Update Performers"** to push performer photos

**Then in Jellyfin/Plex/Emby:** trigger a library rescan. The NFO files will be picked up automatically.

---

## Phase 4 — Whisparr Optimization
*1,001 queue items. Clean this up so new content flows automatically.*

### 4A. Diagnose the Queue

Navigate to `http://192.168.1.147:7070/activity/queue` and look at the breakdown:
- **Downloading:** actively downloading — these are fine
- **Completed, Awaiting Import:** stuck — these need manual intervention
- **Warning/Failed:** broken downloads — need re-search or manual grab

Sort by "Status" to cluster the problems.

### 4B. Force-Clear the Stuck Items

For items "Completed, Awaiting Import":
1. Select all → Remove (keep files)
2. Then: Whisparr → System → Events → look for import errors
3. Check import root folder permissions — Whisparr needs write access to `/data`
4. Manual Import: Whisparr → Wanted → Manual Import → browse to the completed files

### 4C. Prowlarr Health Check

Navigate to `http://192.168.1.147:9696`:
- Check each of the 14 indexers → look for red/failing
- sukebei.nyaa.si, xxxtor, and U3C3 are the highest-value JAV sources — make sure these are green
- Run "Test All Indexers" and look at results

### 4D. Review Import Lists

19 import lists (performers + studios via StashDB/TMDb) are generating "wanted" entries. Check:
- Are these generating Whisparr searches?
- Are those searches returning results?
- Are there quality cutoff issues blocking downloads?

Quality profiles: Any, Ultra-HD, VR, 4K→SD fallback, Scenes, 4K Preferred. Make sure "Scenes" profile isn't blocking reasonable quality items.

---

## Phase 5 — Automation & Ongoing Maintenance
*Set-and-forget so the library stays current.*

### 5A. Start filemonitor as a Service

Currently unknown whether filemonitor is running as a Service or Plugin (or not running at all). Service mode is critical — it watches library paths and auto-imports new files.

1. Stash → Tasks → filemonitor → **"Start Library Monitor Service"**
2. Confirm it stays running after Stash restarts: check the Stash container restart policy

### 5B. Configure stash-scheduler

The stash-scheduler plugin (v0.6.0) can run tasks on a cron schedule. Configure:

| Task | Schedule | Notes |
|------|----------|-------|
| Enrich All Performers | Nightly 2am | `max_per_run = 50` for maintenance |
| Rebuild Alias Index | After enrichment | |
| mcMetadata Bulk Update | Weekly Sunday 3am | After enrichment settles |
| Auto Tag | Weekly | Pick up newly imported scenes |

### 5C. Session Cookie Rotation Plan

JavDB and JavLibrary session cookies will expire. When they do, the image scraping for those sources will silently fail.

**Signs of expiry:** actress_library logs show 0 images from javdb/javlibrary sources.

**Fix:** Log in to JavDB and JavLibrary in your browser, open DevTools → Application → Cookies, copy the session cookie value, update `config.ini`, re-sync to server.

**Proactive:** Set a calendar reminder every 90 days to rotate cookies.

### 5D. Explore ahavenvlmconnector

The ahavenvlmconnector (v1.1.1) plugin is installed and enabled with tasks: "Tag Videos", "Collect Incorrect Markers and Images", "Find Marker Settings". This appears to use a Vision Language Model to auto-tag scene content. Worth exploring once performer enrichment is done — it could automate tagging at scale. Check if it requires an API key or uses a local model.

Backlog update:

- `ai_tagger` community plugin directory on Unraid is effectively empty aside from `__pycache__`
- `AIOverhaul` community plugin directory is also effectively empty and still has no proven backend
- treat `ahavenvlmconnector` as the only viable AI-tagging path for now

---

## Phase 6 — Config File Sync Problem

Currently `config.ini` lives in two places:
- **Local:** `C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management\stash-plugins\config.ini`
- **Server:** `/mnt/container/appdata/stash/stash-plugins/config.ini`

When you edit locally and forget to sync, the server runs stale config. When the server changes (e.g., Stash writes back an updated api_key), your local copy goes stale.

**Solution:** Once SSH is restored, create a `sync_config.ps1` script:
```powershell
$localConfig = "C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management\stash-plugins\config.ini"
$remoteConfig = "root@192.168.1.147:/mnt/container/appdata/stash/stash-plugins/config.ini"
$key = "C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management\.codex-ssh\unraid_new_ed25519"

# Push local → server
scp -i $key $localConfig $remoteConfig
Write-Host "Config synced to server."
```

Run this every time you edit config.ini locally.

---

## IAFD — Decision Point

IAFD detail pages return 403. IAFD is NOT in the actress_library image sources list (sources = r18,javdb,javlibrary,boobpedia,stashdb) so it doesn't affect performer image scraping. It only affects the community IAFD scraper for scene/performer URL lookups.

**Recommendation:** Leave it broken for now. TPDB and StashDB provide better coverage for both scenes and performers. Come back to IAFD if you find a specific gap that only IAFD can fill.

---

## Execution Order (Quick Reference)

```
Week 1
  Day 1:  Phase 0A — Fix Whisparr import backlog
  Day 1:  Phase 1A — Confirm CDP responds at :9222
  Day 1:  Phase 1B — Test scrapers on Marica Hase
  Day 1:  Phase 1D — Validate actress_library on 1 performer
  Day 2:  Phase 0B — Restore SSH access
  Day 2:  Phase 2A — Enable update_stash_profile = true
  Day 2:  Phase 2B — Burst run enrichment (increase max_per_run, run 8x)

Week 2
  Phase 3A/B/C — Scene metadata cleanup (unmatched, no performer, no studio)
  Phase 4A/B/C — Whisparr queue cleanup + Prowlarr health check

Week 3
  Phase 3D — mcMetadata bulk update → Jellyfin/Plex NFO export
  Phase 5A — Start filemonitor as Service
  Phase 5B — Configure stash-scheduler for nightly runs
  Phase 6  — Config sync script

Ongoing
  Phase 5C — Cookie rotation every 90 days
  Phase 5D — Explore ahavenvlmconnector once library is clean
  Next code item — refresh JavLibrary browser cookies and rerun live lookup, then improve JAVDB alias/search fallback for missed names
```

---

## Files Referenced

| File | Location |
|------|----------|
| config.ini (local) | `stash-plugins/config.ini` |
| config.ini (server) | `/mnt/container/appdata/stash/stash-plugins/config.ini` |
| audit script | `audit_unraid.ps1` |
| SSH keys | `.codex-ssh/` |
| This audit | `AUDIT_2026-05-09.md` |
| STATE.md | `stash-plugins/STATE.md` |

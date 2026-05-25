# Master Plan — Adult Media Platform
**Built:** 2026-05-09 from live audit of all systems  
**Authority:** Full — may change, replace, or delete any software. Hardware changes recommended where warranted.  
**Status:** Living document. Update as phases complete.

---

## What We're Actually Working With

This is not a basic Plex box. This is a multi-layer AI-augmented media platform that is ~60% built and ~0% connected. Every piece needed for the target state already exists. The work is wiring, tuning, and executing — not building from scratch.

### Network
| Machine | Hostname | IP | Role | Status |
|---------|----------|----|------|--------|
| Unraid | unriad01 | 192.168.1.147 | Primary compute + storage | ✅ Running, 38 containers |
| Workstation | localhost-live | 192.168.1.182 | **Fedora Linux**, DaVinci Resolve, Ollama (RTX 4090) | ✅ Running |
| z4-media-01 | z4-media-01 | 192.168.1.10 | **Lightweight utility/monitoring node** (cadvisor + node-exporter), no active VM stack | ✅ Up (low load) |
| z4-media-02 | z4-media-02 | 192.168.1.139 | **Active Linux media-processing node** (FileFlows + subtitle-worker + whisper-asr) | ✅ Up (low/steady load) |
| Laptop | tom-lt | 192.168.1.155 | Laptop | ✅ Up |

### Linux Node Reality Check (confirmed live over SSH)
| Host | Uptime | Current Workload | Containers | VM stack |
|------|--------|------------------|------------|----------|
| z4-media-01 (192.168.1.10) | ~47 days | Utility/monitoring only | cadvisor, node-exporter | No `virsh` |
| z4-media-02 (192.168.1.139) | ~47 days | Media processing | fileflows, subtitle-worker-gpu, whisper-asr-webservice, cadvisor, node-exporter | No `virsh` |

### Proxmox Decision (current)
- Do **not** migrate these Linux nodes to Proxmox right now.
- Rationale: both are currently Docker-first workers with little/no VM usage; migration risk and downtime outweigh immediate benefit.
- If Proxmox testing is desired later, pilot on `z4-media-01` first (lower impact), then reassess.

### Unraid Hardware — CONFIRMED
| Component | Spec |
|-----------|------|
| CPU | Intel Core i9-12900K — 16 cores / 24 threads / 5.2 GHz boost |
| RAM | 62 GB (no swap) |
| GPU | **NVIDIA GeForce GTX 1660 Ti — 6 GB VRAM** |
| GPU driver | 595.58.03 · CUDA 13.2 |
| NVMe | 1.9 TB (containers) — 54% full |
| OS | Unraid 7.2.4 · kernel 6.12.54-Unraid |

### Unraid Storage — CONFIRMED
| Pool | Raw Size | Used | % Full | Notes |
|------|----------|------|--------|-------|
| dtv (ZFS) | **311 TB** | 261 TB | **83%** | ⚠️ Above 80% — ZFS perf degrades |
| itv (ZFS) | 87.3 TB | 68.4 TB | 78% | Includes adult library (8.5 TB) |
| photography (ZFS) | 43.7 TB | 24.2 TB | 55% | |
| torrent (ZFS) | 7.25 TB | 2.75 TB | 37% | |
| NVMe (`/mnt/container`) | 1.9 TB | 990 GB | 54% | All Docker app data |

### Laptop Hardware (tom-lt, 192.168.1.155) — NEW, confirmed 2026-05-13
*Cowork runs on this machine. Previously unlisted.*

| Component | Spec |
|-----------|------|
| OS | Windows 11 build 26200 |
| GPU | NVIDIA RTX A3000 Laptop GPU — 6 GB VRAM (CUDA 8.6, driver 591.86) |
| RAM | 63.7 GB |
| Ollama | v0.23.2 — models: qwen2.5:7b (4.7 GB), llava:7b (4.7 GB) |
| Ollama bind | `127.0.0.1:11434` (localhost only — correct for a laptop, don't need LAN access here) |
| Note | Ollama v0.23.1 had GPU discovery timeout bug → fell back to CPU → slow/unresponsive. Fixed in v0.23.2. |

### Workstation Hardware (localhost-live, 192.168.1.182) — CONFIRMED 2026-05-13
| Component | Spec |
|-----------|------|
| OS | **Fedora Linux** (was on kernel 6.19.14-300.fc44, now 7.0.4-200.fc44 after DNF update) |
| GPU | **NVIDIA RTX 4090 — 24 GB VRAM** (22.5 GiB recognized by CUDA, driver 595.71.05) |
| Ollama | **v0.23.3** ✅ — updated 2026-05-13. GPU detected correctly on startup. `OLLAMA_HOST=0.0.0.0:11434` already configured. |
| Ollama models | llava:13b (~8 GB), llava:7b — both loaded and accessible on LAN at :11434 |
| Ollama service | systemd service. Logs via `journalctl -u ollama`. Currently stable. |
| SSH access | Key added (2026-05-13). Direct: `ssh -i claude_cowork_ed25519 mbeck@192.168.1.182` |
| Browser | Opera GX installed and used — **root cause of crash loop** (see below) |

### ⚠️ Workstation Crash Root Cause — DIAGNOSED 2026-05-13
**9 reboots on May 12, 16:39–17:46 PDT. Root cause: NVIDIA GPU VA space exhaustion.**

Pattern confirmed across boots -7, -6, -5, -4 via journalctl:
```
NVRM: dmaAllocMapping_GM107: can't alloc VA space for mapping.
NVRM: nvAssertOkFailedNoLog: Assertion failed: Out of memory [NV_ERR_NO_MEMORY]
com.opera.opera-gx.desktop: SharedContextState context lost via EXT_robustness. Reset status = GL_GUILTY_CONTEXT_RESET_KHR
```

**What happened:** Unraid was running Stash's ahavenvlmconnector which was sending rapid image inference requests to Ollama (llava:13b on the 4090) via POST `/v1/chat/completions`. Simultaneously, Opera GX browser was open and using the GPU for hardware-accelerated rendering/video. The two together exhausted the NVIDIA BAR1 virtual address space — the NVIDIA kernel module panicked, hard-resetting the system with no clean shutdown.

**Why it stopped:** Current boot (since 17:46 PDT) is stable. DNF updated 292 packages (including kernel 7.0.4 and potentially a newer NVIDIA driver). Crash has not recurred.

**Mitigation (do now):** Close Opera GX (or disable GPU hardware acceleration in it) before running heavy Ollama inference. Or limit Ollama GPU headroom with `OLLAMA_GPU_OVERHEAD=2GiB` in the systemd override.

**Still needed:** Update Ollama from v0.21.0 to latest (has GPU discovery timeout bug fix and other improvements).

### GPU Comparison — CONFIRMED (2026-05-13)
| Machine | GPU | VRAM | AI Capability |
|---------|-----|------|---------------|
| Unraid | GTX 1660 Ti | 6 GB | 7B models on GPU; no 14B+ |
| Laptop (tom-lt) | RTX A3000 Laptop | 6 GB | 7B models on GPU; also has 63.7 GB RAM |
| Workstation (.182) | **RTX 4090** | **24 GB** | 32B+ models, full quality vision — primary AI node |

**The workstation (.182) is the AI powerhouse. Route heavy inference there. Currently stable.**

### Full Container Inventory

**Adult Media Core:**
| Container | Version | Port | Status |
|-----------|---------|------|--------|
| stash | v0.31.1 | 9999 | ✅ Running |
| stash-cdp | chromedp/headless-shell | 9222 | ✅ Running |
| whisparr-v3 | v3.3.3.683 | 7070 | ✅ Running, 1001 queue items |
| prowlarr | latest | 9696 | ✅ Running, 14 indexers |
| flaresolverr | latest | 8191 | ✅ Running |

**Download Stack:**
| Container | Port | Notes |
|-----------|------|-------|
| binhex-qbittorrentvpn | 8080 | Torrents behind VPN ✅ |
| sabnzbd | 8282 | Usenet ✅ |
| recyclarr | — | TRaSH quality sync ✅ |

**General Media Automation:**
| Container | Port |
|-----------|------|
| radarr | 7878 |
| sonarr | 8989 |
| bazarr | 6767 |
| lidarr | 8686 |
| binhex-readarr | 8787 |
| mylar3 | 8090 |

**Media Servers:**
| Container | Version | Port | Notes |
|-----------|---------|------|-------|
| Jellyfin | 10.11.8 | 8096 | ✅ Running |
| Plex-Media-Server | latest | 32400 | ✅ Running |
| tautulli | latest | 8181 | ✅ Plex analytics |
| Kometa | latest | — | Plex metadata mgmt |

**AI Stack (THE KEY ASSET):**
| Container | Version | Port | Models / Notes |
|-----------|---------|------|----------------|
| ollama | 0.23.2 | 11434 | llama3.2:3b, **llava:7b** (vision), moondream, qwen3.5:4b |
| open-webui | latest | 3001 | UI for Ollama |
| ComfyUI-Nvidia-Docker | latest | 8189 | GPU image gen |
| Faster-Whisper-Nvidia | latest | 10300 | GPU speech-to-text (on stash-backend network!) |
| Qdrant | latest | 6333 | Vector DB: websearch, rag_collection, open-webui_web-search |

**Orchestration & Monitoring:**
| Container | Port |
|-----------|------|
| n8n | 5678 |
| Grafana | 3000 |
| Prometheus | 9090 |
| cadvisor | 8082 |
| SearXNG | 8888 |

**Other Services:**
| Container | Port | Notes |
|-----------|------|-------|
| immich_pro | 8081 | Photo mgmt (PostgreSQL + Redis backing) |
| tdarr | 8264/8265/8266 | Video transcoding v2.71.01, uptime 2+ days ✅ |
| audiobookshelf | 13378 | |
| calibre | 8085/8086 | |
| n8n | 5678 | Workflow automation — running healthy, API auth-required |
| Unraid-Cloudflared-Tunnel | — | Remote access ✅ |
| OpenProject | 5683 | ⚠️ Misconfigured (Invalid host_name) — likely unused |
| OpenClaw | 18789 | AI gateway/CLI — "OpenClaw Control" web UI, created 2026-05-07 |

### Stash Plugins Installed
| Plugin | Dir | Status | Notes |
|--------|-----|--------|-------|
| actress_library | `actress_library/` | ✅ Configured | Main performer enrichment tool |
| ahavenvlmconnector | `ahavenvlmconnector/` | ⚠️ **UNCONFIGURED** | No Ollama URL or model set |
| AIOverhaul | `AIOverhaul/` | ❌ **BROKEN** | backend_base_url=:4153 — port not running |
| ai_tagger | `ai_tagger/` | ❓ Unknown | Third AI tagging plugin — purpose unclear |
| mcMetadata | `mcMetadata/` | ✅ v1.4.0 | NFO + rename for Jellyfin/Plex |
| sceneMatcher | `sceneMatcher/` | ✅ v1.1.0 | StashDB scene matching |
| studioManager | `studioManager/` | ✅ v0.1.0 | Bulk studio assignment |
| tagManager | `tagManager/` | ✅ Installed | Tag management |
| performerImageSearch | `performerImageSearch/` | ✅ Installed | Image search helper |
| missingScenes | `missingScenes/` | ⚠️ Disabled | Unknown if needed |

**Community plugins** also present in `community/` subdirectory.

### Stash Library State
*Last verified: 2026-05-11 via live API*

| Metric | Current | Change |
|--------|---------|--------|
| Performers | 1,902 | +5 |
| Performers with images | 356 **(19%)** | — |
| Performers needing images | **1,546** | +5 (new performers added) |
| Scenes | 2,964 | +34 |
| Scenes matched to StashDB | 2,647 (89%) | +25 |
| Scenes missing performer | **187** | ✅ -9 (Auto Tag partial run?) |
| Scenes missing studio | **182** | ✅ -9 |
| Scenes without StashDB ID | **317** | ↑ (new scenes added unmatched) |
| Studios | 798 | +5 |
| Tags | 1,853 | +5 |
| Whisparr queue | **971** | ✅ -30 cleared |

---

## Target State

When done, this is what happens automatically:

```
1. Whisparr finds new scene via import list or search
          ↓
2. qBittorrent (VPN) or SABnzbd downloads it
          ↓
3. filemonitor detects new file → triggers Stash scan
          ↓
4. Stash scrapes metadata (JavDB/TPDB/StashDB via CDP/FlareSolverr)
          ↓
5. actress_library enriches all performers in the scene
   - Downloads images from r18, javdb, javlibrary, boobpedia, stashdb
   - Runs face detection → selects best photo
   - Sets performer profile photo in Stash
          ↓
6. ahavenvlmconnector → Ollama (llava model) analyzes scene thumbnails
   - Generates content tags (acts, positions, attributes)
   - Writes tags back to Stash
          ↓
7. Faster-Whisper transcribes scene audio
   - Extracts Japanese/English dialogue
   - Embeds subtitles or stores as metadata
          ↓
8. n8n orchestrates everything — handles retries, errors, ordering
          ↓
9. tdarr transcodes to H.265/AV1 (storage savings)
          ↓
10. mcMetadata generates NFO files + renames + exports performer images
          ↓
11. Jellyfin and/or Plex pick up NFO → full artwork, metadata, performer gallery
          ↓
12. Qdrant gets semantic embeddings → enables natural language search
          ↓
Done. Zero manual steps after initial configuration.
```

---

## The Critical Decisions (Decide These First)

### Decision 1: Plex vs Jellyfin vs Both

**Current:** Both running (Plex on 32400, Jellyfin on 8096).  
Running both is wasted resources and split attention.

| | Plex | Jellyfin |
|-|------|----------|
| Adult content | Awkward, cloud sync issues | Native support, fully local |
| Hardware transcoding | Good (needs Pass) | Good (free) |
| Mobile apps | Better | Good but clunkier |
| Metadata | Plex agents + Kometa | NFO-native, Jellyfin agents |
| Cost | $5/mo or ~$120 lifetime | Free forever |
| Kometa support | ✅ Primary use case | Limited |
| Community plugins | Large | Growing |

**Recommendation: Keep Jellyfin as primary for adult content. Keep Plex for everything else (mainstream TV/movies where Kometa shines). They serve different libraries.** Stop trying to make one server do both jobs.

→ **Action:** Configure mcMetadata to export to Jellyfin paths. Point Kometa at Plex mainstream library only.

### Decision 2: AI Tagging — Local vs Cloud — REVISED (2026-05-13)

**Reality check after workstation audit:** Both Unraid and workstation have 6 GB VRAM. The 32B/14B model assumption was wrong — those ran on CPU RAM (63.7 GB) and are now gone. **There is no high-VRAM GPU on the network.**

| Option | Quality | Cost | Speed | Privacy | Fits GPU? |
|--------|---------|------|-------|---------|-----------|
| llava:7b-v1.5-q2_K (current, Unraid) | Poor | $0 | Fast | ✅ | ✅ but tight |
| llava:7b-v1.5-q4_K_M (upgrade, Unraid) | Good | $0 | Fast | ✅ | ✅ 4.1 GB |
| llava:7b on workstation (installed) | Good | $0 | Fast | ✅ | ✅ 4.7 GB |
| llava:13b (was planned) | Better | $0 | Medium | ✅ | ❌ 7+ GB, won't fit GPU |
| GPT-4o vision API | Excellent | ~$0.01/scene | Fast | ❌ Cloud | N/A |

**Revised recommendation (post-laptop-audit):**
1. **Unraid Ollama:** Upgrade llava:7b-v1.5-q2_K → llava:7b-v1.5-q4_K_M (better quality, same VRAM)
2. **Workstation (.182 with RTX 4090):** Target for ahavenvlmconnector. llava:13b (7.4 GB) fits in 24 GB VRAM easily. **BUT need to fix OLLAMA_HOST binding first (see 0G)** and verify Ollama is running after the update.
3. **Laptop (tom-lt):** Has Ollama too (llava:7b, qwen2.5:7b) but laptop GPU is only 6 GB — don't route Unraid inference here.

→ **Critical action: Add SSH key to workstation, verify Ollama state, fix OLLAMA_HOST (see 0G)**

### Decision 2.5 (NEW): AIOverhaul vs ahavenvlmconnector vs ai_tagger — Which AI Plugin?

Three AI tagging plugins are installed in Stash. Only one should be used for scene tagging.

| Plugin | Status | Backend | Notes |
|--------|--------|---------|-------|
| **AIOverhaul** | ❌ BROKEN | `http://192.168.1.147:4153` (port not running) | Configured with API key, capture_events=true. Backend service not running. |
| **ahavenvlmconnector** | ⚠️ UNCONFIGURED | None set | Blank slate — no Ollama URL or model. Ready to configure. |
| **ai_tagger** | ❓ UNKNOWN | Unknown | Third option — purpose and config unknown. |

**What is AIOverhaul?** It's a Stash plugin that requires a *separate backend service* running on port 4153. That backend is NOT running. The plugin is essentially dead until someone starts that backend. This backend may be OpenClaw (the AI gateway on port 18789 — different port, unclear connection).

**Recommendation:**
1. Investigate `ai_tagger` to understand if it's better than `ahavenvlmconnector`
2. Configure `ahavenvlmconnector` — it's a known quantity, designed for Ollama, has documentation
3. Research AIOverhaul — if its backend is the OpenClaw gateway, it may be more powerful but also more complex to operate
4. Don't run all three simultaneously — pick one for tagging

→ **Immediate action: Configure ahavenvlmconnector first (Phase 1B). Investigate AIOverhaul + ai_tagger separately.**

### Decision 3: What Are .10 and .139? — ✅ ANSWERED

**z4-media-01 (192.168.1.10):** NFS storage server. Open ports: SSH (22) + NFS portmapper (111) only. No web UI, no media services. Role: shared network storage. No GPU. Direct SSH access still needed to confirm disk layout and NFS exports.

**z4-media-02 (192.168.1.139):** Linux media processing machine running **FileFlows v26.01.9.6181** (port 5000). 3 flow runners. This is a dedicated transcoding/processing node.

**Critical finding: FileFlows (z4-media-02) vs Tdarr (Unraid) are duplicates.** Both do automated video processing. Running both is wasteful and confusing. Pick one.

| | Tdarr (Unraid) | FileFlows (z4-media-02) |
|-|----------------|------------------------|
| Location | Unraid container | Dedicated Linux machine |
| Runners | Unraid GPU + CPU | 3 runners (hardware unknown) |
| Plugin library | Very large community | Smaller but growing |
| Pipeline model | Node-based flows | Flow-based (cleaner) |

**→ DECISION MADE: Keep Tdarr, decommission FileFlows.**

FileFlows audit (2026-05-10): 1 library configured ("Manually Added"), last scanned: NEVER (0001-01-01). One custom flow "Subtitle Worker Async JA" (disabled) that POSTs to a subtitle-worker at `192.168.1.139:8100`. Zero active processing jobs. FileFlows on z4-media-02 is essentially an empty install that has never processed anything.

**BUT:** z4-media-02 appears to have a subtitle-worker service running at port 8100 — a separate service for audio transcription/subtitle generation. This is useful for JAV content and worth preserving *independently* of FileFlows.

**Action:**
1. Stop FileFlows on z4-media-02 (the transcoding part is idle and redundant with Tdarr)
2. Keep/investigate the subtitle-worker at `192.168.1.139:8100` — could supplement Faster-Whisper on Unraid
3. Configure z4-media-02 as a Tdarr remote node (3 additional CPU workers) — requires SSH access first

### Decision 4 (NEW): Unraid Ollama vs Workstation Ollama for AI Tagging — ✅ RESOLVED

ahavenvlmconnector `haven_vlm_config.py` was already pointed at the workstation (`http://192.168.1.182:11434/v1`). The only problem was the model was set to `llava:34b` (nonexistent in Ollama). Fixed to `llava:13b` on 2026-05-10.

- **`llava:13b` pull triggered** on workstation Ollama — 7.4 GB download, in progress
- Once complete: tag a few scenes with `VLM_TagMe`, run "Tag Videos" task, verify output
- `CREATE_MARKERS = True` — plugin will create timestamped scene markers, not just flat tags
- Frame interval: every 80 seconds (deliberate — good for long JAV scenes)
- 35-tag act list already configured: Blowjob, Vaginal Fucking, Anal Fucking, Cumshot, etc.

**→ Next: Wait for pull to finish, then test on 3–5 scenes.**

---

## Phase 0 — Stabilize (Days 1–2)
*Fix what's broken before building anything new.*

### 0A: Whisparr Import Jam (2 hours)

1001 items in queue, many at 0MB downloaded. These are almost certainly completed downloads awaiting import that Whisparr lost track of.

```
http://192.168.1.147:7070/activity/queue
```

**Step by step:**
1. Sort queue by Status. Count: Downloading vs Completed vs Warning vs Failed
2. For "Completed, Awaiting Import": select all → Manual Import
3. Open qBittorrent `http://192.168.1.147:8080` → check Completed tab → verify Whisparr's `/data` path is mapped correctly
4. Whisparr → Settings → Download Clients → Edit each → Test
5. Whisparr → Settings → Media Management → confirm Root Folder `/data` permissions are writable
6. Force a manual scan: Whisparr → System → Backup, then trigger a library rescan

**If many items are permanently stuck:** Remove them with "Delete File" option off, then re-search. The content already exists locally — just needs re-importing.

### 0B: Restore SSH Access — ✅ COMPLETE (2026-05-09)

**Done.** New key generated and added to Unraid authorized_keys.

| Key | Location | Status |
|-----|----------|--------|
| `claude-cowork-2026` (ed25519) | `.codex-ssh/claude_cowork_ed25519` | ✅ Working — Unraid only |

SSH confirmed working: `ssh -i .codex-ssh/claude_cowork_ed25519 root@192.168.1.147`

**Still needed:** Add the same public key to z4-media-01, z4-media-02, and workstation.
```bash
# Public key to add to other machines:
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPT/s6bW5BmU8wLYQya1UDuqJHtHa5ivZVcSGZq7zYgv claude-cowork-2026
```

### 0C: Identify the Unknown Machines — ✅ COMPLETE (2026-05-09)

**z4-media-01 (192.168.1.10):** NFS storage server. Only SSH (22) and NFS portmapper (111) running. No GPU. No web UI. Role: additional network storage.

→ **Next step:** SSH in (need to add key), check `df -h` and `exportfs -v` to see what storage it has and what it exports.

**z4-media-02 (192.168.1.139):** Linux machine running FileFlows v26.01.9.6181 (port 5000). 3 flow runners configured. This is a dedicated media processing node.

→ **Next step:** SSH in (need to add key), check `nvidia-smi` (does it have a GPU?), check FileFlows for active workflows. Then make Tdarr vs FileFlows decision.

**Workstation (192.168.1.182):** Windows 11 with NVIDIA RTX GPU (≥24 GB VRAM). Running Ollama v0.21.0 with qwen2.5:32b and qwen2.5:14b. Port 11434 reachable from Unraid.

→ **Next step:** Run `nvidia-smi` in PowerShell to confirm exact GPU model. Add `llava:13b-v1.5-q4_K_M` to workstation Ollama for use with ahavenvlmconnector.

### 0D: Fix scraperCDPPath (5 min, do this right now)

Currently: `http://192.168.1.147:9222/json/version` (host IP — breaks if IP changes)  
Better: `http://stash-cdp:9222/json/version` (container name — always works)

Stash → Settings → Scraping → Chrome CDP Path → update → Save

### 0E: Investigate AIOverhaul + ai_tagger Before Configuring ahavenvlmconnector

Three AI tagging plugins are installed. Before committing to ahavenvlmconnector, spend 30 minutes investigating the other two:

**AIOverhaul investigation:**
1. Navigate to `http://192.168.1.147:18789` (OpenClaw) — does it have any AIOverhaul-related configuration?
2. Check AIOverhaul plugin directory: `cat /mnt/container/appdata/stash/plugins/AIOverhaul/*.yml`
3. Web search "AIOverhaul Stash plugin" — what does it do, and what backend does it require?
4. If AIOverhaul requires OpenClaw as its backend, it may offer more capabilities than ahavenvlmconnector

**ai_tagger investigation:**
1. `cat /mnt/container/appdata/stash/plugins/ai_tagger/*.yml`
2. What does it do differently from ahavenvlmconnector?
3. Does it use a different inference approach?

**Decision tree:**
- If AIOverhaul = powerful + easily configured → configure it with OpenClaw backend
- If ai_tagger = newer/better version of ahavenvlmconnector → use that instead
- If both are more complex than needed → proceed with ahavenvlmconnector (Phase 1B)

**Time limit:** 30 minutes of investigation. If not clearly better, go with ahavenvlmconnector.

### 0G: Fix Workstation Ollama — Open LAN Access ⚠️ BLOCKING ISSUE

**Confirmed (2026-05-13):** Ollama on the workstation binds to `127.0.0.1:11434` — localhost only. Unraid at 192.168.1.147 CANNOT reach it. ahavenvlmconnector pointing at `http://192.168.1.182:11434` will **always fail silently** until this is fixed.

**Root cause of prior crashes (confirmed from logs):** Ollama v0.23.1 had a GPU discovery timeout bug. When GPU detection timed out, it fell back to CPU-only mode. Running vision models on CPU with 63.7 GB RAM made the machine extremely slow (felt like a crash). Updated to v0.23.2 which correctly detects the RTX A3000 — **this part is fixed**.

**Fix — set OLLAMA_HOST environment variable on Windows:**
1. Open Start → search "Environment Variables" → "Edit the system environment variables"
2. Click "Environment Variables..."
3. Under "User variables for Tom Beck", click New:
   - Variable name: `OLLAMA_HOST`
   - Variable value: `0.0.0.0:11434`
4. Click OK → OK
5. Restart Ollama (right-click tray icon → Quit, then relaunch)
6. Verify from Unraid: `curl http://192.168.1.182:11434/api/tags`

**Also add Claude's SSH public key to workstation** so future sessions can connect:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPT/s6bW5BmU8wLYQya1UDuqJHtHa5ivZVcSGZq7zYgv claude-cowork-2026
```
Add to: `C:\Users\Tom Beck\.ssh\authorized_keys`

**Note:** Windows Firewall may also block port 11434. If curl from Unraid fails after the env var fix, add an inbound rule:
`netsh advfirewall firewall add rule name="Ollama LAN" protocol=TCP dir=in localport=11434 action=allow`

### 0F: filemonitor — Host-Level inotifywait Watcher ✅ DONE (2026-05-13)

**The filemonitor Stash plugin cannot run inside Docker** — it explicitly detects Docker and exits. Solution: host-level inotifywait script.

**Deployed:** `/boot/config/scripts/stash-filemonitor.sh`  
**Watching:** `/mnt/user/adult/movies`, `/mnt/user/adult/scenes`, `/mnt/user/torrents/Complete/xxx`, `/mnt/user/torrents/usenet/_complete/xxx`  
**On new video file:** calls `mutation { metadataScan(...) }` via Stash GraphQL with 30s debounce  
**Persists across reboots:** entry added to `/boot/config/go`  
**Log:** `/var/log/stash-filemonitor.log`

To check status: `pgrep -a inotifywait | grep -v changes.txt`  
To restart manually: `nohup bash /boot/config/scripts/stash-filemonitor.sh </dev/null >> /var/log/stash-filemonitor.log 2>&1 &`

---

## Phase 1 — Wire the AI Stack (Days 2–4)
*Connect what already exists. Zero new software required.*

### 1A: Fix Unraid Ollama Vision Model — ✅ DONE (2026-05-13)

**Confirmed via `ollama list` on 2026-05-11:** llava:7b-v1.5-q2_K is still present. llava:7b-v1.5-q4_K_M has NOT been pulled. Do this now.

**GPU confirmed: GTX 1660 Ti — 6 GB VRAM.** The current llava:7b-v1.5-q2_K is 2-bit quantized (junk quality). Replace it with the best model that actually fits:

```bash
ssh -i .codex-ssh/claude_cowork_ed25519 root@192.168.1.147

# Pull the q4 version (4.1 GB — fits in 6 GB with ~1.9 GB headroom)
docker exec ollama ollama pull llava:7b-v1.5-q4_K_M

# Wait for download, then verify it loads on GPU:
docker exec ollama ollama run llava:7b-v1.5-q4_K_M "describe this image" 2>&1 | head -5
docker exec ollama nvidia-smi  # confirm VRAM usage jumped

# Delete the degraded q2 model:
docker exec ollama ollama rm llava:7b-v1.5-q2_K
```

**Do NOT attempt llava-llama3:8b or any 14B+ model on Unraid.** With 6 GB VRAM, 8B at q4_K_M (~5 GB) is possible but leaves only 1 GB headroom — Jellyfin NVENC or ComfyUI running simultaneously will OOM. Stick with 7B q4.

**The real vision powerhouse is the workstation** — see 1B.

### 1B: Configure ahavenvlmconnector → Workstation Ollama — ✅ DONE (2026-05-10)

**Configuration was already partially complete.** `haven_vlm_config.py` had the workstation endpoint correct but used a nonexistent model (`llava:34b`). Fixed on 2026-05-10:

- **Endpoint:** `http://192.168.1.182:11434/v1` ✅ (was already set)
- **Model:** `llava:13b` ✅ (changed from nonexistent `llava:34b`)
- **Pull:** `llava:13b` triggered via Ollama API on workstation — 7.4 GB, in progress
- **Tag list:** 35 adult content act tags pre-configured ✅
- **Markers:** `CREATE_MARKERS = True` — creates timestamped scene markers ✅
- **Frame interval:** 80 seconds ✅

**Config file location:** `/mnt/container/appdata/stash/plugins/community/ahavenvlmconnector/haven_vlm_config.py`

**Next step — validate before bulk run:**
1. Wait for `llava:13b` pull to complete: `curl http://192.168.1.182:11434/api/tags | grep llava`
2. In Stash: tag 3 scenes with `VLM_TagMe`
3. Stash → Tasks → ahavenvlmconnector → "Tag Videos"
4. Check: are act tags appearing on those scenes? Are scene markers being created?
5. If yes → proceed to bulk tag all 2,930 scenes

### 1C: Wire Faster-Whisper to the Pipeline

Faster-Whisper (port 10300) is already on the stash-backend network alongside Stash. This is purpose-built placement — it was set up to process Stash content.

1. Confirm it's responding: `http://192.168.1.147:10300` (check the API)
2. Determine how it receives jobs — likely a REST API: `POST /asr` with audio file path
3. Test: send one scene's audio track → get transcript back
4. For JAV content: configure language detection (Japanese primary, English secondary)
5. Store transcripts as scene details or tags in Stash

**Usefulness:** For JAV content, Whisper transcription + Japanese NLP can:
- Identify studio watermarks spoken in audio
- Extract performer names from dialogue
- Classify content type by audio patterns

### 1D: Qdrant — Semantic Search Setup

Qdrant already has collections. Add a stash-content collection:

```bash
# Create collection for scene embeddings
curl -X PUT http://192.168.1.147:6333/collections/stash_scenes \
  -H 'Content-Type: application/json' \
  -d '{"vectors": {"size": 768, "distance": "Cosine"}}'
```

The goal: embed scene metadata (title, tags, performers, studio, description) as vectors so you can search "intimate JAV scene with experienced performer, morning setting" and get relevant results rather than relying on exact tags.

**This becomes valuable once tags are cleaned up in Phase 3.**

---

## Phase 2 — Performer Enrichment at Scale (Week 1)
*Get from 19% to 95%+ performer image coverage.*

### 2A: Validate First (1 performer test)

Before running bulk, confirm the pipeline works:

1. Stash → Tasks → actress_library → "Import Performer by Name" → `Marica Hase`
2. Check: aliases, birthdate, measurements, nationality populated
3. Stash → Tasks → actress_library → "Scrape Images for Performer" → `Marica Hase`
4. Check: images in `/data/performer_gallery/marica_hase/`
5. Check: face detection scores in Stash logs (Settings → Logs)
6. Check: best image selected (if update_stash_profile was true)

If this works end-to-end → proceed to bulk.

### 2B: Update config.ini — Enable Profile Updates

Edit `config.ini` locally, then sync to server:

```ini
# Change:
update_stash_profile = false
# To:
update_stash_profile = true

# Also increase batch size for the burst run:
max_per_run = 100
```

Sync to server (once SSH is restored):
```powershell
$key = "C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management\.codex-ssh\unraid_2026_ed25519"
scp -i $key "C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management\stash-plugins\config.ini" "root@192.168.1.147:/mnt/container/appdata/stash/stash-plugins/config.ini"
```

### 2C: Burst Run — Weekend Operation

With `max_per_run = 100`:
- Each run: ~100 performers
- 1,541 to process ÷ 100 = ~16 runs
- Target: run 2× per hour for 8 hours = done in a day

**Saturday plan:**
```
10am: Start Run 1 → verify it's working after 10 min
10am–6pm: Run manually every 30 min (or use n8n to automate the repetition)
Evening: Check results, fix any session expiry issues
Sunday: Run "Rebuild Alias Index" and review
```

**Watch for:** JavDB/JavLibrary session cookie expiry. If scraping shows 0 images from those sources, refresh cookies.

### 2D: Cookie Refresh Process

When sessions expire:
1. Open browser → navigate to javdb.com → log in
2. DevTools (F12) → Application → Cookies → copy `_jdb_session` value
3. Update `config.ini` → `[javdb]` → `session = NEW_VALUE`
4. Sync to server
5. Repeat for JavLibrary

---

## Phase 3 — Scene Metadata & AI Tagging (Week 2)
*Clean up the 11% unmatched scenes and apply AI tags to everything.*

### 3A: Identify the 308 Unmatched Scenes

Stash → Scenes → filter "StashID: None":
- First: try Auto Tag (Stash Tasks → Auto Tag → Scenes) — filename-based matching
- For remaining: run sceneMatcher plugin (v1.1.0) — it's installed and designed for this
- Manual fallback: search by scene code (e.g., ABP-857 → JavDB → match to StashDB entry)

**Japanese scene codes** (e.g., IPX-123, SSNI-456) almost always have StashDB entries. The miss rate is usually: 
- Uncensored JAV (no standard code) → use dmm.co.jp or r18.com scraper
- Western scene from small studio → TPDB usually has it
- Homebrew/amateur content → accept as unscrapable, tag manually

### 3B: Fix Performer Gaps (196 scenes)

1. Stash → Scenes → filter "Performers: 0"
2. Run: Tasks → Auto Tag → Performers
3. For remainder: the sceneMatcher + stashdb data will have performer info — re-scrape those scenes

### 3C: Fix Studio Gaps (191 scenes)

1. Tasks → Auto Tag → Studios
2. For unmatched: check filename — most JAV filenames embed studio code (ABP = Attackers, SSNI = S1 No.1 Style, etc.)
3. studioManager plugin (v0.1.0) — installed, may help with bulk studio assignment

### 3D: AI Tagging — Full Library Run

Once ahavenvlmconnector is validated (Phase 1B):

```
Stash → Tasks → ahavenvlmconnector → "Tag Videos"
```

This analyzes video thumbnails/frames via llava and generates tags. Expected output:
- Content type tags (solo, couples, group, etc.)
- Act tags (specific activities)
- Setting tags (indoor, outdoor, studio, etc.)
- Attribute tags (costumes, props, setting details)

**Volume:** 2,930 scenes. Timing depends on where inference runs:
- Workstation RTX (24 GB) at llava:13b: ~8–12s per scene → ~10–14 hours. Run Friday night, done Saturday morning.
- Unraid GTX 1660 Ti (6 GB) at llava:7b q4: ~15–20s per scene → ~16–24 hours. Slow and ties up Unraid GPU.

**Use the workstation.** It's faster, better quality, and doesn't block Jellyfin transcoding on Unraid.

**Tag review:** After the run, review a sample of 50 scenes — check tag accuracy. Tune the plugin's system prompt if needed.

### 3E: Faster-Whisper Audio Analysis

For JAV content specifically, run Faster-Whisper on the audio track:
- Language: Japanese
- Output: subtitle file (.srt) or transcript text
- Use case 1: Japanese subtitles for non-Japanese speakers
- Use case 2: Extract studio watermark text spoken at start/end
- Use case 3: Performer name extraction from spoken dialogue

The container is already on stash-backend network. Build an n8n workflow to trigger it on newly imported scenes.

---

## Phase 4 — n8n Automation (Week 2–3)
*Stop doing things manually. n8n is already running at port 5678 — use it.*

### The Core Workflow: Scene Lifecycle

Create this n8n workflow:

```
TRIGGER: Stash webhook (scene.create or scene.update)
    ↓
NODE: Wait 2 min (let file settle)
    ↓
NODE: Stash GraphQL — get scene details
    ↓
NODE: IF scene has no StashDB ID
    → Branch A: POST to Stash scrape endpoint (JavDB/TPDB/StashDB via CDP)
    ↓
NODE: IF scene has performers with no images
    → Branch B: trigger actress_library "Scrape Images for Performer" for each
    ↓
NODE: POST to Faster-Whisper API (http://192.168.1.147:10300)
      audio transcription → store as scene details
    ↓
NODE: POST to WORKSTATION Ollama (http://192.168.1.182:11434)
      llava:13b vision analysis → generate content tags
      → Write tags back to Stash via GraphQL mutation
    ↓
NODE: Call tdarr API — queue scene for transcode check
    ↓
NODE: Call mcMetadata — trigger NFO generation for this scene
    ↓
NODE: Notify — "Scene processed: {title}"
```

**n8n first steps:**
1. Navigate to `http://192.168.1.147:5678` in browser — check if workflows already exist
2. The n8n API requires an `X-N8N-API-KEY` header — set this up in n8n Settings → API
3. Once API key is created, update this plan with it

**n8n credential store (set these up first):**
| Credential | Value |
|------------|-------|
| Stash API key | `eyJhbGci...GeGebjc` (from config.ini) |
| Whisparr API key | `6c3aff48df4d40da8a41cfe57f97cc03` |
| Ollama URL | `http://192.168.1.182:11434` ← workstation |
| Stash GraphQL | `http://192.168.1.147:9999/graphql` |
| n8n API key | [create in n8n Settings → API, then add here] |

### Supporting Workflows

**Workflow 2: Daily Maintenance**
```
TRIGGER: Cron 2:00 AM daily
→ actress_library "Enrich All Performers" (max_per_run batches until done)
→ stash-scheduler tasks
→ recyclarr sync (quality profiles)
→ Rebuild Alias Index
```

**Workflow 3: Whisparr Queue Monitor**
```
TRIGGER: Cron every 30 min
→ GET Whisparr /api/v3/queue
→ IF items with sizeleft=0 AND status=downloading for >60min
    → POST Whisparr manual import trigger
→ IF failed items > 10
    → Send notification
```

**Workflow 4: Session Cookie Health Check**
```
TRIGGER: Cron weekly
→ Test JavDB scraper on known URL
→ IF fails → send notification "JavDB cookie expired — rotate"
→ Same for JavLibrary
```

### n8n ↔ Stash Integration

Stash supports webhooks. Enable them:
- Stash → Settings → Tasks → add webhook URL pointing to n8n
- Events to listen to: `Scene.Create`, `Scene.Update`, `Performer.Create`

Use Stash's GraphQL for all data operations from n8n.

---

## Phase 5 — Media Server Excellence (Week 3)
*Clean output to Jellyfin (adult) and Plex (mainstream).*

### 5A: The Media Server Split

**Jellyfin (port 8096) = Adult Library**
- Library paths: `/data/movies`, `/data/scenes`  
- NFO metadata from mcMetadata
- Performer images exported by mcMetadata
- No cloud dependency, no content restrictions
- Hardware transcoding via GPU

**Plex (port 32400) = Mainstream Library**
- Movies, TV shows, music, books
- Kometa handles artwork and collections
- Tautulli analytics
- Keep for remote access (better apps)

This is cleaner than mixing everything in one server.

### 5B: mcMetadata Configuration

Plugin v1.4.0 is installed. Configure for Jellyfin output:

In Stash → Plugins → mcMetadata → Settings:
- NFO format: Jellyfin/Kodi compatible
- Output structure: `/data/scenes/{filename}/{filename}.nfo`
- Performer images: `/data/performers/{performer_name}/folder.jpg`
- File naming template: `{studio} - {date} - {title} [{resolution}]`

After config:
1. Run "Bulk Update Performers" → exports all performer photos
2. Run "Bulk Update Scenes" → generates all NFOs and renames files
3. Jellyfin → Dashboard → Libraries → Scan All Libraries

### 5C: Kometa for Plex (Mainstream Only)

Kometa is running but its target needs to be restricted to mainstream libraries only. Edit Kometa's config to exclude adult library paths. This prevents it from mangling Stash-managed content.

### 5D: GPU Transcoding

Configure Jellyfin hardware transcoding:
- Jellyfin → Admin → Playback → Hardware Acceleration → NVIDIA NVENC
- This uses the same GPU as ComfyUI/Faster-Whisper — monitor VRAM usage

**GPU conflict map — GTX 1660 Ti (6 GB total):**
| Service | VRAM | Can run simultaneously? |
|---------|------|------------------------|
| Jellyfin NVENC | ~500 MB | ✅ Yes — minimal |
| Faster-Whisper | ~1–2 GB | ✅ Yes — manageable |
| llava:7b q4 inference | ~4.1 GB | ⚠️ Only if nothing else is active |
| ComfyUI (image gen) | 4–6 GB | ❌ Mutually exclusive with llava |
| tdarr NVENC | ~500 MB | ✅ Yes — minimal |

**Rule:** Never run ComfyUI image generation while AI tagging is in progress. Schedule them apart. The 6 GB is tight — this is the single strongest argument for a GPU upgrade long-term.

**Stagger strategy (n8n enforces this):**
- AI tagging runs overnight via workstation Ollama (no Unraid VRAM needed)
- Tdarr transcoding runs daytime (low VRAM)
- ComfyUI runs on-demand only

### 5E: Transcoding — Tdarr (DECISION MADE: Keep Tdarr)

**FileFlows audit result (2026-05-10):** FileFlows on z4-media-02 has 1 library configured but LastScanned = NEVER. All 21 flows are disabled. Zero active processing. It has never done any work. **Decision: Keep Tdarr, decommission FileFlows.**

**Tdarr configuration (Unraid, port 8264/8265):**
- Configure source libraries: `/mnt/itv/adult/` (8.5 TB adult content)
- Codec target: HEVC/H.265 NVENC (uses GTX 1660 Ti)
- Audio: AAC passthrough or normalize to AAC 192kbps
- Bitrate targets: 4K→15 Mbps, 1080p→5 Mbps, 720p→2 Mbps
- Check UI at `:8265` to see existing library config before adding new ones

**z4-media-02 as Tdarr remote node (after SSH access):**
- Add machine as CPU-only Tdarr worker (3 runners)
- CPU encoding is slower than NVENC but offloads work from Unraid
- First need: SSH key added, then configure Tdarr node agent on z4-media-02

**Note on subtitle-worker:** z4-media-02 has a service at port 8100 referenced in FileFlows "Subtitle Worker Async JA" flow. This appears to be a subtitle/transcription service. After FileFlows is decommissioned, investigate this service independently — it may complement Faster-Whisper for Japanese content.

**Storage impact:** H.265 at target rates compresses H.264 originals 40–60%. On 8.5 TB adult library → frees 3–5 TB on itv pool.

---

## Phase 6 — Semantic Search (Month 2)
*Make the library discoverable by meaning, not just tags.*

### 6A: Embed Everything in Qdrant

Use Ollama to generate text embeddings (use llama3.2:3b — it's fast and small):

For each scene in Stash:
1. Build a text document: `"{title}. Studio: {studio}. Performers: {names}. Tags: {tags}. Description: {details}."`
2. POST to Ollama embed endpoint: `POST /api/embeddings` with model=llama3.2:3b
3. Upsert vector to Qdrant collection `stash_scenes` with scene ID as payload

n8n workflow handles this automatically when a scene is updated.

### 6B: Search Interface

Two options:
1. **Open-WebUI RAG** (already running at 3001): Configure it to query Qdrant's stash_scenes collection. Allows natural language queries.
2. **Custom n8n workflow**: Accept query → embed it → Qdrant search → return top 10 scene IDs → display in a webpage

**Query examples that become possible:**
- "intimate solo Japanese scene in natural lighting"
- "English-speaking performer, studio setting, 2024"
- "outdoor scene with costume element"

### 6C: SearXNG Integration

SearXNG (port 8888) is running. It can be configured to search Qdrant as a custom engine, making it a unified search across all content types on the server.

---

## Software Changes

### Kill These (confirmed)

| Software | Reason | Action |
|----------|--------|--------|
| llava:7b-v1.5-q2_K | 2-bit quantization — junk quality, replaced by q4 | `docker exec ollama ollama rm llava:7b-v1.5-q2_K` |
| OpenProject (port 5683) | Misconfigured (Invalid host_name), almost certainly unused | `docker stop OpenProject && docker rm OpenProject` |
| qwen3.5:4b (Unraid Ollama) | Redundant — workstation has better 14B and 32B models | `docker exec ollama ollama rm qwen3.5:4b` — only if not used by open-webui |
| missingScenes plugin | Disabled — verify use case | Delete if nothing depends on it |
| **FileFlows (z4-media-02)** | **CONFIRMED IDLE** — 1 library configured, never scanned, all flows disabled. Redundant with Tdarr. | Stop FileFlows service on z4-media-02. Keep machine — add as Tdarr remote node. Keep subtitle-worker (:8100) separately. |

**AIOverhaul plugin — hold:**
- Plugin installed in Stash, configured with API key, but backend (port 4153) is NOT running
- Don't remove yet — investigate if OpenClaw (port 18789) is the intended backend
- If AIOverhaul + OpenClaw form a more powerful pipeline than ahavenvlmconnector, may be worth setting up

### Add These

| Software | Purpose | Where |
|----------|---------|-------|
| llava:7b-v1.5-q4_K_M | Better local vision model (fits 6 GB) | `docker exec ollama ollama pull llava:7b-v1.5-q4_K_M` on Unraid |
| llava:13b | Primary tagging model — high quality | ❓ **Status unknown** — pull triggered 2026-05-10, workstation port 11434 unreachable from sandbox (firewall). Verify from Unraid: `curl http://192.168.1.182:11434/api/tags \| grep llava` |
| nomic-embed-text | Fast text embedding for Qdrant | `ollama pull nomic-embed-text` on Unraid (1.5 GB, fits easily) |

### Keep Exactly As-Is (confirmed working)

stash, stash-cdp, whisparr-v3, prowlarr, flaresolverr, n8n, Qdrant, Grafana, Prometheus, cadvisor, binhex-qbittorrentvpn (VPN critical), sabnzbd, recyclarr, Jellyfin, filemonitor, Faster-Whisper-Nvidia, ComfyUI-Nvidia-Docker, immich_pro, audiobookshelf

**Unraid Ollama:** Keep running for local tasks (moondream fast-checks, nomic-embed-text for Qdrant). NOT for heavy vision inference.  
**Workstation Ollama:** Primary AI inference endpoint for ahavenvlmconnector and n8n workflows.

### Keep Exactly As-Is

stash, stash-cdp, whisparr-v3, prowlarr, flaresolverr, n8n, Qdrant, Ollama, Grafana, Prometheus, binhex-qbittorrentvpn (VPN is important), sabnzbd, recyclarr, tdarr, Jellyfin, filemonitor

### Consider Replacing

| Current | Replace With | Why |
|---------|-------------|-----|
| Kometa (Plex-focused) | No replacement | If going Jellyfin-primary, Kometa loses most of its value. Jellyfin has native collection management. |
| Plex (for adult content) | Jellyfin already does this | Run Plex for mainstream only |

---

## Hardware Assessment & Recommendations

### Confirmed Hardware — Unraid (192.168.1.147)
- **CPU:** i9-12900K — 16 cores / 24 threads / 5.2 GHz. No bottleneck here.
- **RAM:** 62 GB. Fine for 38 containers. No swap — normal for Unraid.
- **GPU: GTX 1660 Ti (6 GB VRAM)** — this IS the bottleneck. See below.
- **NVMe:** 1.9 TB at 54% used. Watch this — Qdrant + model weights will grow.
- **ZFS pools:** dtv at 83% is a problem. ZFS slows significantly above 80%.

### Confirmed Hardware — Workstation (192.168.1.182)
- **GPU:** NVIDIA RTX with ≥ 24 GB VRAM (runs 32B model). Most likely RTX 4090.
- **Ollama:** Already running, accessible from Unraid. This is your AI powerhouse.
- **Strategic role:** All serious inference happens here. Unraid GPU handles transcoding only.

### Confirmed Other Machines
- **z4-media-01 (192.168.1.10):** Linux NFS server. Storage role only. No GPU, no services beyond NFS. SSH access needed to see what it's exporting.
- **z4-media-02 (192.168.1.139):** Linux + FileFlows v26.01, 3 runners. Dedicated transcoding node. Hardware unknown (need SSH access).

### GPU Bottleneck — Unraid GTX 1660 Ti

**The 6 GB limit affects everything on Unraid:**

| Workload | VRAM needed | Fits? |
|----------|-------------|-------|
| Jellyfin NVENC | ~0.5 GB | ✅ |
| Faster-Whisper | ~1–2 GB | ✅ |
| Tdarr NVENC | ~0.5 GB | ✅ |
| llava:7b-v1.5-q4_K_M | ~4.1 GB | ✅ alone |
| ComfyUI (SD generation) | 4–6 GB | ✅ alone, ❌ with llava |
| llava:13b+ | ~8+ GB | ❌ Won't fit |

**Solution already in place:** Route heavy AI inference to workstation (24 GB). Unraid GPU handles only: NVENC transcoding + Faster-Whisper + moondream (tiny checks). This is the right architecture.

### GPU Upgrade Recommendation

**Short term (free):** Route AI to workstation. Done. Works now.

**Long term (optional):** If you want to run 14B+ vision models locally on Unraid without involving the workstation — upgrade to RTX 3090 (24 GB, ~$500 used) or wait for RTX 5000 series to bring 3090 prices lower. The i9-12900K has PCIe 5.0 — any modern GPU will work.

Do NOT upgrade to RTX 3080 10 GB — the step from 6 GB to 10 GB isn't enough. 24 GB is the target.

### Storage Outlook — REVISED

| Pool | Free | Concern |
|------|------|---------|
| dtv | 50 TB | ⚠️ At 83% — ZFS perf degrading now |
| itv | 19 TB | Comfortable |
| photography | 19.5 TB | Comfortable |
| torrent | 4.5 TB | Comfortable |
| NVMe | ~910 GB | Watch as models/Qdrant grow |

**dtv at 83% needs action now.** Options:
1. Run Tdarr on mainstream content first — H.265 recompression will free 30–50 TB from the domestic library
2. Add drives to dtv pool (Unraid makes this easy — just add and resize ZFS vdev)
3. Archive older content to cold storage (z4-media-01 NFS if it has space)

**Recommendation:** Move Ollama model weights from NVMe to itv pool to free NVMe space:
```bash
# Move models to ITV pool
mv /mnt/container/appdata/ollama/models /mnt/itv/ai-models
ln -s /mnt/itv/ai-models /mnt/container/appdata/ollama/models
```

---

## Monitoring & Maintenance

### Grafana Dashboards to Build

Grafana (port 3000) + Prometheus (9090) + cadvisor (8082) are all running. Build dashboards for:

1. **Library Health:** Performers with/without images (% over time), scenes with/without tags, queue depth
2. **GPU Utilization:** VRAM usage, inference queue, transcoding jobs
3. **Storage:** Pool usage trends, Tdarr compression savings
4. **Pipeline:** n8n job success/fail rates, Whisparr queue health

Query cadvisor via Prometheus for container metrics. Add Stash as a Prometheus target by scraping the GraphQL API via a custom exporter (n8n can push metrics to Prometheus pushgateway).

### Weekly Maintenance Checklist (automated via n8n)

- [ ] recyclarr sync — ensure quality profiles match TRaSH guides
- [ ] JavDB/JavLibrary session test
- [ ] Qdrant index optimization
- [ ] Stash database backup
- [ ] Grafana alert review
- [ ] Ollama model update check

---

## Execution Timeline

```
WEEK 1: STABILIZE + VALIDATE (updated 2026-05-13)
  ✅ Done:  0B SSH restore, 0C identify unknown servers, 1B ahavenvlmconnector config (endpoint + model fixed)
  ✅ Done:  SSH keys added to z4-media-01 (.10) and z4-media-02 (.139)
  ✅ Done:  z4-media-01 confirmed as NFS CLIENT (not server); z4-media-02 has Quadro P1000 (NVENC capable)
  ✅ Done:  FileFlows decision made — keep Tdarr, decommission FileFlows
  ✅ Done:  Kometa confirmed safe (mainstream libraries only, not touching adult content)
  ✅ Done:  0D CDPPath — already set to stash-cdp hostname (no change needed, confirmed 2026-05-13)
  ✅ Done:  0F filemonitor — host-level inotifywait watcher deployed (2026-05-13). Plugin can't run in Docker.
            Script: /boot/config/scripts/stash-filemonitor.sh. Watching: /mnt/user/adult/{movies,scenes},
            /mnt/user/torrents/Complete/xxx, /mnt/user/torrents/usenet/_complete/xxx.
            Starts on boot via /boot/config/go. Triggers Stash metadataScan on new video files (30s debounce).
  ✅ Done:  1A llava:7b-v1.5-q4_K_M pulled on Unraid (4.7 GB). llava:7b-v1.5-q2_K deleted (2026-05-13).
  ✅ Done:  1B Workstation Ollama confirmed reachable from Unraid at http://192.168.1.182:11434. Models:
            llava:13b (8 GB, Q4_0) ✅, qwen2.5:32b (19.8 GB), qwen2.5:14b-instruct (9 GB). OLLAMA_HOST fix already applied.
  ⚠️ Partial: 0A Whisparr — queue at 971 (was 1,001); still needs bulk clearing + root cause fix
  ✅ Done:  0E ai_tagger / AIOverhaul directory check — both live community plugin dirs are effectively empty placeholders; neither is a viable tagging path today
  ✅ Done:  2A single performer validation and config promotion — `update_stash_profile=true`, `max_per_run=100` validated live on Marica Hase
  ❌ Pending: 2C burst enrichment run

WEEK 2: AUTOMATE
  Day 8:  1C wire Faster-Whisper, 1D Qdrant collection setup
  Day 9:  4A build n8n core scene lifecycle workflow
  Day 10: 4B build maintenance workflows
  Day 11: 3A–3C scene metadata cleanup (Auto Tag run)
  Day 12–14: 3D AI tagging full library run (overnight)

WEEK 3: MEDIA SERVER
  Day 15: 5A split Jellyfin/Plex responsibilities
  Day 16: 5B mcMetadata bulk update → Jellyfin scan
  Day 17: 5D GPU transcoding setup in Jellyfin
  Day 18: 5E Tdarr pipeline config
  Day 19–21: validate end-to-end with 10 new scenes

MONTH 2: SEARCH + MONITORING
  Week 5: 6A–6B Qdrant embeddings + search interface
  Week 6: Grafana dashboards
  Week 7: Tune AI tagging prompts based on 1000-scene results
  Week 8: Full library audit — measure against target metrics

TARGET METRICS (Month 2 end):
  Performers with images: 1,897 / 1,897 (100%)
  Scenes with AI tags: 2,930 / 2,930 (100%)
  Scenes with NFO in Jellyfin: 2,930 / 2,930 (100%)
  New scene → fully processed: < 15 min automatic
  Manual intervention required: 0 (for standard content)
```

---

## Config Files to Update

| File | Change | When |
|------|--------|------|
| `stash-plugins/config.ini` | `update_stash_profile = true`, `max_per_run = 100` | Phase 2B |
| Stash Settings → Scraping | `scraperCDPPath = http://stash-cdp:9222/json/version` | Phase 0D (now) |
| ahavenvlmconnector settings | ✅ **DONE** — URL: `http://192.168.1.182:11434`, model: `llava:13b` (Q4_0, confirmed reachable from stash container) | Phase 1B |
| n8n credentials | Stash API key, **Ollama URL: `http://192.168.1.182:11434`**, Whisparr API key: `6c3aff48...cc03` | Phase 4A |
| tdarr config | NVENC codec, bitrate targets, paths; or FileFlows migration | Phase 5E |
| mcMetadata config | Jellyfin paths, NFO format, naming template | Phase 5B |
| Kometa config | Remove adult library paths — restrict to mainstream only | Phase 5C |
| Workstation Ollama | ✅ DONE — `llava:13b` present and reachable | Phase 1B ✅ |

---

## Open Questions (Update This List)

**Answered:**
- [x] ~~What GPU is in Unraid?~~ **GTX 1660 Ti — 6 GB VRAM** (confirmed via nvidia-smi)
- [x] ~~What is running at 192.168.1.10?~~ **z4-media-01 — NFS CLIENT, NOT server** (mounts all media from Unraid .147; 233GB root + 477GB scratch /dev/md1p1; no exportfs; confirmed 2026-05-11)
- [x] ~~What is running at 192.168.1.139?~~ **z4-media-02 — Linux with FileFlows v26.01 + subtitle-worker on :8100; GPU = NVIDIA Quadro P1000 (4GB, NVENC capable); Ubuntu 22.04; SSH key added 2026-05-11**
- [x] ~~SSH access to Unraid?~~ **✅ Working** (`claude-cowork-2026` key, confirmed)
- [x] ~~Is ahavenvlmconnector configured or blank?~~ **BLANK** — no Ollama URL or model in config.yml
- [x] ~~What is OpenClaw (port 18789)?~~ **"OpenClaw Control"** — AI gateway/CLI tool (openclaw.ai), created 2026-05-07, HTTP 200, web UI reachable
- [x] ~~Is n8n empty?~~ **Running + healthy** — API is auth-required (needs X-N8N-API-KEY header). Workflow count unknown without auth.
- [x] ~~Is Tdarr processing or idle?~~ **Running** — v2.71.01, uptime 2+ days. Library/queue status not exposed at probed endpoints.
- [x] ~~Is Kometa hitting adult library paths?~~ **NO** — Kometa config confirmed: mainstream libraries only (Movies, TV Shows, Animation, Anime). Safe.
- [x] ~~FileFlows active workflows or empty?~~ **EFFECTIVELY IDLE** — 1 library "Manually Added" configured but LastScanned = NEVER. All 21 flows disabled. Decision: **keep Tdarr, decommission FileFlows.**
- [x] ~~What is the AIOverhaul plugin / port 4153?~~ **Backend is NOT running** — port 4153 is closed. Plugin is configured (API key set) but dead. AIOverhaul needs a separate backend service on :4153.

- [x] ~~Workstation Ollama reachable?~~ **YES from both Unraid host and stash container** — confirmed 2026-05-13. llava:13b (8 GB Q4_0), qwen2.5:32b, qwen2.5:14b-instruct all present. OLLAMA_HOST already set to 0.0.0.0.
- [x] ~~llava:7b-v1.5-q4_K_M on Unraid GPU?~~ **CONFIRMED** — loads 4.2 GB into GTX 1660 Ti, leaving 736 MiB free. q2_K deleted.
- [x] ~~ahavenvlmconnector endpoint reachable from stash container?~~ **YES** — docker exec stash can reach 192.168.1.182:11434. model_id=llava:13b set correctly.
- [x] ~~filemonitor in Docker?~~ **Impossible** — plugin explicitly refuses Docker. Replaced with host-level inotifywait watcher. Script at /boot/config/scripts/stash-filemonitor.sh. Live-tested: file drop → Stash scan task #28 fired in <1s.

**Still open:**
- [x] ~~What is the ai_tagger plugin?~~ **Live directory under `/mnt/container/appdata/stash/plugins/community/ai_tagger` is effectively empty aside from `__pycache__`**. Not a viable installed plugin path today.
- [x] ~~What is AIOverhaul's backend?~~ **Still no working backend, and the live community plugin directory is effectively empty**. Not a viable installed plugin path today.
- [ ] **n8n workflow count + API key** — Open `http://192.168.1.147:5678` — how many workflows exist? Create API key in n8n Settings → API.
- [ ] **Subtitle-worker at 192.168.1.139:8100** — What is this service? Can it do Japanese transcription? Survives FileFlows decommission.
- [ ] **Tdarr libraries configured** — Check UI at `:8265`. How many libraries? What paths? What codec targets?
- [ ] **Exact workstation GPU model** — `nvidia-smi` in PowerShell confirms model (likely RTX 4090).
- [ ] **Is OpenProject actually used?** — Misconfigured (Invalid host_name). Candidate for removal.

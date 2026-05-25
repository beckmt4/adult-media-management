# Container Migration Analysis — Unraid Workload Distribution

**Date:** 2026-05-14  
**Purpose:** Identify Unraid containers suitable for relocation to z4 worker nodes (z4-media-01, z4-media-02)  
**Constraint:** 1Gb network interfaces (~250 MB/s theoretical max) limit bandwidth-heavy workloads

---

## Network Topology Context

| Node | IP | Role | Network | GPU | Storage | Use Case |
|------|----|----|---------|-----|---------|----------|
| **Unraid (primary)** | 192.168.1.147 | Master server | Direct to storage | GTX 1660 Ti 6GB | 450TB ZFS | Storage hub, encoding, AI inference |
| **z4-media-01** | 192.168.1.10 | NFS client | 1Gb (250MB/s) | None | 233GB local + 477GB scratch | Temp processing, metadata ops |
| **z4-media-02** | 192.168.1.139 | Media processor | 1Gb (250MB/s) | NVIDIA P1000 4GB | SSD (local) | Transcode, low-bandwidth ops |
| **Workstation** | 192.168.1.182 | AI node | 1Gb (250MB/s) | RTX 4090 24GB | SSD (local) | Large model inference |

---

## Container Classification by Bandwidth Requirements

### 🟢 **TIER 1: Low Bandwidth ← MIGRATE TO Z4**
*These services read/write small files, metadata, configs, or make infrequent API calls. Network is NOT the bottleneck.*

#### Orchestration & Automation
- **n8n** (workflow engine)
  - Reads: Webhook payloads (~100KB), scene IDs, metadata queries
  - Writes: Execution logs, state
  - Storage touch: Minimal (queries Stash via API, doesn't store video)
  - **Candidate:** z4-media-01 (low CPU, low memory, any storage)
  - **Rationale:** Pure orchestration; all media work delegated via HTTP/GraphQL

- **Qdrant** (vector embeddings)
  - Reads: Embedding queries (~1-10MB typical)
  - Writes: New embeddings (~1KB each)
  - Storage: ~50-500MB for embeddings (SSD preferred, not critical bandwidth)
  - **Candidate:** z4-media-01
  - **Rationale:** Semantic search backend; never touches actual video; CPU-constrained, not I/O constrained

#### Metadata & Discovery
- **Navidrome** (music server, if running)
  - Reads: Track metadata, index queries
  - Writes: Transcoding (streaming) via HTTP, not direct file access
  - **Candidate:** z4-media-01
  - **Rationale:** Serves metadata/streams over HTTP; local SSD cache handles bandwidth

- **Jellyfin/Emby** (media server, if running)
  - ⚠️ **Exception:** If running transcoding locally, stays on Unraid (see TIER 2)
  - If metadata-only, can move to z4
  - **Candidate:** z4-media-01 (metadata mode only)

#### Development & Logging
- **Portainer** (Docker management UI)
  - Reads: Container state, logs
  - Writes: Minimal (UI actions)
  - **Candidate:** z4-media-01
  - **Rationale:** Pure orchestration; doesn't touch user data

- **Prometheus** + **Grafana** (monitoring, if running)
  - Reads: Scrape endpoints (~1KB per scrape)
  - Writes: Time-series metrics (~100 bytes per event)
  - **Candidate:** z4-media-01
  - **Rationale:** Monitoring backend; network load negligible

- **Loki** (log aggregation, if running)
  - Reads: Log streams
  - Writes: Indexed logs
  - **Candidate:** z4-media-01
  - **Rationale:** Append-only; no high-bandwidth requirements

- **ELK Stack** (Elasticsearch, Kibana, if running)
  - Reads: Index queries (~MB range, not GB)
  - Writes: Logs (~KB per event)
  - **Candidate:** z4-media-01
  - **Rationale:** Search backend for logs, not video

#### APIs & Utilities
- **Plex/Kaleidescape APIs** (if running)
  - Reads: Metadata queries
  - Writes: Watch history, state
  - **Candidate:** z4-media-01
  - **Rationale:** API gateway; proxies requests, doesn't handle video

- **Home Assistant** (if running)
  - Reads: Sensor queries, state
  - Writes: Automations, entity updates
  - **Candidate:** z4-media-01
  - **Rationale:** Orchestration; zero direct media access

- **Node-RED** (if running)
  - Similar to n8n; low bandwidth
  - **Candidate:** z4-media-01

---

### 🟡 **TIER 2: Medium/Conditional — May Migrate with Caveats**
*These services have network dependencies but might work across 1Gb if carefully configured.*

#### Transcoding with GPU
- **tdarr** (distributed transcode)
  - If using z4-media-02 as remote GPU node (NVENC): **KEEP THE QUEUE ON UNRAID**, move only the remote agent to z4-media-02
  - If transcode locally on Unraid: **STAY ON UNRAID** (video ingestion → direct encode → return)
  - **Decision:** Remote agent on z4-media-02 ✅, queue/distribution on Unraid ❌
  - **Rationale:** Source video stays on Unraid NFS; GPU does encoding work at z4; result streams back (~1-2 Mb/s per stream, acceptable)

- **Handbrake** / **FFmpeg containers** (if running standalone)
  - Reads: Video files (GB per job)
  - Writes: Encoded output (smaller, still GB range)
  - **Decision:** STAY ON UNRAID
  - **Rationale:** Video ingestion too heavy for 1Gb link

#### Metadata Scraping & Enrichment
- **actress_library plugin** (Stash enrichment)
  - Reads: Performer data queries (~100KB per performer)
  - Writes: Tags, metadata (KB per performer)
  - **Current Status:** Already running on Unraid; ~1,897 performers, ~32 hours at ~4/15min rate
  - **Decision:** STAY ON UNRAID (already optimized)
  - **Rationale:** Can stay, but doesn't need to; move only if Unraid load is critical

- **Stable Diffusion / ComfyUI** (if running)
  - Depends on: Input image source (local? remote?)
  - If generating from scratch: Move to workstation (RTX 4090)
  - If processing Stash scenes: STAY ON UNRAID or use workstation
  - **Decision:** MOVE TO WORKSTATION if GPU bottleneck is issue
  - **Rationale:** RTX 4090 >> GTX 1660 Ti; Ollama already routed there

---

### 🔴 **TIER 3: High Bandwidth ← KEEP ON UNRAID**
*These services need sub-millisecond access to large video libraries. Must stay local.*

#### Storage & Serving
- **Stash** (database + API server)
  - Reads: SQL queries (results), scene files (for scraping/tagging)
  - Writes: Updated metadata, thumbnails
  - **Decision:** STAY ON UNRAID
  - **Rationale:** All 38 containers query Stash API; moving it behind 1Gb link bottlenecks the entire system

- **NFS Server** (Unraid native)
  - Reads/Writes: All stored media (GB/s potential)
  - **Decision:** STAY ON UNRAID
  - **Rationale:** Physical location of data; cannot move

- **Plex Media Server** (if running locally for streaming)
  - Reads: Video files for playback/transcoding
  - **Decision:** STAY ON UNRAID (or move transcoding to z4 if hybrid)
  - **Rationale:** Local video access; transcoding might delegate to z4-media-02 via NVENC

#### AI Inference (Large Models)
- **Ollama** (if running locally)
  - Current setup: On workstation (192.168.1.182) RTX 4090
  - Models: qwen2.5:32b (too large for Unraid GTX 1660 Ti)
  - **Decision:** STAY ON WORKSTATION
  - **Rationale:** Unraid GPU too small; workstation already optimized

- **LlamaCPP** / **vLLM** (if running)
  - **Decision:** STAY ON UNRAID or move to workstation depending on model size
  - 7B models: Can stay on Unraid
  - 14B+ models: Move to workstation

#### Vision & Audio Processing
- **Faster-Whisper** (transcription)
  - Reads: Audio files (extracted from video)
  - Writes: SRT/VTT transcripts (much smaller)
  - **Decision:** STAY ON UNRAID
  - **Rationale:** Processes every scene; tight integration with Stash; local access critical for batch jobs

- **ComfyUI / Ollama Vision** (scene analysis)
  - If on Unraid (7B models): STAY
  - If on workstation (13b+ models): Already routed there
  - **Decision:** STAY WHERE DEPLOYED

#### Search & Indexing
- **Meilisearch** / **Opensearch** (if running)
  - Reads: Indexed documents (~KB per query)
  - Writes: New documents for indexing
  - **Decision:** CAN MOVE if not real-time (z4-media-01), but typically STAYS for performance
  - **Rationale:** Query latency matters for UX; keep near Stash

---

## Migration Plan

### **Phase 1: Immediate Moves (Low Risk)**
*These can move immediately with zero performance impact.*

| Container | Current | Target | Effort | Risk | Notes |
|-----------|---------|--------|--------|------|-------|
| n8n | Unraid | z4-media-01 | 15 min | Very Low | Export workflow, change endpoint, re-import; Stash still at .147 |
| Qdrant | Unraid | z4-media-01 | 15 min | Very Low | Backup embeddings, copy volume, reconfigure endpoint; n8n points to new IP |
| Portainer | Unraid | z4-media-01 | 10 min | Very Low | Pure orchestration; can run anywhere |
| Prometheus/Grafana | Unraid | z4-media-01 | 20 min | Low | Redirect scrape endpoints; time-series data can be migrated |

**Network Impact:** z4-media-01 sees only small API calls to Stash; well under 1Gb capacity.

### **Phase 2: Conditional Moves (Medium Complexity)**
*Requires testing and configuration; consider only if Unraid load is critical.*

| Container | Consideration | Target | Effort | Risk |
|-----------|---|--------|--------|------|
| tdarr agent | If using remote transcode | z4-media-02 | 20 min | Medium |
| actress_library | If Stash load high | Keep on Unraid | - | N/A |

**Network Impact:** tdarr remote agents push encoded video back (1-2 Mbps per stream); acceptable on 1Gb link.

### **Phase 3: Not Recommended**
*Keep on Unraid regardless of load.*

- Stash (API bottleneck)
- Faster-Whisper (every scene depends on it)
- NFS server (physical storage location)
- Local Ollama >7B (GPU constraint, not network)

---

## Bandwidth Estimates (Post-Migration)

### Current State (All on Unraid)
- Unraid network: 38 containers, internal container-to-Stash: ~50-200 Mbps peaks
- Bottleneck: Storage I/O, not network

### Post-Phase-1 Migration
- Unraid network: Down to ~20-30 Mbps (Stash queries, Faster-Whisper, tdarr coordination)
- z4-media-01 to Unraid: ~5-10 Mbps (n8n metadata queries, Qdrant lookups)
- z4-media-02 to Unraid: ~30-50 Mbps if tdarr agent enabled (transcode return stream)
- **Total outbound from Unraid:** Still well under 1Gb link capacity (theoretical 250 MB/s)

---

## Implementation Checklist

### Pre-Migration
- [ ] Export all container volumes (n8n workflows, Qdrant embeddings)
- [ ] Document current container endpoint URLs (for other services to update)
- [ ] Backup Unraid configuration
- [ ] Test z4-media-01 and z4-media-02 stability under load

### Migration Steps
- [ ] Shut down n8n on Unraid
- [ ] Copy n8n volume to z4-media-01
- [ ] Spin up n8n on z4-media-01
- [ ] Update n8n workflow endpoint references (if any external services call it)
- [ ] Repeat for Qdrant, Portainer, Prometheus/Grafana
- [ ] Verify all container-to-container communication still works

### Post-Migration Validation
- [ ] n8n webhook receives events and triggers workflows ✓
- [ ] Qdrant responds to search queries ✓
- [ ] All Stash API queries complete <500ms ✓
- [ ] tdarr queue shows z4-media-02 as available GPU node ✓

---

## Known Constraints

1. **z4-media-01 Limitations:**
   - No GPU (use for orchestration/metadata only)
   - 233GB root + 477GB scratch (local NFS client, NOT server)
   - 1Gb network (cannot serve video streams; only metadata/API responses)

2. **z4-media-02 Capabilities:**
   - NVIDIA P1000 4GB VRAM (NVENC capable; good for transcode acceleration)
   - 1Gb network (acceptable for transcode return stream, NOT for source video ingestion)
   - Viable as tdarr remote GPU node only

3. **Network Bottleneck:**
   - 1Gb link = ~125 MB/s sustained (accounting for overhead)
   - Acceptable for: API queries, metadata, logs, small files
   - NOT acceptable for: Video streaming, batch video processing without local GPU

---

## Recommendations Summary

✅ **Move immediately:**
- n8n → z4-media-01
- Qdrant → z4-media-01

⏳ **Move if needed for load reduction:**
- Portainer → z4-media-01
- Prometheus/Grafana → z4-media-01

❌ **Do NOT move:**
- Stash (API bottleneck)
- Faster-Whisper (per-scene processing)
- NFS (physical storage)
- GPU-dependent services >7B models (stay on Unraid or move to workstation)

---

## Alternative: VM-Based Architecture (Instead of Containers on Worker Nodes)

If you prefer to run full VMs on z4 worker nodes rather than containerized services, here's what's viable:

### Option A: Single Orchestration VM on z4-media-01
**Size:** 8GB RAM, 4 vCPU, 100GB storage  
**Services:** n8n, Qdrant, Prometheus, Portainer, nginx reverse proxy  
**Network:** 1Gb link sufficient (same bandwidth profile as containerized versions)  
**Benefit:** Isolated environment, easier backup/restore, single point to manage

### Option B: Dual VMs (Orchestration + Transcode)
**VM 1 on z4-media-01:** n8n, Qdrant, monitoring (same as Option A)  
**VM 2 on z4-media-02:** tdarr agent, FFmpeg, with GPU acceleration (P1000 passthrough)  
**Network:** z4-media-02 VM gets direct GPU access; better than container GPU pass-through  
**Benefit:** GPU isolation, cleaner resource allocation

### Option C: Hybrid (VMs + Containers)
**z4-media-01:** Run Debian 12 VM with orchestration services installed natively (systemd, not Docker)  
**Unraid:** Keep Stash, Faster-Whisper, GPU-dependent containers only  
**Benefit:** Mix of VM stability for core services + container lightweightness for Unraid

### VM Viability Assessment
| Service | Container | VM | Notes |
|---------|-----------|----|----|
| n8n | ✅ Easy | ✅ Better (systemd auto-restart) | Recommend VM |
| Qdrant | ✅ Easy | ✅ Good | Either works |
| Stash | ❌ No move | ✅ No (stays Unraid) | Never move |
| tdarr agent | ✅ Container | ✅ Better (GPU passthrough) | VM if using GPU |
| Faster-Whisper | ❌ No move | ❌ No (stays Unraid) | Needs Stash proximity |

**Recommendation:** If you want to offload Unraid with minimal complexity, containers on z4 (Phase 1 plan) is faster. If you want a cleaner long-term architecture, a single Debian VM on z4-media-01 with n8n + Qdrant installed natively is more maintainable.

---

**Prepared by:** Claude  
**Date:** 2026-05-14  
**Next Action:** Confirm container list, clarify VM preference, and prioritize Phase 1 migrations


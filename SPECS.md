# Infrastructure Specs — Live Audit
**Collected:** 2026-05-09 via SSH + HTTP probe  
**Method:** SSH into Unraid, port scan + HTTP probe to other machines  
**SSH key used:** `claude-cowork-2026` (ed25519, saved in `.codex-ssh/claude_cowork_ed25519`)

---

## Machine 1 — Unraid Server (192.168.1.147)
**Hostname:** unriad01  
**DNS:** (no external DNS entry — local only)

### Hardware
| Component | Detail |
|-----------|--------|
| **CPU** | Intel Core i9-12900K (Alder Lake) |
| **Cores / Threads** | 16 cores (8P + 8E) / 24 threads |
| **Max Boost** | 5.2 GHz |
| **RAM** | 62 GB (no swap) |
| **GPU** | NVIDIA GeForce GTX 1660 Ti |
| **VRAM** | 6 GB total · 796 MB used · ~5 GB free at idle |
| **GPU Driver** | 595.58.03 (CUDA 13.2) |
| **Network** | Bond0 (eth0 active, eth1 no-carrier) → br0 @ 192.168.1.147/24 |
| **Boot device** | 7.5 GB USB (2.2 GB used) |

### Storage — ZFS Pools
| Pool | Raw Size | Used | Free | % Full | Datasets |
|------|----------|------|------|--------|----------|
| **dtv** | 311 TB | 261 TB | 50 TB | 83% | Domestic_Series (73TB), Domestic_Movies (102TB), Domestic_Concerts (86GB) |
| **itv** | 87.3 TB | 68.4 TB | 19 TB | 78% | adult (8.5TB), Animated_Series (4TB), Anime_Series (5.4TB), International_Movies (15TB), + more |
| **photography** | 43.7 TB | 24.2 TB | 19.5 TB | 55% | SCUBA_Videos (1.5TB), Photos (3TB), SCUBA_Media (8.2TB), raw (1.2TB), immich (210GB) |
| **torrent** | 7.25 TB | 2.75 TB | 4.5 TB | 37% | torrents (2.8TB), tdarr (9GB), ai-data (5.3GB) |

### Storage — Other
| Mount | Size | Used | Notes |
|-------|------|------|-------|
| `/mnt/container` (NVMe) | 1.9 TB | 990 GB | Docker volumes, app data |
| `/boot` (USB) | 7.5 GB | 2.2 GB | Unraid OS boot |

### OS / Software
| Item | Version |
|------|---------|
| Unraid | 7.2.4 |
| Kernel | 6.12.54-Unraid |
| Docker | (current with Unraid 7.2) |

### Running Containers (38 total)
#### Media Acquisition
| Container | Image | Port | Notes |
|-----------|-------|------|-------|
| whisparr-v3 | hotio/whisparr:v3 | 7070 | Adult scene manager |
| prowlarr | linuxserver/prowlarr | 9696 | Indexer aggregator (14 indexers) |
| binhex-qbittorrentvpn | binhex/arch-qbittorrentvpn | 8080 | Torrent client + VPN |
| sabnzbd | linuxserver/sabnzbd | 8282 | Usenet client |
| radarr | linuxserver/radarr | 7878 | Movie manager |
| sonarr | linuxserver/sonarr | 8989 | TV series manager |
| binhex-readarr | binhex/arch-readarr | 8787 | Book manager |
| lidarr | linuxserver/lidarr | 8686 | Music manager |
| mylar3 | linuxserver/mylar3 | 8090 | Comics manager |
| bazarr | linuxserver/bazarr | 6767 | Subtitle manager |
| recyclarr | recyclarr/recyclarr | — | Quality profile sync |

#### Media Management
| Container | Image | Port | Notes |
|-----------|-------|------|-------|
| stash | hotio/stash:latest | 9999 | Adult media manager (v0.31.1) |
| stash-cdp | chromedp/headless-shell | 9222 | Headless Chrome for scraping |
| flaresolverr | flaresolverr/flaresolverr | 8191 | Cloudflare bypass |
| tdarr | haveagitgat/tdarr | 8264-8266 | Video transcoding (v2.71) |
| beets | linuxserver/beets | 8337 | Music library organizer |

#### Media Servers
| Container | Image | Port | Notes |
|-----------|-------|------|-------|
| Jellyfin | jellyfin/jellyfin:latest | (internal) | Open-source media server (v10.11.8) |
| Plex-Media-Server | plexinc/pms-docker | (internal) | Plex media server |
| audiobookshelf | advplyr/audiobookshelf | 13378 | Audiobook server |
| calibre | linuxserver/calibre | 8085 | Book server + manager |
| immich_pro | imagegenius/immich | 8081 | Photo management |

#### AI / ML
| Container | Image | Port | Notes |
|-----------|-------|------|-------|
| ollama | ollama/ollama | 11434 | Local LLM server (GPU) |
| open-webui | open-webui/open-webui | 3001 | Ollama web UI |
| ComfyUI-Nvidia-Docker | mmartial/comfyui-nvidia-docker | 8189 | AI image generation (GPU) |
| Faster-Whisper-Nvidia | linuxserver/faster-whisper:gpu | 10300 | GPU speech-to-text |
| Qdrant | qdrant/qdrant | 6333 | Vector database |
| n8n | n8nio/n8n | 5678 | Workflow automation (idle) |
| SearXNG | searxng/searxng | 8888 | Self-hosted search |

#### Monitoring
| Container | Image | Port | Notes |
|-----------|-------|------|-------|
| Grafana | grafana/grafana | 3000 | Metrics dashboards |
| prometheus | prom/prometheus | 9090 | Metrics collection |
| cadvisor | cadvisor/cadvisor | 8082 | Container metrics |
| tautulli | tautulli/tautulli | 8181 | Plex statistics |
| sabnzbd_exporter | msroest/sabnzbd_exporter | 9387 | SABnzbd metrics |

#### Infrastructure
| Container | Image | Port | Notes |
|-----------|-------|------|-------|
| Redis | redis | 6379 | Cache |
| PostgreSQL_Immich | tensorchord/pgvecto-rs | 5433 | Immich database |
| Unraid-Cloudflared-Tunnel | figro/unraid-cloudflared-tunnel | 46495 | Cloudflare tunnel |
| Kometa | kometateam/kometa | — | Plex metadata (running 3 weeks) |
| OpenProject | openproject/openproject | 5683 | Project management |
| OpenClaw | openclaw/openclaw | 18789 | (purpose TBD) |

### Ollama Models on Unraid
| Model | Size | Quantization | Quality |
|-------|------|--------------|---------|
| llava:7b-v1.5-q2_K | 3.5 GB | Q2_K (2-bit) | ⚠️ Very degraded — primary vision model |
| moondream:latest | 1.7 GB | — | Small vision model |
| llama3.2:3b | 2.0 GB | — | General language |
| qwen3.5:4b | 3.4 GB | — | General language |

**Critical GPU constraint:** GTX 1660 Ti (6 GB VRAM) limits model quality. A 7B vision model at Q4_K_M needs ~4.1 GB, leaving only ~2 GB headroom — tight but feasible. Recommend replacing llava:7b-v1.5-q2_K with llava:7b-v1.5-q4_K_M.

---

## Machine 2 — Workstation (192.168.1.182)
**Hostname:** localhost-live.tom-scuba.com  
**SSH access:** Port 22 open, needs key added

### Hardware (inferred)
| Component | Detail |
|-----------|--------|
| **OS** | Windows 11 |
| **GPU** | NVIDIA RTX (class inferred from RTX Desktop Manager + Nsight tools) |
| **VRAM** | ≥ 19 GB — runs qwen2.5:32b at Q4_K_M (18.5 GB model) |
| **GPU** | Most likely RTX 4090 (24 GB) or RTX 3090 (24 GB) |

> **Note:** GPU specs are inferred. Run `nvidia-smi` in PowerShell to confirm exact model/VRAM.

### Software
| App | Version | Notes |
|-----|---------|-------|
| Ollama | 0.21.0 | Models: qwen2.5:32b, qwen2.5:14b-instruct |
| Docker Desktop | current | — |
| WSL (Ubuntu-24.04) | — | Linux subsystem |
| DaVinci Resolve | current | GPU-accelerated video editing |
| VS Code | current | — |
| MakeMKV | current | Disc ripping |
| NVIDIA Nsight Compute | 2022 + 2025 | GPU profiling |
| NVIDIA RTX Desktop Manager | current | RTX-specific GPU management |

### Ollama Models on Workstation
| Model | Size | Quantization | Notes |
|-------|------|--------------|-------|
| qwen2.5:32b | 18.5 GB | Q4_K_M | Large general-purpose LLM |
| qwen2.5:14b-instruct | 8.4 GB | Q4_K_M | Mid-size instruct model |

**Strategic implication:** The workstation's GPU is 4x+ more powerful than Unraid's GTX 1660 Ti. For vision inference (ahavenvlmconnector), routing requests to the workstation Ollama at `http://192.168.1.182:11434` would yield dramatically better quality than running locally on Unraid.

---

## Machine 3 — z4-media-01 (192.168.1.10)
**Hostname:** z4-media-01.tom-scuba.com  
**SSH access:** Port 22 open, needs key added

### Known
| Item | Detail |
|------|--------|
| Open ports | 22 (SSH), 111 (NFS portmapper) |
| Role | NFS storage server |
| OS | Linux (SSH banner identifies, type unknown) |
| Services visible | Only NFS portmapper — no web UI, no media server |

### Unknown (need SSH access)
- CPU / RAM / disk
- NFS exports (what volumes does it serve?)
- OS distribution and version
- Whether it's TrueNAS, OpenMediaVault, or plain Linux

---

## Machine 4 — z4-media-02 (192.168.1.139)
**Hostname:** z4-media-02.tom-scuba.com  
**SSH access:** Port 22 open (user `mbeck` has existing sessions), needs new key added

### Known
| Item | Detail |
|------|--------|
| Open ports | 22 (SSH), 5000 (FileFlows), 9000 (unknown) |
| OS | Linux |
| FileFlows | v26.01.9.6181 |
| FileFlows runners | 3 flow runners, temp path `/temp` |
| Role | Media processing / transcoding automation |

### FileFlows Note
FileFlows is a direct competitor to Tdarr (both handle automated video transcoding). Running both is redundant. Decision needed: keep one, migrate jobs to the survivor, decommission the other. FileFlows is newer and has a cleaner pipeline model; Tdarr has a larger community plugin library.

### Unknown (need SSH access)
- CPU / RAM / GPU (does it have a GPU for transcoding?)
- Disk configuration and mounts
- OS distribution and version
- What media paths it processes
- Port 9000 — Portainer? Another service?

---

## Network Topology

```
192.168.1.0/24
├── 192.168.1.10    z4-media-01    NFS server (storage)
├── 192.168.1.139   z4-media-02    Linux media processing (FileFlows)
├── 192.168.1.147   unriad01       Unraid — primary media server (38 containers)
├── 192.168.1.155   tom-lt         Laptop (tom-lt.tom-scuba.com)
├── 192.168.1.182   localhost-live  Windows workstation (Ollama, DaVinci Resolve)
├── 192.168.1.25    HDHR-108081B9  HDHomeRun tuner
└── 192.168.1.225   RokuUltra      Streaming device
```

---

## SSH Key Status
| Machine | Key | Status |
|---------|-----|--------|
| Unraid (192.168.1.147) | `claude-cowork-2026` (ed25519) | ✅ Working |
| z4-media-01 (192.168.1.10) | — | ❌ No access — add key manually |
| z4-media-02 (192.168.1.139) | — | ❌ No access — add key manually |
| Workstation (192.168.1.182) | — | ❌ No access — add key manually |

**Public key to add to all machines:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPT/s6bW5BmU8wLYQya1UDuqJHtHa5ivZVcSGZq7zYgv claude-cowork-2026
```

To add to each machine (run as that machine's admin user):
```bash
mkdir -p ~/.ssh && echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPT/s6bW5BmU8wLYQya1UDuqJHtHa5ivZVcSGZq7zYgv claude-cowork-2026' >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
```

**Private key location:** `C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management\.codex-ssh\claude_cowork_ed25519`

---

## Key Decisions Unlocked by This Audit

### 1. AI Vision Routing
The Unraid GTX 1660 Ti (6 GB VRAM) is too limited for good vision model inference. The workstation has a high-VRAM RTX GPU. **Recommendation:** Configure ahavenvlmconnector to point at `http://192.168.1.182:11434` (workstation Ollama) instead of the local Unraid Ollama. This gives Stash access to full-quality vision inference without adding GPU load to Unraid.

### 2. Tdarr vs. FileFlows
Tdarr runs on Unraid (port 8264). FileFlows runs on z4-media-02 (port 5000). Both do the same job. **Recommendation:** Audit what each is processing, consolidate to one tool. FileFlows is cleaner but Tdarr has wider community support. Decision depends on what workflows are configured in each.

### 3. Unraid GPU Upgrade Path
The GTX 1660 Ti (6 GB) is the single biggest hardware bottleneck. Upgrading to an RTX 3090 (24 GB) or RTX 4080 Super (16 GB) would unlock: better llava models (14B+), ComfyUI at higher quality, Faster-Whisper at larger model size, and reduce the need to offload inference to the workstation.

### 4. eth1 Down
The bond0 shows eth1 as no-carrier (DOWN). If this was meant to be a 10GbE link or a failover NIC, it's not working. Investigate: is the second NIC unplugged, or was this intentional?

### 5. Plex AND Jellyfin
Both media servers are running simultaneously. This is intentional (some content in Plex, some in Jellyfin?) or redundant. Clarify which is the primary endpoint and whether both need to be running.

### 6. dtv Pool at 83% Full
The `dtv` pool (311 TB) is at 83%. ZFS performance degrades above 80%. Consider: adding drives, pruning old content, or migrating some content to dtv from other pools.

# Changelog

All notable changes to the Adult Media Management project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### In Progress
- Phase 1B: n8n HTTP node configuration for content processing
- VLM task execution monitoring on Unraid
- Media server integration testing (Jellyfin/Plex NFO import)

### Planned
- Performer image enrichment at scale (goal: 1,897 performers)
- NFO generation workflow automation
- Performer gallery creation
- Automated publishing pipeline

## [0.1.0] — May 25, 2026 — Foundation Restart

### Added
- Project assessment document (PROJECT_STATUS_2026-05-25.md)
- GitHub setup guide (GITHUB_SETUP.md)
- Comprehensive README with project overview
- .gitignore for secrets management
- Complete infrastructure documentation in MASTER_PLAN.md

### Infrastructure Status (Verified May 9-16)
- **Stash v0.31.1** — Scene/performer library operational
- **n8n v2.20.7** — Workflow automation foundation (Phase 4: 35% complete)
- **Ollama** — Vision LLM models available:
  - llava:7b (4.7GB) on Unraid — primary tagging model
  - llava:13b (8GB) on Workstation — high-quality vision
- **Network:** 5-node infrastructure with confirmed SSH access
- **GPU Resources:** RTX 4090 (24GB), GTX 1660 Ti (6GB), 2x Quadro P1000 (4GB)

### Completed (Phase 1A — Stash Authentication)
- ✅ GraphQL API authentication with Stash v0.31.1
- ✅ Scene data retrieval via authenticated GraphQL queries
- ✅ Cookie-based session management
- ✅ n8n webhook endpoint functional (Phase 4: 35% complete)

### Completed (Phase 1C — VLM Migration)
- ✅ Haven VLM connector configuration fixed
- ✅ Ollama migrated from workstation to Unraid for stability
- ✅ Model compatibility verified (llava:13b → llava:7b)
- ✅ VLM task queued and ready for execution

### Fixed
- **May 16:** Ollama model mismatch (config pointed to unavailable llava:13b) → resolved to llava:7b
- **May 13:** Workstation kernel updated, Ollama v0.21.0 → v0.23.3 for GPU stability
- **May 13:** Root cause of May 12 crash identified: Opera GX + Ollama VA space exhaustion

### Documentation
- Full infrastructure audit (AUDIT_2026-05-09.md)
- Master plan with service inventory (MASTER_PLAN.md)
- Network topology with confirmed roles (PROJECT_NETWORK.md)
- Phase-by-phase implementation guides (PHASE_*_*.md)

### Known Issues
- **Stash webhook configuration:** v0.31.1 UI doesn't expose webhook config section (workaround: use actress_library plugin events)
- **dtv storage pool:** 311 TB, 83% full (above 80% threshold) → monitor for capacity planning
- **VLM task execution:** Queued but not actively monitored yet

---

## [0.0.2] — May 16, 2026 — VLM Migration & Stabilization

### Fixed
- **llava:13b model unavailable on Unraid** → migrated to stable llava:7b (4.7GB)
- **Ollama version outdated** → updated from v0.21.0 to v0.23.3 on workstation
- **Haven VLM config** → corrected model_id and base_url endpoints

### Infrastructure Verified
- Ollama API: http://127.0.0.1:11434/v1 (Unraid)
- Stash API: http://127.0.0.1:9999 (Unraid)
- VLM task ready for execution in Stash queue

---

## [0.0.1] — May 13, 2026 — Workstation Stabilization

### Resolved
- **Workstation crash loop (9 reboots May 12, 16:39–17:46)** → root cause: NVRM VA space exhaustion
  - Opera GX browser + Ollama inference competing for GPU BAR1 virtual address space
  - Mitigation: Disable GPU in Opera GX or limit Ollama GPU headroom

### Infrastructure Updates
- Fedora kernel: 6.19.14 → 7.0.4
- NVIDIA driver: 595.71.05 (maintained)
- Ollama v0.23.3 tested and stable
- RTX 4090 confirmed 22.5 GiB CUDA-visible

---

## [0.0.0] — May 9, 2026 — Initial Audit

### Infrastructure Audit Complete
- **Machines:** 5 confirmed (Unraid, Workstation, z4-media-01, z4-media-02, Laptop)
- **Services:** 38 containers on Unraid, full software stack operational
- **SSH Access:** Verified to all nodes
- **Storage:** 438 TB usable across ZFS pools
- **GPU:** RTX 4090 (24GB), GTX 1660 Ti (6GB), confirmed via live audit

### Project Goals Established
1. Clean performer profiles (1,897 performers, 356 with images = 19%)
2. Automated content pipeline (end-to-end, zero manual steps)
3. Media server output (Jellyfin/Plex with NFO + galleries)
4. AI-powered tagging (vision LLM auto-tagging)

### Documentation Created
- MASTER_PLAN.md — Infrastructure & service inventory
- SPECS.md — Hardware specifications
- AUDIT_2026-05-09.md — Raw audit data
- ACTION_PLAN.md — Initial roadmap

---

## Version Numbering

- **0.x.y** — Pre-release (foundation building)
  - 0.1.z — Phase 1 complete (authentication, VLM, n8n foundation)
  - 0.2.z — Phase 2 complete (automation, enrichment, NFO)
  - 0.3.z — Phase 3 complete (media server integration, publishing)

- **1.0.0** — Release candidate (all 4 goals achieved)
  - 1.0.1+ — Bug fixes, optimizations
  - 1.1.0+ — New features (gallery expansion, AI improvements, etc.)

---

## Future Roadmap (Estimated)

| Phase | Goal | Est. Duration | Completion |
|-------|------|---------------|------------|
| 1B | HTTP nodes & content processing | 1 week | May 31 |
| 1C Validation | VLM execution & media server testing | 1 week | June 7 |
| 2 | Performer enrichment at scale | 2-3 weeks | June 21 |
| 3 | NFO & publishing automation | 1-2 weeks | July 5 |
| **Release** | **v1.0.0 — All 4 goals achieved** | | **~July 5** |

---

## Glossary & Acronyms

- **Stash** — Scene/performer library management system
- **n8n** — Workflow automation platform
- **Ollama** — Local LLM/vision model hosting
- **VLM** — Vision Language Model (llava, etc.)
- **NFO** — XML metadata file format for media servers
- **GraphQL** — API query language used by Stash
- **Webhook** — HTTP callback trigger for automation
- **Jellyfin** — Open-source media server
- **Plex** — Commercial media server
- **Unraid** — NAS/container OS platform
- **ZFS** — Advanced filesystem for storage pools

---

**Created:** May 25, 2026  
**Maintained by:** Tom Beck (beckmt4@gmail.com)  
**Repository:** https://github.com/YOUR_USERNAME/adult-media-management

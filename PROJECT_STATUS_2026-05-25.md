# Adult Media Management Platform — Project Assessment & Restart Plan
**Date:** May 25, 2026  
**Status:** Stale project restart — reboot with GitHub integration

---

## Executive Summary

The Adult Media Management platform is **~60% infrastructure complete** but **~20% operationally complete**. All hardware, services, and core tools exist. The work ahead is completing integrations, validation, and automation workflows.

This assessment covers:
- What has been completed vs. original goals
- Current blockers and state
- Prioritized next steps
- GitHub setup and version control strategy

---

## Original Goals — Status Matrix

| # | Goal | Description | Progress | ETA |
|---|------|-------------|----------|-----|
| 1️⃣ | Clean performer profiles | Enrich 1,897 performers; currently 356 (19%) have images | 25% | 2-3 weeks |
| 2️⃣ | Automated pipeline | End-to-end scene acquisition → tagging → publishing, zero manual steps | 30% | 4-5 weeks |
| 3️⃣ | Media server output | Jellyfin/Plex with NFO metadata + performer galleries | 15% | 3-4 weeks |
| 4️⃣ | AI-powered tagging | Vision LLM auto-tag scene content from video frames | 40% | 2 weeks (if VLM task completes) |

---

## What's Actually Complete

### ✅ Infrastructure (Phase 0)
- **Network:** 5 machines, confirmed roles & SSH access
  - Unraid (192.168.1.147) — primary compute
  - Workstation (192.168.1.182) — RTX 4090 AI node
  - z4-media-01 (192.168.1.10) — n8n orchestration
  - z4-media-02 (192.168.1.139) — media processing (FileFlows, Whisper)
  - Laptop (192.168.1.155) — Cowork host
- **Storage:** 438 TB usable across ZFS pools
- **GPU:** RTX 4090 (24GB), GTX 1660 Ti (6GB), 2x Quadro P1000 (4GB each)
- **Crash root cause:** Identified & mitigated (Ollama + Opera GX VA exhaustion)

### ✅ Stash Core (Phase 1A — Authentication)
- Stash v0.31.1 running on Unraid
- GraphQL API endpoint working (http://192.168.1.147:9999/graphql)
- Session cookie authentication implemented
- Scene library: 2,964 scenes, 1,902 performers, 798 studios

### ✅ Stash Plugins Installed
- **actress_library** — performer enrichment (configured, working)
- **sceneMatcher** — StashDB matching (v1.1.0)
- **mcMetadata** — NFO generation for Jellyfin/Plex (v1.4.0)
- **tagManager**, **studioManager**, **performerImageSearch** — utilities
- **ahavenvlmconnector** — vision LLM integration (fixed May 16, llava:7b)

### ✅ AI/Vision Stack (Phase 1C — VLM Migration)
- Ollama migrated from workstation to Unraid (May 16)
- Models available:
  - **llava:7b** (4.7 GB) — primary vision model
  - llama3.2:3b, moondream, qwen3.5:4b
- Haven VLM config fixed (was pointing to unavailable llava:13b)
- **VLM task queued** — ready for execution in Stash

### ✅ n8n Workflow Framework (Phase 4 — 35% complete)
- n8n v2.20.7 running on z4-media-01
- Workflow published & active: `oYYQuZXygAejZWac`
- Webhook endpoint working: `http://192.168.1.147:5678/webhook/scene-lifecycle`
- Scene lifecycle automation workflow scaffolded (Webhook → Wait → HTTP nodes)

### ✅ Media Servers Running
- Jellyfin 10.11.8 (8096)
- Plex Media Server (32400)
- Tautulli for analytics (8181)

---

## What's Incomplete / Blocked

### ⏳ Phase 1B — Content Processing & Expansion
**Status:** Not started  
**Blocker:** HTTP node configuration in n8n  
**Work needed:**
1. Configure 6 HTTP nodes in n8n workflow (each with GraphQL queries)
2. Add query fields: performers, studios, tags, duration, ratings, cover URLs
3. Implement ID format normalization (webhook string → numeric Stash ID)
4. Add error handling and conditional branches

**Time estimate:** 3-4 hours of hands-on config

### ⏳ Phase 1C Validation — VLM Task Execution
**Status:** Task queued, not monitored  
**Work needed:**
1. Monitor VLM task execution on Unraid (expect ~18 FPM frame processing rate)
2. Verify scene markers created with correct content tags
3. Validate llava:7b accuracy and performance
4. Address any model-specific refinements

**Time estimate:** 2-3 hours (mostly monitoring/iteration)

### ⏳ Phase 2 — Performer Enrichment
**Status:** actress_library configured but not at scale  
**Goals:**
1. Complete performer image acquisition (356 → 1,546 needed)
2. Implement batch enrichment process
3. Add cross-source validation (StashDB, TMDB, manual correction)

**Blockers:** Needs data sources (scraping or API integration)  
**Time estimate:** 2-3 weeks

### ⏳ Phase 3 — NFO & Media Server Integration
**Status:** Plugin installed, not activated  
**Work needed:**
1. Enable mcMetadata NFO generation on every scene update
2. Configure Jellyfin/Plex to import NFO metadata
3. Test gallery generation for performers
4. Implement watch history sync

**Time estimate:** 1-2 weeks

### ❌ Phase 2B — Automated Publishing
**Status:** Not started  
**Scope:** End-to-end automation (acquisition → processing → tagging → publishing)

---

## Current Blockers & Technical Debt

### 🔴 Critical
1. **n8n HTTP node config incomplete** — blocking Phase 1B (3-4 hours to fix)
2. **VLM task not monitored** — task queued but no execution verification (low risk, just needs review)
3. **Stash webhook integration** — UI doesn't expose webhook config in v0.31.1 (workaround: use actress_library events)

### 🟡 Medium Priority
1. **Performer image source integration** — no automated scraping/API yet
2. **NFO generation testing** — plugin installed but untested at scale
3. **Whisparr/Whisper transcription** — queued items not flowing end-to-end

### 🟢 Low Priority (Won't Block MVP)
1. DaVinci Resolve integration (mentioned but not core path)
2. Whisparr queue clearance optimization
3. Grafana/Prometheus dashboard setup

---

## Recommended Next Steps (Prioritized)

### **Week 1: Complete Automation Foundation**

**Day 1-2: Finish n8n Phase 1B** (6 hours)
- [ ] Complete HTTP node #1: Get Scene Details (GraphQL query expansion)
- [ ] Add HTTP nodes #2-6 (Scrape, Tag, Transcription, Vision, Transcode)
- [ ] Implement conditional error handling
- [ ] Test workflow end-to-end with manual trigger

**Day 3: Validate VLM Execution** (3 hours)
- [ ] SSH to Unraid, check Stash task queue
- [ ] Monitor VLM task execution (should process ~18 FPM)
- [ ] Verify scene markers created with correct tags
- [ ] Adjust model/settings if needed

**Day 4: Test Media Server Integration** (4 hours)
- [ ] Trigger n8n workflow with test scene
- [ ] Verify NFO generation via mcMetadata
- [ ] Test Jellyfin/Plex metadata import
- [ ] Validate performer gallery display

### **Week 2: Performer Enrichment at Scale** (10-15 hours)
- [ ] Identify performer image source (StashDB API, TMDB, web scraping)
- [ ] Implement batch enrichment in actress_library
- [ ] Run enrichment on 1,546 performers needing images
- [ ] Validate data quality and accuracy

### **Week 3: Polish & Hardening** (8-10 hours)
- [ ] End-to-end workflow testing with real content
- [ ] Monitor for 2-3 days of continuous operation
- [ ] Document edge cases and known limitations
- [ ] Set up alerting/monitoring for failures

---

## Infrastructure Health Check

| Component | Status | Notes |
|-----------|--------|-------|
| Unraid (147) | ✅ Healthy | 38 containers, GPU stable, ZFS pools stable |
| Workstation (182) | ✅ Healthy | Fedora kernel 7.0.4, Ollama updated, stable boot |
| z4-media-01 (10) | ✅ Healthy | n8n running, SSH access working |
| z4-media-02 (139) | ✅ Healthy | FileFlows + GPU transcoding ready |
| Network | ✅ Healthy | SSH access confirmed to all nodes |
| **VRAM Usage** | ⚠️ Monitor | Unraid: llava:7b (~4.7GB), headroom OK; Workstation: RTX 4090 (24GB), plenty |

---

## GitHub Integration Plan

### Repository Structure
```
adult-media-management/
├── docs/
│   ├── MASTER_PLAN.md              (this file, updated)
│   ├── ARCHITECTURE.md             (new: system design)
│   ├── API_REFERENCE.md            (new: Stash + n8n specs)
│   ├── SETUP.md                    (new: deployment guide)
│   └── TROUBLESHOOTING.md          (new: common issues)
├── stash-plugins/
│   ├── actress_library/            (existing)
│   ├── haven-vlm-config.py         (existing config)
│   └── README.md                   (new: plugin guide)
├── n8n/
│   ├── workflows/
│   │   ├── scene-lifecycle.json    (main automation)
│   │   └── performer-enrichment.json (new)
│   └── README.md
├── scripts/
│   ├── audit_unraid.ps1            (existing diagnostics)
│   ├── deploy.sh                   (new: setup automation)
│   ├── monitor.sh                  (new: health checks)
│   └── README.md
├── tests/
│   ├── stash_api_test.py           (new: verify API connectivity)
│   ├── n8n_workflow_test.py        (new: verify workflow execution)
│   └── README.md
├── config/
│   ├── docker-compose.yml          (new: quick-start)
│   ├── unraid-template.xml         (new: Unraid app definitions)
│   └── .env.example                (new: secrets template)
├── README.md                        (project overview)
├── CHANGELOG.md                     (version history)
├── LICENSE                          (Apache 2.0)
└── .gitignore                       (API keys, secrets)
```

### What to Include in Git
- All documentation (*.md)
- n8n workflow JSON exports
- Stash plugin source code
- Deployment scripts
- Configuration templates
- Test cases
- GitHub Actions CI/CD (if applicable)

### What to Exclude (.gitignore)
- `.env`, `.env.local` (secrets, API keys)
- `.codex/`, `.codex-ssh/` (local SSH keys)
- `manual-tmp/` (test/throwaway dirs)
- `node_modules/`, `__pycache__/` (generated)
- `.DS_Store`, `*.log` (OS/build artifacts)
- Container secrets and credentials

### GitHub Milestones & Issues
**Milestone 1: Foundation** (Week 1)
- Issue: Complete n8n workflow HTTP nodes
- Issue: Validate VLM execution
- Issue: Test media server integration

**Milestone 2: Scale** (Week 2)
- Issue: Implement performer enrichment at scale
- Issue: Add 1,500+ performer images

**Milestone 3: Polish** (Week 3)
- Issue: End-to-end testing
- Issue: Documentation & runbooks
- Issue: Alerting & monitoring setup

---

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Performers with images | 1,897 | 356 (19%) | 📈 Improving |
| Scenes with AI tags | 2,964 | ~78 (from May VLM run) | 📈 In progress |
| Automated pipeline runtime | <5 min (scene → publishing) | Not yet measured | ❓ TBD |
| Media server metadata quality | 95%+ accuracy | Not yet tested | ❓ TBD |
| System uptime | >99% | >95% (stable) | ✅ Good |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Ollama VRAM exhaustion (4090) | Low | High | OLLAMA_MAX_LOADED_MODELS=1, no concurrent GPU apps |
| Stash API breaking change | Low | Medium | Version lock (v0.31.1), monitor releases |
| n8n workflow failure | Medium | Medium | Error handling nodes, alerting, backoff logic |
| Performer data source loss | Low | Medium | Multiple sources (StashDB, TMDB, manual), backup enrichment |
| Storage capacity (dtv 83% full) | Medium | High | Monitor monthly, archive or expand before 90% |

---

## Restart Checklist

- [ ] Review this assessment with team
- [ ] Initialize GitHub repository
- [ ] Push all code and documentation
- [ ] Set up GitHub Actions for CI/CD (optional, but recommended)
- [ ] Update memory/context with new GitHub URL
- [ ] Begin Day 1 work (n8n HTTP node config)
- [ ] Schedule daily status updates
- [ ] Monitor infrastructure health continuously

---

## Key Files & Resources

| File | Purpose | Location |
|------|---------|----------|
| MASTER_PLAN.md | Infrastructure & goals | Project root |
| PHASE_4_N8N_AUTOMATION.md | Workflow node specifications | Project root |
| N8N_IMPLEMENTATION_GUIDE.md | Step-by-step n8n setup | Project root |
| Scene Lifecycle Automation.json | Current workflow definition | Project root |
| haven-vlm-multiplexer-config.json | VLM model config | Project root |

---

## Contact & Handoff Notes

**Current Owner:** Tom Beck (beckmt4@gmail.com)  
**Stash API Key:** [Stored securely, not in Git]  
**Whisparr API Key:** [Stored securely, not in Git]  
**SSH Key:** `~/.codex-ssh/claude_cowork_ed25519` for Unraid  

For questions on infrastructure:
- Unraid SSH: `ssh -i claude_cowork_ed25519 root@192.168.1.147`
- n8n API: `http://192.168.1.147:5678/` (requires auth)
- Stash API: `http://192.168.1.147:9999/` (requires session auth)

---

**Next Review Date:** May 28, 2026  
**Assessment Created:** May 25, 2026 by Claude

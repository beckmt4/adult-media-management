# Adult Media Management Platform

**Status:** Restarted May 25, 2026 | Infrastructure ~60% complete | Automation ~20% complete

An AI-powered, self-hosted media management platform for adult content with automated tagging, performer enrichment, and media server integration.

## 🎯 Project Goals

| # | Goal | Progress | Est. Completion |
|---|------|----------|-----------------|
| 1️⃣ | Clean performer profiles (1,897 performers) | 25% | 2-3 weeks |
| 2️⃣ | Automated content pipeline (zero manual steps) | 30% | 4-5 weeks |
| 3️⃣ | Media server output (Jellyfin/Plex + metadata) | 15% | 3-4 weeks |
| 4️⃣ | AI-powered tagging (vision LLM) | 40% | 2 weeks |

## 🏗️ Architecture

### Network Infrastructure
- **Unraid** (192.168.1.147) — Primary compute server with 38 containers
- **Workstation** (192.168.1.182) — RTX 4090 AI processing node (Fedora Linux)
- **z4-media-01** (192.168.1.10) — n8n workflow orchestration
- **z4-media-02** (192.168.1.139) — FileFlows transcoding + media processing
- **Laptop** (192.168.1.155) — Cowork management host

### Core Services

**Media Management**
- **Stash v0.31.1** — Scene/performer library with GraphQL API
- **Whisparr v3.3.3** — Automated content acquisition (1,000+ items queued)
- **n8n v2.20.7** — Workflow automation (Phase 4: 35% complete)

**AI/Vision**
- **Ollama** — Vision LLM hosting (llava:7b on Unraid; llava:13b on workstation)
- **Haven VLM Connector** — Integration with Stash for auto-tagging
- **ComfyUI** — GPU image generation

**Media Output**
- **Jellyfin 10.11.8** — Open-source media server
- **Plex Media Server** — Commercial media server
- **mcMetadata** — NFO generation for media servers

**Audio/Transcription**
- **Faster-Whisper** — GPU-accelerated speech-to-text
- **FileFlows** — Distributed media processing

## 📊 Current Status

### ✅ Completed
- [x] Infrastructure audit & documentation (May 9-13)
- [x] SSH access & network topology verified
- [x] Stash GraphQL API authentication (Phase 1A, May 15)
- [x] Haven VLM migration to Unraid (Phase 1C, May 16)
- [x] n8n webhook endpoint (Phase 4, 35% complete)
- [x] Workstation crash diagnosis & mitigation (May 12)

### 🚀 In Progress
- [ ] Phase 1B: n8n HTTP node configuration (6 nodes remaining)
- [ ] VLM task execution monitoring & validation
- [ ] Media server integration testing
- [ ] Performer image enrichment at scale

### 📋 Not Started
- [ ] Phase 2: NFO generation & media server publishing
- [ ] Phase 3: Performer gallery creation
- [ ] Automated publishing & watch history sync

## 🛠️ Quick Start

### Prerequisites
- SSH access to Unraid (192.168.1.147)
- API keys: Stash, Whisparr (stored securely, not in repo)
- Local Git installation

### Initial Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/adult-media-management.git
   cd adult-media-management
   ```

2. **Review Documentation**
   - `PROJECT_STATUS_2026-05-25.md` — Assessment & next steps
   - `MASTER_PLAN.md` — Infrastructure specs
   - `PHASE_4_N8N_AUTOMATION.md` — Workflow details

3. **SSH into Infrastructure**
   ```bash
   # Unraid
   ssh -i ~/.codex-ssh/claude_cowork_ed25519 root@192.168.1.147
   
   # n8n workflow status
   curl http://192.168.1.147:5678/api/v1/workflows
   
   # Stash API
   curl http://192.168.1.147:9999/graphql
   ```

4. **Verify Services**
   - Unraid: http://192.168.1.147:6543 (webUI)
   - Stash: http://192.168.1.147:9999
   - n8n: http://192.168.1.10:5678 (if accessible)
   - Jellyfin: http://192.168.1.147:8096

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| `PROJECT_STATUS_2026-05-25.md` | Assessment, next steps, risks | Project leads |
| `MASTER_PLAN.md` | Infrastructure details, specs | DevOps, architects |
| `PHASE_4_N8N_AUTOMATION.md` | Workflow node specifications | Engineers (n8n) |
| `N8N_IMPLEMENTATION_GUIDE.md` | Step-by-step n8n setup | Engineers (n8n) |
| `GITHUB_SETUP.md` | Git & GitHub workflow | All contributors |
| `TROUBLESHOOTING.md` | Common issues & solutions | Support, ops |

## 🔧 Development Workflow

### Branches
- `main` — Stable, tagged releases
- `develop` — Active development
- `feature/*` — Feature branches (e.g., `feature/phase-1b-http-nodes`)

### Making Changes
```bash
# Create feature branch
git checkout -b feature/your-feature develop

# Make changes
git add .
git commit -m "Description of changes"

# Push and create PR
git push -u origin feature/your-feature
# Then create PR on GitHub: develop ← feature/your-feature
```

## 🚨 Critical Infrastructure Notes

### Unraid Storage ⚠️
- **dtv pool:** 311 TB, **83% full** (above 80% threshold)
- **Action:** Monitor monthly, expand or archive before reaching 90%

### Workstation GPU ⚠️
- **RTX 4090** (24GB VRAM) — primary AI node
- **Risk:** Ollama + concurrent GPU apps (e.g., Opera GX) → VA space exhaustion
- **Mitigation:** Close GPU apps before heavy Ollama inference; use `OLLAMA_MAX_LOADED_MODELS=1`

### Ollama Models
- **Unraid:** llava:7b (4.7GB, stable)
- **Workstation:** llava:13b (8GB), llava:7b (4.7GB)
- **Don't load:** Multiple models simultaneously on same machine

## 📈 Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Performers with images | 1,897 | 356 (19%) | 📈 In progress |
| Scenes with AI tags | 2,964 | ~78 | 📈 Queued |
| Pipeline automation | 100% | ~30% | 🚀 Not started |
| Media server metadata | 95% accurate | Unknown | ❓ TBD |
| System uptime | >99% | >95% | ✅ Good |

## 🔐 Security & Secrets

**NEVER commit to this repository:**
- API keys, tokens, credentials
- SSH private keys
- `.env` files with secrets
- Passwords or authentication data

**Secure storage:**
- Use `.env.example` as template
- Store secrets in GitHub Actions Secrets
- Keep API keys in secure password manager
- Rotate credentials every 90 days

See `.gitignore` for excluded file patterns.

## 📞 Support & Contact

**Project Owner:** Tom Beck (beckmt4@gmail.com)

**Infrastructure Access:**
- Unraid SSH: `root@192.168.1.147`
- Stash API: `http://192.168.1.147:9999/graphql`
- n8n API: `http://192.168.1.147:5678`

**Useful Commands:**
```bash
# SSH to Unraid
ssh -i ~/.codex-ssh/claude_cowork_ed25519 root@192.168.1.147

# Check Stash GraphQL
curl -X POST http://192.168.1.147:9999/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ version }"}'

# Monitor Ollama
curl http://127.0.0.1:11434/api/tags

# Check n8n workflow status
curl http://192.168.1.147:5678/api/v1/workflows
```

## 📋 Roadmap

### Phase 1: Foundation (Weeks 1-2)
- ✅ Phase 1A: Stash auth (complete)
- ✅ Phase 1C: VLM migration (complete)
- ⏳ Phase 1B: HTTP nodes & content processing (in progress)
- ⏳ Phase 1 Validation: VLM execution & media server testing (next)

### Phase 2: Scale (Weeks 3-4)
- [ ] Performer image enrichment (1,500+ images)
- [ ] NFO generation & media server integration
- [ ] Batch workflow optimization

### Phase 3: Polish (Week 5)
- [ ] End-to-end testing
- [ ] Documentation & runbooks
- [ ] Monitoring & alerting setup

## 📝 License

Apache 2.0 — See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature develop`
3. Commit changes: `git commit -m "Description"`
4. Push to branch: `git push -u origin feature/your-feature`
5. Create Pull Request against `develop` branch

**Code Review:** All PRs require 1 approval before merging.

---

**Last Updated:** May 25, 2026  
**Repository:** https://github.com/YOUR_USERNAME/adult-media-management  
**Status:** ✅ Restarted, foundation solid, ready for Phase 1B

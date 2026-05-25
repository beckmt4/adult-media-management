# GitHub Setup Guide

## Overview
This project is being moved to GitHub for version control and collaboration. Follow these steps to initialize and push the repository.

## Prerequisites
- `git` installed on your local machine
- GitHub account with SSH key configured (or HTTPS auth ready)
- Access to create a new repository on GitHub

## Steps to Create & Push Repository

### 1. Create Repository on GitHub
1. Go to https://github.com/new
2. Repository name: `adult-media-management`
3. Description: `AI-powered adult media platform with Stash, n8n, and vision LLM automation`
4. Choose: **Private** (since this contains sensitive infrastructure details)
5. **Do NOT** initialize with README, .gitignore, or License (we have these locally)
6. Click "Create repository"

### 2. Initialize Git Locally (if not already done)
```bash
cd "C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management"

# Initialize git repository
git init --initial-branch=main

# Create .gitignore if not exists (already done in this project)
# echo "# See .gitignore for excluded files" > .gitignore

# Stage all files
git add .

# Create initial commit
git commit -m "Initial commit: Adult Media Management Platform - Foundation Setup

- Infrastructure: 5-node network with Unraid, workstation, media processors
- Stash v0.31.1 with GraphQL API authenticated
- n8n workflow automation platform
- Ollama vision LLM (llava:7b) on Unraid
- Plugins: actress_library, sceneMatcher, mcMetadata, ahavenvlmconnector
- Phase 1A complete: Stash auth working
- Phase 1C complete: VLM migrated and configured
- Next: Complete Phase 1B (HTTP node config), validate VLM execution"
```

### 3. Add Remote and Push to GitHub

**Option A: Using SSH (Recommended)**
```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin git@github.com:YOUR_USERNAME/adult-media-management.git
git branch -M main
git push -u origin main
```

**Option B: Using HTTPS**
```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/adult-media-management.git
git branch -M main
git push -u origin main
# Will prompt for GitHub token/password
```

### 4. Verify Repository

After pushing, verify on GitHub:
- https://github.com/YOUR_USERNAME/adult-media-management
- Check that all files are present
- Check that .gitignore is working (no `.env`, `.codex-ssh/`, etc.)

## Branch Strategy

### Main Branch (`main`)
- Stable, tested code
- Tagged releases
- Protected: requires PR review before merging

### Development Branch (`develop`)
- Active development
- Merges from feature branches
- Staging environment testing

### Feature Branches
- Format: `feature/phase-1b-http-nodes`, `feature/vlm-validation`, etc.
- Create from `develop`
- Submit PR to `develop` when ready

### Example Workflow
```bash
# Create feature branch
git checkout -b feature/phase-1b-http-nodes develop

# Make changes, commit
git add .
git commit -m "Phase 1B: Add HTTP nodes for GraphQL queries"

# Push to GitHub
git push -u origin feature/phase-1b-http-nodes

# Create Pull Request on GitHub (UI)
# After review, merge to develop
```

## Protect Branch Rules (Optional, Recommended)

In GitHub repository settings:
1. Go to **Settings** → **Branches**
2. Add rule for `main`:
   - Require pull request reviews before merging (1 reviewer)
   - Dismiss stale pull request approvals when new commits are pushed
   - Require status checks to pass before merging (if CI/CD is set up)

## Secrets Management

### Store Secrets in GitHub Secrets (NOT in code)
For sensitive data needed by CI/CD:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Create secrets for:
   - `STASH_API_KEY`
   - `WHISPARR_API_KEY`
   - `UNRAID_SSH_KEY`
   - etc.

### Use `.env.example` for Template
```bash
# .env.example (SAFE - can be committed)
STASH_URL=http://192.168.1.147:9999
STASH_API_KEY=<your-api-key-here>
WHISPARR_API_KEY=<your-api-key-here>
N8N_URL=http://192.168.1.147:5678
```

Users can copy: `cp .env.example .env` and fill in secrets locally.

## Continuous Integration (Optional Future Enhancement)

Create `.github/workflows/tests.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run API tests
        run: python tests/stash_api_test.py
      - name: Run workflow validation
        run: python tests/n8n_workflow_test.py
```

## Syncing Local & Remote

### Pull Latest Changes
```bash
git pull origin main
```

### Push Local Changes
```bash
git push origin <branch-name>
```

### Check Status
```bash
git status
git log --oneline -5
```

## First Sync (What to Do Right Now)

1. Open PowerShell/Terminal in project directory
2. Run the commands in "Step 2" above
3. Create GitHub repo (Step 1)
4. Run commands in "Step 3" above (choose SSH or HTTPS)
5. Verify on GitHub

**Estimated time:** 5-10 minutes

## Troubleshooting

### "fatal: not a git repository"
```bash
cd "C:\Users\Tom Beck\Documents\Claude\Projects\Adult Media Management"
git init --initial-branch=main
```

### "error: remote origin already exists"
```bash
git remote remove origin
git remote add origin git@github.com:YOUR_USERNAME/adult-media-management.git
```

### "Permission denied (publickey)"
- Ensure SSH key is added to GitHub: https://github.com/settings/keys
- Test: `ssh -T git@github.com`

### "Updates were rejected because the tip of your current branch is behind"
```bash
git pull origin main
git push origin main
```

## Files Committed

- `PROJECT_STATUS_2026-05-25.md` — Assessment report
- `MASTER_PLAN.md` — Infrastructure & goals  
- `PHASE_4_N8N_AUTOMATION.md` — Workflow specs
- `N8N_IMPLEMENTATION_GUIDE.md` — Setup guide
- `docs/` — Documentation
- `stash-plugins/` — Plugin source code
- `n8n/workflows/` — Workflow JSON exports
- `scripts/` — Deployment & diagnostic scripts
- `.gitignore` — Excluded files
- `LICENSE`, `README.md`, `CHANGELOG.md` — Metadata

**NOT committed** (per .gitignore):
- API keys, credentials, secrets
- SSH private keys (`.codex-ssh/`)
- Temporary files (`manual-tmp/`)
- Model files (too large)
- `.env` files

## Next Steps After Pushing

1. ✅ Push initial commit to GitHub
2. 📋 Create GitHub Issues for:
   - Phase 1B: Complete n8n HTTP nodes
   - Phase 1C Validation: Monitor VLM execution
   - Phase 2: Performer enrichment at scale
3. 🔀 Create `develop` branch for ongoing work
4. 📝 Update GitHub README with project status
5. 🏷️ Create releases/tags for each phase completion

## Resources

- GitHub Docs: https://docs.github.com/
- Git Handbook: https://guides.github.com/introduction/git-handbook/
- SSH Key Setup: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

---

**Setup Date:** May 25, 2026  
**Repository Owner:** Tom Beck (beckmt4@gmail.com)  
**Questions?** Review the GitHub Docs or reach out to maintainers.

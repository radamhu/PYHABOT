# GitHub Actions CI/CD Setup - PYHABOT

**Date:** October 31, 2025  
**Purpose:** Automated testing, building, and artifact management for PYHABOT

---

## 📋 Current CI/CD Setup

### 1. CI Workflow (`.github/workflows/ci.yml`)

A comprehensive testing and building pipeline for PYHABOT with the following features:

**Key Features:**
- ✅ Python 3.11 and 3.12 compatibility testing
- ✅ Poetry-based dependency management
- ✅ Multi-layer caching (pip and Poetry)
- ✅ Code quality checks (Ruff linting, MyPy type checking)
- ✅ Pytest with coverage reporting
- ✅ Codecov integration
- ✅ Package building with Poetry
- ✅ Artifact upload for distribution

**Triggers:**
- Push to `master` or `main` branches
- Pull requests to `master` or `main` branches

**Test Matrix:**
- Python 3.11
- Python 3.12

**Quality Checks:**
- Ruff linting for code style and potential issues
- MyPy static type checking
- Pytest with coverage reporting
- Coverage upload to Codecov (optional)

### 2. Build and Push Workflow (`.github/workflows/build-and-push.yml`)

A comprehensive Docker image building and publishing pipeline with the following features:

**Key Features:**
- ✅ Multi-architecture builds (AMD64 + ARM64)
- ✅ Automatic tagging based on branches, tags, and commits
- ✅ GitHub Container Registry (ghcr.io) publishing
- ✅ Docker layer caching for faster builds
- ✅ Integration testing of built images
- ✅ Supply chain security with artifact attestation
- ✅ SBOM generation for transparency
- ✅ Optional Docker Hub support (commented out)

**Triggers:**
- Push to `master` or `main` branches
- Version tags (e.g., `v1.0.0`)
- Pull requests to `master` or `main` (build only, no push)
- Manual dispatch

**Image Tags Generated:**
```
ghcr.io/radamhu/pyhabot:latest          # Latest from master
ghcr.io/radamhu/pyhabot:master           # Master branch
ghcr.io/radamhu/pyhabot:main             # Main branch
ghcr.io/radamhu/pyhabot:v1.0.0          # Semver tag
ghcr.io/radamhu/pyhabot:1.0             # Major.minor
ghcr.io/radamhu/pyhabot:1               # Major version
ghcr.io/radamhu/pyhabot:master-abc1234    # Branch + SHA
```

### 2. Docker Support

**Dockerfile**
- ✅ Multi-stage build (builder + runtime)
- ✅ Python 3.12-slim base image
- ✅ Non-root user execution for security
- ✅ Optimized layer caching
- ✅ Poetry-based dependency installation
- ✅ Persistent data volume support

**docker-compose.yml**
- ✅ Production-ready configuration
- ✅ Environment variable management
- ✅ Health checks and resource limits
- ✅ Volume mounting for persistent data
- ✅ Logging configuration

**entrypoint.sh**
- ✅ Secret file expansion support
- ✅ Environment variable debugging
- ✅ Secure secret handling

### 3. CD Pipeline Features

**Container Registry Publishing**
- ✅ GitHub Container Registry (ghcr.io) integration
- ✅ Multi-architecture support (AMD64 + ARM64)
- ✅ Semantic versioning with automatic tagging
- ✅ Branch-specific image tags
- ✅ SHA-based immutable tags

**Security & Compliance**
- ✅ Artifact attestation for supply chain security
- ✅ SBOM (Software Bill of Materials) generation
- ✅ Container image testing before deployment
- ✅ Immutable digest-based references

**Deployment Automation**
- ✅ Automatic builds on code changes
- ✅ Release-triggered builds via git tags
- ✅ Pull request validation builds
- ✅ Manual workflow dispatch capability

### 3. Project Structure

**PYHABOT** is an async Python bot that monitors HardverApró (Hungarian classified ads site):

**Core Features:**
- Web scraping with aiohttp and BeautifulSoup
- Multiple integrations (Discord, Telegram, Terminal)
- TinyDB for data persistence
- Async/await architecture
- Configurable monitoring intervals
- Price change detection and notifications

**Key Technologies:**
- Python 3.11+
- discord.py 2.5.0
- telegram.py (git version)
- aiohttp for async HTTP
- BeautifulSoup4 for HTML parsing
- TinyDB for JSON storage
- Poetry for dependency management

---

## 🚀 Quick Start

### 1. Enable GitHub Container Registry

The workflow is ready to use! GitHub automatically provides the `GITHUB_TOKEN` secret with necessary permissions.

**First time setup:**
1. Push code to trigger the workflow
2. After successful build, the image will be at:
   ```
   ghcr.io/radamhu/pyhabot:latest
   ```

### 2. Pull and Run Your Image

```bash
# Pull the image
docker pull ghcr.io/radamhu/pyhabot:latest

# Run the container
docker run -d \
  -e INTEGRATION=terminal \
  -e PERSISTENT_DATA_PATH=/data \
  -v $(pwd)/persistent_data:/data \
  --name pyhabot \
  ghcr.io/radamhu/pyhabot:latest

# Check logs
docker logs -f pyhabot
```

### 3. Use with Docker Compose

Update your `docker-compose.yml`:
```yaml
services:
  pyhabot:
    image: ghcr.io/radamhu/pyhabot:latest
    environment:
      - INTEGRATION=${INTEGRATION:-terminal}
      - DISCORD_TOKEN=${DISCORD_TOKEN:-}
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN:-}
      - PERSISTENT_DATA_PATH=/data
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./persistent_data:/data
    restart: unless-stopped
```

### 4. Create a Release

```bash
# Tag a version
git tag v1.0.0
git push origin v1.0.0

# This triggers a build with multiple tags:
# - v1.0.0, 1.0, 1, latest
```

### 5. Monitor Workflow Runs

```bash
# Via GitHub CLI
gh run list

# Via web interface
# Go to: Actions tab in your GitHub repository
```

### 6. Local Development Setup

**Using Poetry (Recommended):**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run the bot
pyhabot run
```

### 7. Configuration

Create a `.env` file:
```bash
# Required: Integration type
INTEGRATION=discord  # or telegram, terminal

# Required: Authentication token
DISCORD_TOKEN=your_discord_bot_token
# OR
TELEGRAM_TOKEN=your_telegram_bot_token

# Optional: Logging
LOG_LEVEL=INFO
PERSISTENT_DATA_PATH=./persistent_data
```

---

## 📊 Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CODE PUSH/TAG                          │
│                  (master, main, v*)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐            ┌──────────────────┐
│   CI WORKFLOW   │            │ BUILD & PUSH     │
│                 │            │   WORKFLOW       │
│ • Test code     │            │                  │
│ • Run tests     │            │ • Build image    │
│ • Check types   │            │ • Multi-arch     │
│ • Coverage      │            │ • Push to ghcr   │
│ • Build pkg    │            │ • Test image     │
│ • Upload dist  │            │ • SBOM gen       │
└─────────────────┘            └────────┬─────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │  GHCR REGISTRY   │
                              │                  │
                              │  📦 PYHABOT     │
                              │  Image ready     │
                              │  to deploy      │
                              └────────┬─────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────┐
│                DEPLOYMENT OPTIONS                           │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    DOCKER    │  │  COMPOSE    │  │    LOCAL DEV        │  │
│  │             │  │             │  │                     │  │
│  │ • docker    │  │ • docker-   │  │ • poetry install    │  │
│  │   pull      │  │   compose   │  │ • poetry shell      │  │
│  │ • docker    │  │ • Multi-    │  │ • pyhabot run       │  │
│  │   run       │  │   service   │  │                     │  │
│  │ • Production│  │ • Production│  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration

### Required Repository Settings

**1. Workflow Permissions**
- Navigate to: Settings → Actions → General → Workflow permissions
- Select: ✅ **Read and write permissions**
- Enable: ✅ **Allow GitHub Actions to create and approve pull requests**

### Application Configuration

**Required Environment Variables:**
```bash
# Integration selection
INTEGRATION=discord          # or telegram, terminal

# Authentication tokens (based on integration)
DISCORD_TOKEN=your_discord_bot_token
TELEGRAM_TOKEN=your_telegram_bot_token

# Data persistence
PERSISTENT_DATA_PATH=./persistent_data
```

**Optional Environment Variables:**
```bash
# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR

# Webhook notifications
WEBHOOK_URL=https://your-webhook-url.com

# Timezone
TZ=Europe/Budapest
```

### Optional Secrets

**For Codecov (optional):**
```
CODECOV_TOKEN=your-codecov-token
```

To add secrets:
1. Settings → Secrets and variables → Actions
2. New repository secret
3. Add name and value

---

## 🎯 Next Steps

### 1. Test the Workflows

```bash
# Trigger CI
git commit --allow-empty -m "Test CI pipeline"
git push origin main

# Check the Actions tab on GitHub
```

### 2. Add Status Badges

Add to your `README.md`:

```markdown
## Build Status

![CI](https://github.com/radamhu/PYHABOT/workflows/CI/badge.svg)
![Build and Push](https://github.com/radamhu/PYHABOT/workflows/Build%20and%20Push%20Docker%20Image/badge.svg)
```

### 3. Set Up Branch Protection

Recommended settings for `main`/`master` branch:
- ✅ Require status checks to pass before merging
  - ✅ CI (test job)
  - ✅ Build and Push Docker Image
- ✅ Require branches to be up to date before merging

### 4. Consider Adding

**Dependabot for automatic updates:**
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
```

**Enhanced Testing:**
- Integration tests for Discord/Telegram
- End-to-end tests with fixtures
- Performance benchmarks

**Auto-deployment:**
- Deploy to staging environments on PR
- Automatic production deployment on tag
- Rollback capabilities

---

## 📈 Performance Optimizations

### CI Pipeline Improvements

**Current optimizations:**
1. ✅ Multi-layer caching (pip and Poetry)
2. ✅ Matrix testing with Python 3.11/3.12
3. ✅ Parallel job execution
4. ✅ Artifact retention management
5. ✅ Dependency caching based on hash files

**Expected CI times:**
- First run: ~3-5 minutes
- Cached runs: ~1-3 minutes
- No dependency changes: ~30-60 seconds

### Docker Build Optimizations

**Multi-stage build benefits:**
1. ✅ Smaller final image size
2. ✅ Reduced attack surface
3. ✅ Better layer caching
4. ✅ Separation of build/runtime dependencies

**Expected build times:**
- First build: ~2-3 minutes
- Cached builds: ~30-60 seconds

### CD Pipeline Optimizations

**Multi-architecture builds:**
1. ✅ AMD64 and ARM64 support
2. ✅ GitHub Actions cache integration
3. ✅ BuildKit inline caching
4. ✅ Parallel platform builds

**Registry publishing:**
1. ✅ GitHub Container Registry (ghcr.io)
2. ✅ Semantic versioning tags
3. ✅ Branch-specific tags
4. ✅ SHA-based immutable tags

### Cache Hit Rates

Monitor cache effectiveness:
```bash
# Check workflow run details
# Look for "Cache restored from key: ..." messages
# Poetry cache: venv-${{ runner.os }}-${{ matrix.python-version }}
# Pip cache: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
# Docker cache: type=gha,mode=max
```

---

## 🐛 Troubleshooting

### Issue: "Permission denied while pushing to ghcr.io"

**Solution:**
```bash
# Check workflow permissions:
Settings → Actions → General → Workflow permissions
→ Select "Read and write permissions"
```

### Issue: "Poetry install fails in CI"

**Solution:**
```bash
# Check poetry.lock exists and is up to date
git add poetry.lock
git commit -m "Add poetry.lock"
git push

# Or regenerate lock file
poetry lock --no-update
```

### Issue: "Tests fail with import errors"

**Solution:**
```bash
# Check package installation in CI
# Ensure pyproject.toml has correct package configuration
# Verify src/pyhabot structure is correct

# Local test:
poetry install
poetry run pytest tests/
```

### Issue: "Docker build fails with permission errors"

**Solution:**
```bash
# Check entrypoint.sh permissions
chmod +x entrypoint.sh

# Ensure non-root user setup is correct
# Verify volume permissions for persistent data
```

### Issue: "Bot fails to start with missing tokens"

**Solution:**
```bash
# Check environment variables
echo $INTEGRATION
echo $DISCORD_TOKEN
echo $TELEGRAM_TOKEN

# Ensure .env file is properly configured
# For Docker, check docker-compose environment section
```

### Issue: "Multi-architecture build fails"

**Solution:**
```bash
# Check Docker Buildx setup
docker buildx ls
docker buildx create --use

# Ensure QEMU emulation is available
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

### Issue: "CI cache miss on every run"

**Solution:**
```bash
# Check cache key format
# Ensure poetry.lock and pyproject.toml are included in hash
# Verify cache version compatibility
# Check Docker BuildKit cache settings
```

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [TinyDB Documentation](https://tinydb.readthedocs.io/)
- [PYHABOT Repository](https://github.com/radamhu/PYHABOT)

---

## ✅ Checklist

Before committing these changes:

- [ ] Review CI and CD workflow files for correctness
- [ ] Verify repository settings (workflow permissions)
- [ ] Test workflows by pushing to a test branch
- [ ] Add status badges to README.md
- [ ] Set up branch protection rules (optional)
- [ ] Configure Dependabot (optional)
- [ ] Configure Codecov if desired (optional)
- [ ] Test local development setup with Poetry
- [ ] Verify Docker configuration works correctly
- [ ] Test multi-architecture builds
- [ ] Verify container registry publishing

---

## 🎉 Success Criteria

Your CI/CD is working when:

1. ✅ Pushing to `main`/`master` triggers both CI and CD workflows
2. ✅ Tests run and pass on both Python 3.11 and 3.12
3. ✅ Code quality checks (Ruff, MyPy) pass
4. ✅ Coverage reports are generated and uploaded
5. ✅ Package artifacts are built and uploaded
6. ✅ Docker image is built and pushed to ghcr.io
7. ✅ Multi-architecture images (AMD64 + ARM64) are created
8. ✅ Image tags are generated correctly (branch, tag, SHA)
9. ✅ SBOM and attestations are generated
10. ✅ Local development setup works with Poetry
11. ✅ Bot starts correctly with proper configuration
12. ✅ Container can be pulled and run successfully

---

**Updated by:** GitHub Copilot  
**Date:** October 31, 2025  
**Repository:** PYHABOT

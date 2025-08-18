# WSL2 Development Setup Guide for GitGuard

This guide provides a battle-tested WSL2 setup for developing GitGuard on Windows, ensuring Makefiles, shells, and Docker behave like they do on native Linux.

## Why WSL2 (and not PowerShell for builds)

- **Native POSIX tools**: Make + POSIX tools behave natively. No CRLF vs LF drama; no quoting oddities; bash-isms Just Work™
- **Performance**: WSL2 runs a real Linux kernel with near-native filesystem speed inside Linux
- **Docker Integration**: Docker Desktop integrates with WSL2, so Linux containers run without a heavy VM hop

## The Golden Path (Step-by-Step)

### 1) Install & Pin Basics

On Windows (admin PowerShell, just this once):

```powershell
wsl --install -d Ubuntu-24.04
wsl --set-default-version 2
```

Create `C:\Users\Ava\.wslconfig` to keep WSL well-behaved:

```ini
[wsl2]
memory=8GB
processors=4
swap=4GB
localhostForwarding=true
```

Then:

```powershell
wsl --shutdown
```

### 2) Minimal Linux Tuning (inside Ubuntu)

Create `/etc/wsl.conf` to avoid Windows-path pollution and enable sane mounts:

```ini
[interop]
appendWindowsPath=false

[automount]
enabled=true
options=metadata
```

Apply and reboot WSL:

```bash
wsl.exe --shutdown
```

**Filesystem rule**: Keep your repos under `~/code` (Linux side), not under `/mnt/c/...`. Cross-OS IO is slower and causes edge-case bugs.

### 3) Core Packages + Dev Ergonomics

```bash
sudo apt update
sudo apt install -y build-essential git curl unzip zip pkg-config ca-certificates \
                    make gcc g++ python3 python3-venv python3-pip \
                    libssl-dev libffi-dev

# Optional: modern Zsh + fzf (nice quality-of-life)
sudo apt install -y zsh fzf
```

Increase file watchers (VS Code + big monorepos):

```bash
echo fs.inotify.max_user_watches=524288 | sudo tee /etc/sysctl.d/99-inotify.conf
sudo sysctl --system
```

### 4) Git + Line Endings (The Makefile Sanity Saver)

Inside WSL:

```bash
git config --global core.autocrlf false
git config --global core.eol lf
git config --global pull.rebase false
git config --global init.defaultBranch main
```

Add this once per repo to guarantee LF everywhere:

```gitattributes
# .gitattributes
* text=auto eol=lf
*.sh text eol=lf
Makefile text eol=lf
```

If you ever pulled with CRLF already:

```bash
sudo apt install -y dos2unix
find . -type f -name "*.sh" -o -name "Makefile" | xargs dos2unix
```

### 5) VS Code the Right Way

1. Install "WSL" extension on Windows
2. In WSL: from your repo folder, run `code .` (this installs the VS Code Server in WSL and opens the folder remotely)

**Recommended extensions** (install them in the WSL context):
- Makefile Tools
- Docker
- Dev Containers
- GitLens
- YAML
- EditorConfig
- Language packs: Python (Pylance, Black/Ruff), ESLint/Prettier, Go, Rust, etc.

**Helpful VS Code settings** (User or Workspace):

```json
{
  "files.eol": "\n",
  "terminal.integrated.defaultProfile.linux": "bash",
  "editor.formatOnSave": true,
  "git.detectSubmodules": true
}
```

## GitGuard-Specific Setup

After completing the above setup:

1. Clone the GitGuard repository to `~/code/gitguard` in WSL2
2. Install Python dependencies:
   ```bash
   cd ~/code/gitguard
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
3. Set up Docker (if using Docker Desktop, ensure WSL2 integration is enabled)
4. Run the project's Makefile commands natively:
   ```bash
   make test
   make build
   ```

## Troubleshooting

- **Line ending issues**: Ensure `.gitattributes` is properly configured and run `dos2unix` on affected files
- **Performance issues**: Keep repositories on the Linux filesystem (`~/code/`) rather than Windows mounts (`/mnt/c/`)
- **Docker issues**: Verify Docker Desktop has WSL2 integration enabled in settings
- **File watching limits**: Increase `fs.inotify.max_user_watches` if VS Code or build tools complain about file watching

## 7) Language/Tool Versioning (One Tool to Rule Them All)

For polyglot projects, install **mise** (formerly rtx) to manage Node, Python, Go, Java, etc., per-project:

```bash
curl https://mise.run | sh
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc
exec bash
mise install node@lts python@3.11 go@1.22  # example
```

Then drop a `.mise.toml` in each repo to pin versions.

If you live in Python-land, add **uv** for fast envs:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 8) Makefiles That Behave Across Machines

At the top of Makefiles that use Bashisms:

```makefile
SHELL := /usr/bin/env bash
```

Use parallelism reliably:

```makefile
# inside your Makefile
# default to all cores unless overridden
JOBS ?= $(shell nproc)
build:
	@echo "Building with $(JOBS) jobs"
	@$(MAKE) -C src -j $(JOBS)
```

And from the CLI:

```bash
make -j"$(nproc)"
```

## 9) Dev Containers (Optional but Powerful)

If you want 100% reproducible environments for the team, add a devcontainer. VS Code will auto-enter it inside WSL using Docker:

```
.devcontainer/
  devcontainer.json
  Dockerfile
```

**devcontainer.json** (minimal, sane defaults):

```json
{
  "name": "codessa-dev",
  "build": { "dockerfile": "Dockerfile" },
  "remoteUser": "vscode",
  "features": {},
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-vscode.makefile-tools",
        "ms-azuretools.vscode-docker",
        "tamasfe.even-better-toml",
        "esbenp.prettier-vscode",
        "ms-python.python",
        "charliermarsh.ruff"
      ],
      "settings": { "files.eol": "\n" }
    }
  },
  "mounts": ["source=${localWorkspaceFolder},target=/workspaces/${localWorkspaceFolderBasename},type=bind,consistency=cached"],
  "workspaceFolder": "/workspaces/${localWorkspaceFolderBasename}"
}
```

**Dockerfile** (Ubuntu base + build tools):

```dockerfile
FROM mcr.microsoft.com/devcontainers/base:ubuntu

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential make git curl unzip zip ca-certificates pkg-config \
    libssl-dev libffi-dev python3 python3-venv python3-pip \
 && rm -rf /var/lib/apt/lists/*

# Optional: mise for toolchains
RUN curl https://mise.run | sh && \
    echo 'eval "$(/root/.local/bin/mise activate bash)"' >> /etc/bash.bashrc

# Create non-root user `vscode` exists in base image; ensure ownership
USER vscode
WORKDIR /workspaces
```

This eliminates "it works on my laptop" by baking dependencies into a container while you still code in WSL.

## Common Foot-guns (And How to Sidestep Them)

- **CRLF gremlins**: Set `core.autocrlf=false` in WSL, enforce LF with `.gitattributes`. If you see `^M` or `/bin/bash^M`, run `dos2unix` on the offending files.

- **Wrong find/sed**: Ensure Linux commands come first on PATH. Our `/etc/wsl.conf` keeps Windows utilities off the path to avoid `find.exe` collisions.

- **Slow builds**: Make sure repos live under `~/code` (ext4). Don't build from `/mnt/c`.

- **Makefile Bashisms**: Always declare `SHELL := /usr/bin/env bash` if using arrays, `[[ ]]`, `set -euo pipefail`, etc.

## TL;DR Recommended "Optimal" Stack

- **Windows 11 + WSL2** (Ubuntu 24.04)
- **VS Code + Remote: WSL** (code lives in `~/code`)
- **Docker Desktop** with WSL backend (or Rancher Desktop)
- **mise** for toolchain pinning per project
- **Dev Containers** for fully reproducible teams/projects
- **Git LF discipline** (`.gitattributes` + global config)

This setup provides a clean, battle-tested environment for GitGuard development that leverages the best of both Windows and Linux ecosystems.
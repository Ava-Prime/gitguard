FROM mcr.microsoft.com/devcontainers/base:ubuntu

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3 python3-venv python3-pip make git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Optional: install uv (fast Python installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

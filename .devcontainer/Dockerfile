FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# The base image contains a Yarn APT source whose signing key may be stale.
# Remove that unrelated source before refreshing package metadata.
RUN find /etc/apt/sources.list.d -type f -print0 2>/dev/null \
    | xargs -0r grep -l 'dl\.yarnpkg\.com' \
    | xargs -r rm -f \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker.io docker-compose-v2 \
    && rm -rf /var/lib/apt/lists/*

# Codespaces exposes the host Docker daemon through the mounted socket.
RUN groupadd --system docker-host 2>/dev/null || true \
    && usermod -aG docker-host vscode

USER vscode

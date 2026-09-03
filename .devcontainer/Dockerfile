FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# The Codespaces Python image can contain a stale Yarn APT source.
# Remove that unrelated repository before any package metadata refresh.
RUN set -eux; \
    if [ -f /etc/apt/sources.list ]; then \
      sed -i '/dl\.yarnpkg\.com/d' /etc/apt/sources.list; \
    fi; \
    find /etc/apt/sources.list.d -type f -print0 2>/dev/null \
      | xargs -0r grep -l 'dl\.yarnpkg\.com' \
      | xargs -r rm -f

# Install only the client binaries. Codespaces supplies the Docker daemon.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends docker.io docker-compose-v2; \
    rm -rf /var/lib/apt/lists/*; \
    usermod -aG docker vscode

USER vscode

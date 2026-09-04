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

# Install the Android build toolchain required by the repository.
# CI builds the Android app with Java 17, so Codespaces must provide the same
# major JDK version for reproducible local verification.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends openjdk-17-jdk docker.io docker-compose-v2; \
    rm -rf /var/lib/apt/lists/*; \
    usermod -aG docker vscode

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

USER vscode

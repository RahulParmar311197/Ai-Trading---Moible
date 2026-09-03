FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# The Python base image can contain a Yarn APT source whose signing key is
# stale. Yarn is not required by this project, so remove only that source
# before devcontainer Features run apt-get update.
RUN set -eux; \
    if [ -f /etc/apt/sources.list ]; then \
      sed -i '/dl\.yarnpkg\.com/d' /etc/apt/sources.list; \
    fi; \
    find /etc/apt/sources.list.d -type f -print0 2>/dev/null \
      | xargs -0r grep -l 'dl\.yarnpkg\.com' \
      | xargs -r rm -f

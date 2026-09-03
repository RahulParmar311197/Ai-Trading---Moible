#!/usr/bin/env bash
set -euo pipefail

# Codespaces provides the Docker daemon on the host. The devcontainer mounts
# the host socket, so only the Docker CLI is required inside this container.
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI is not available in the base image; Codespaces host Docker cannot be used." >&2
  exit 1
fi

docker version

docker compose version

python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

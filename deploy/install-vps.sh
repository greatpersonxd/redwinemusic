#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"

if [[ "${EUID}" -ne 0 ]]; then
  SUDO="sudo"
else
  SUDO=""
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Missing ${PYTHON_BIN}. Install Python 3.12 and python3.12-venv first."
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Installing FFmpeg..."
  ${SUDO} apt-get update
  ${SUDO} apt-get install -y ffmpeg
fi

cd "${APP_DIR}"
if ! "${PYTHON_BIN}" -m venv --help >/dev/null 2>&1; then
  echo "Installing the Python venv module..."
  ${SUDO} apt-get update
  ${SUDO} apt-get install -y "${PYTHON_BIN}-venv"
fi

"${PYTHON_BIN}" -m venv .venv
".venv/bin/python" -m pip install --upgrade pip setuptools wheel
".venv/bin/python" -m pip install --requirement requirements.txt

if [[ ! -f .env ]]; then
  cp sample.env .env
  chmod 600 .env
  echo "Created ${APP_DIR}/.env. Fill it before starting the bot."
else
  chmod 600 .env
  echo "Existing .env kept unchanged."
fi

echo
echo "Installation complete."
echo "Start once with: ${APP_DIR}/.venv/bin/python -m SHIVMUSIC"
echo "Do not run a second copy of the bot while systemd or another shell loop is active."
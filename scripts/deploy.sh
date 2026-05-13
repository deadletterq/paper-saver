#!/usr/bin/env bash
# Deploy paper-saver to a Raspberry Pi on the local network.
#
# Reads RPI_HOST / RPI_USER / RPI_PASSWORD / TELEGRAM_BOT_TOKEN from .env.
# Installs system + Python deps if missing, mirrors the working tree to the Pi
# (rsync --delete so removed files disappear on the Pi too), writes/refreshes
# the systemd unit, then enables and (re)starts the service.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found at $PROJECT_DIR/.env" >&2
  echo "       Copy .env.example to .env and fill it in." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${TELEGRAM_BOT_TOKEN:?TELEGRAM_BOT_TOKEN must be set in .env}"
: "${RPI_USER:?RPI_USER must be set in .env}"
: "${RPI_HOST:?RPI_HOST must be set in .env}"
: "${RPI_PASSWORD:?RPI_PASSWORD must be set in .env}"

REMOTE_DIR="${RPI_REMOTE_DIR:-/home/${RPI_USER}/paper-saver-bot}"
SERVICE_NAME="paper-saver"

command -v sshpass >/dev/null 2>&1 || {
  echo "ERROR: sshpass is required." >&2
  echo "       macOS: brew install hudochenkov/sshpass/sshpass" >&2
  echo "       Linux: sudo apt-get install sshpass" >&2
  exit 1
}
command -v rsync >/dev/null 2>&1 || { echo "ERROR: rsync is required" >&2; exit 1; }

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o ServerAliveInterval=30)

# Run a heredoc on the Pi with SUDO_PW exported into the remote shell.
remote_run() {
  SSHPASS="$RPI_PASSWORD" sshpass -e ssh "${SSH_OPTS[@]}" \
    "${RPI_USER}@${RPI_HOST}" \
    "SUDO_PW=$(printf %q "$RPI_PASSWORD") bash -s"
}

remote_cmd() {
  SSHPASS="$RPI_PASSWORD" sshpass -e ssh "${SSH_OPTS[@]}" \
    "${RPI_USER}@${RPI_HOST}" "$@"
}

remote_rsync() {
  SSHPASS="$RPI_PASSWORD" sshpass -e rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "$@"
}

echo "==> Verifying SSH to ${RPI_USER}@${RPI_HOST}"
remote_cmd true

echo "==> Ensuring system packages and uv are installed on the Pi"
remote_run <<'REMOTE'
set -euo pipefail
sudo_run() { echo "$SUDO_PW" | sudo -S -p '' "$@"; }

PKGS=(python3-venv libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libharfbuzz0b rsync curl)
MISSING=()
for p in "${PKGS[@]}"; do
  dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p")
done
if (( ${#MISSING[@]} > 0 )); then
  echo "   installing: ${MISSING[*]}"
  sudo_run apt-get update
  sudo_run apt-get install -y "${MISSING[@]}"
else
  echo "   apt packages already present"
fi

if ! command -v uv >/dev/null 2>&1 && ! [[ -x "$HOME/.local/bin/uv" ]]; then
  echo "   installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
else
  echo "   uv already present"
fi
REMOTE

echo "==> Ensuring remote dir exists: $REMOTE_DIR"
remote_cmd "mkdir -p '$REMOTE_DIR'"

echo "==> Syncing source tree (rsync --delete; removed files vanish on the Pi)"
remote_rsync \
  --filter=':- .gitignore' \
  --exclude '.git/' \
  --exclude '.python-version' \
  ./ "${RPI_USER}@${RPI_HOST}:${REMOTE_DIR}/"

echo "==> Pushing .env (only bot-relevant vars; RPi credentials are not sent)"
TMP_ENV="$(mktemp)"
trap 'rm -f "$TMP_ENV"' EXIT
printf 'TELEGRAM_BOT_TOKEN=%s\n' "$TELEGRAM_BOT_TOKEN" > "$TMP_ENV"
remote_rsync --chmod=F600 "$TMP_ENV" "${RPI_USER}@${RPI_HOST}:${REMOTE_DIR}/.env"

echo "==> Installing Python deps on the Pi (uv sync)"
remote_run <<REMOTE
set -euo pipefail
export PATH="\$HOME/.local/bin:\$PATH"
cd "$REMOTE_DIR"
uv sync
REMOTE

echo "==> Writing systemd unit and (re)starting service"
remote_run <<REMOTE
set -euo pipefail
sudo_run() { echo "\$SUDO_PW" | sudo -S -p '' "\$@"; }

UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
TMP_UNIT="\$(mktemp)"
cat >"\$TMP_UNIT" <<UNIT
[Unit]
Description=Paper-Saver Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RPI_USER}
WorkingDirectory=${REMOTE_DIR}
EnvironmentFile=${REMOTE_DIR}/.env
ExecStart=${REMOTE_DIR}/.venv/bin/paper-saver
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

sudo_run install -m 0644 "\$TMP_UNIT" "\$UNIT_PATH"
rm -f "\$TMP_UNIT"
sudo_run systemctl daemon-reload
sudo_run systemctl enable "${SERVICE_NAME}" >/dev/null
sudo_run systemctl restart "${SERVICE_NAME}"

sleep 1
sudo_run systemctl --no-pager --lines=0 status "${SERVICE_NAME}" || true
REMOTE

echo
echo "==> Deploy complete."
echo "    Logs:  ssh ${RPI_USER}@${RPI_HOST} 'journalctl -u ${SERVICE_NAME} -f'"

#!/bin/sh
set -eu

# Beginner installer for TeleCloud-Downloader (Ubuntu/Debian).
# This script is idempotent and safe to rerun.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR="$SCRIPT_DIR"
ENV_FILE="$PROJECT_DIR/.env"
COLAB_DEFAULT_URL="https://colab.research.google.com/drive/1Ltyqs4i0UAuR6FpBrn3ygMuqlnPo_igV?usp=sharing"

if [ -t 1 ]; then
  C_RESET="$(printf '\033[0m')"
  C_BLUE="$(printf '\033[34m')"
  C_GREEN="$(printf '\033[32m')"
  C_YELLOW="$(printf '\033[33m')"
  C_RED="$(printf '\033[31m')"
else
  C_RESET=""
  C_BLUE=""
  C_GREEN=""
  C_YELLOW=""
  C_RED=""
fi

log_step() { printf "%s==> %s%s\n" "$C_BLUE" "$1" "$C_RESET"; }
log_ok() { printf "%sOK:%s %s\n" "$C_GREEN" "$C_RESET" "$1"; }
log_warn() { printf "%sWARN:%s %s\n" "$C_YELLOW" "$C_RESET" "$1"; }
log_err() { printf "%sERROR:%s %s\n" "$C_RED" "$C_RESET" "$1" >&2; }
die() { log_err "$1"; exit 1; }

if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  else
    die "This script needs root privileges. Install sudo or run as root."
  fi
fi

run_root() {
  if [ -n "$SUDO" ]; then
    "$SUDO" "$@"
  else
    "$@"
  fi
}

APT_UPDATED=0
apt_install() {
  if [ "$APT_UPDATED" -eq 0 ]; then
    run_root apt-get update -y
    APT_UPDATED=1
  fi
  run_root apt-get install -y "$@"
}

has_cmd() { command -v "$1" >/dev/null 2>&1; }

ensure_dir_path() {
  path="$1"
  if [ -e "$path" ] && [ ! -d "$path" ]; then
    die "Path '$path' must be a directory, but a file exists there."
  fi
  mkdir -p "$path"
}

ensure_regular_file() {
  path="$1"
  default_content="$2"
  if [ -e "$path" ] && [ -d "$path" ]; then
    die "Path '$path' must be a file, but a directory exists there."
  fi
  if [ ! -e "$path" ]; then
    if [ -n "$default_content" ]; then
      printf "%s" "$default_content" > "$path"
    else
      : > "$path"
    fi
  fi
}

env_get() {
  key="$1"
  if [ ! -f "$ENV_FILE" ]; then
    return 1
  fi
  line="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 || true)"
  [ -n "$line" ] || return 1
  printf "%s" "${line#*=}"
}

env_set() {
  key="$1"
  value="$2"
  ensure_regular_file "$ENV_FILE" ""
  if grep -q -E "^${key}=" "$ENV_FILE"; then
    tmp_file="$(mktemp)"
    awk -v k="$key" -v v="$value" '
      BEGIN { done=0 }
      {
        if ($0 ~ ("^" k "=")) {
          if (!done) {
            print k "=" v
            done=1
          }
        } else {
          print $0
        }
      }
      END {
        if (!done) print k "=" v
      }
    ' "$ENV_FILE" > "$tmp_file"
    mv "$tmp_file" "$ENV_FILE"
  else
    printf "%s=%s\n" "$key" "$value" >> "$ENV_FILE"
  fi
}

prompt_value() {
  prompt="$1"
  secret="$2"
  while :; do
    if [ "$secret" = "1" ]; then
      printf "%s: " "$prompt"
      stty -echo
      IFS= read -r value
      stty echo
      printf "\n"
    else
      printf "%s: " "$prompt"
      IFS= read -r value
    fi
    if [ -n "$value" ]; then
      printf "%s" "$value"
      return 0
    fi
    log_warn "Value cannot be empty."
  done
}

ensure_required_env() {
  key="$1"
  label="$2"
  secret="$3"
  numeric="$4"
  existing="$(env_get "$key" || true)"
  if [ -n "$existing" ]; then
    log_ok "Using existing $key from .env"
    return 0
  fi
  while :; do
    value="$(prompt_value "$label" "$secret")"
    if [ "$numeric" = "1" ]; then
      case "$value" in
        *[!0-9]*)
          log_warn "$key must be numeric."
          continue
          ;;
      esac
    fi
    env_set "$key" "$value"
    return 0
  done
}

set_default_if_missing() {
  key="$1"
  value="$2"
  existing="$(env_get "$key" || true)"
  if [ -z "$existing" ]; then
    env_set "$key" "$value"
    log_ok "Set default $key=$value"
  fi
}

prompt_yes_no() {
  question="$1"
  default="${2:-n}"
  while :; do
    if [ "$default" = "y" ]; then
      printf "%s [Y/n]: " "$question"
    else
      printf "%s [y/N]: " "$question"
    fi
    IFS= read -r answer
    case "${answer:-$default}" in
      y|Y|yes|YES) return 0 ;;
      n|N|no|NO) return 1 ;;
      *) log_warn "Please answer y or n." ;;
    esac
  done
}

docker_compose_ok() {
  run_root docker compose version >/dev/null 2>&1
}

start_compose() {
  if docker_compose_ok; then
    run_root docker compose up -d --build
    run_root docker compose ps
    return 0
  fi
  if has_cmd docker-compose; then
    run_root docker-compose up -d --build
    run_root docker-compose ps
    return 0
  fi
  die "Neither 'docker compose' nor 'docker-compose' is available."
}

log_step "Checking project context"
cd "$PROJECT_DIR"
[ -f "$PROJECT_DIR/docker-compose.yml" ] || die "docker-compose.yml not found. Run this script from the project folder."
[ -f "$PROJECT_DIR/main.py" ] || die "main.py not found. Run this script from the project folder."

log_step "Checking operating system support"
[ -f /etc/os-release ] || die "Cannot detect OS. /etc/os-release not found."
# shellcheck disable=SC1091
. /etc/os-release
case "${ID:-}" in
  ubuntu|debian) ;;
  *)
    case "${ID_LIKE:-}" in
      *debian*|*ubuntu*) ;;
      *) die "Unsupported OS '$ID'. This installer supports Ubuntu/Debian only." ;;
    esac
    ;;
esac
log_ok "Supported OS detected: ${PRETTY_NAME:-$ID}"

log_step "Installing/checking system dependencies"
missing_tools=""
for tool in git curl unzip; do
  if ! has_cmd "$tool"; then
    missing_tools="$missing_tools $tool"
  fi
done
if [ -n "$missing_tools" ]; then
  # shellcheck disable=SC2086
  apt_install $missing_tools
fi

if ! has_cmd docker; then
  log_warn "Docker not found. Installing docker.io..."
  apt_install docker.io
fi

if ! docker_compose_ok; then
  log_warn "Docker Compose plugin not found. Installing..."
  if ! apt_install docker-compose-plugin; then
    log_warn "docker-compose-plugin package unavailable. Installing docker-compose fallback."
    apt_install docker-compose
  fi
fi

if has_cmd systemctl; then
  run_root systemctl enable --now docker >/dev/null 2>&1 || run_root systemctl start docker >/dev/null 2>&1 || true
else
  run_root service docker start >/dev/null 2>&1 || true
fi

run_root docker info >/dev/null 2>&1 || die "Docker daemon is not usable. Check docker service status and user permissions."
log_ok "Docker is ready."

log_step "Preparing required folders/files"
ensure_dir_path "$PROJECT_DIR/downloads"
ensure_dir_path "$PROJECT_DIR/cookies"
ensure_dir_path "$PROJECT_DIR/telegram-bot-api-data"
ensure_dir_path "$PROJECT_DIR/user_configs"
ensure_regular_file "$PROJECT_DIR/cookies_enabled.json" "{}"
ensure_regular_file "$PROJECT_DIR/rclone.conf" ""
log_ok "Paths and base files are ready."

log_step "Configuring .env (required values + safe defaults)"
ensure_regular_file "$ENV_FILE" ""

ensure_required_env "DOWNLOADER_BOT_TOKEN" "Enter DOWNLOADER_BOT_TOKEN (from @BotFather)" 0 0
ensure_required_env "BOT_PASSWORD" "Enter BOT_PASSWORD (users must send this to access bot)" 1 0
ensure_required_env "TELEGRAM_API_ID" "Enter TELEGRAM_API_ID (from my.telegram.org)" 0 1
ensure_required_env "TELEGRAM_API_HASH" "Enter TELEGRAM_API_HASH (from my.telegram.org)" 0 0
ensure_required_env "ADMIN_ID" "Enter ADMIN_ID (your Telegram numeric user id)" 0 1

set_default_if_missing "TELEGRAM_LOCAL" "1"
set_default_if_missing "REGISTRATION_OPEN" "false"
set_default_if_missing "MAX_DAILY_FILES" "20"
set_default_if_missing "MAX_DAILY_BYTES" "5368709120"
set_default_if_missing "MAX_CONCURRENT_DOWNLOADS" "2"
set_default_if_missing "COLAB_URL" "$COLAB_DEFAULT_URL"

log_ok ".env is configured."

log_step "Google Drive (rclone.conf) setup"
if [ -d "$PROJECT_DIR/rclone.conf" ]; then
  die "rclone.conf is a directory. Remove it and create a file named rclone.conf."
fi

if [ -s "$PROJECT_DIR/rclone.conf" ]; then
  log_ok "Existing rclone.conf file detected."
else
  if prompt_yes_no "Do you already have an rclone.conf file?" "n"; then
    while :; do
      printf "Enter full path to your rclone.conf: "
      IFS= read -r rclone_src
      [ -n "$rclone_src" ] || { log_warn "Path cannot be empty."; continue; }
      if [ ! -f "$rclone_src" ]; then
        log_warn "File not found: $rclone_src"
        continue
      fi
      cp "$rclone_src" "$PROJECT_DIR/rclone.conf"
      log_ok "Copied rclone.conf into project root."
      break
    done
  else
    # Critical guard: ensure file exists (not missing) so Docker does not create a directory on mount.
    touch "$PROJECT_DIR/rclone.conf"
    colab_url="$(env_get COLAB_URL || true)"
    [ -n "$colab_url" ] || colab_url="$COLAB_DEFAULT_URL"
    log_warn "Google Drive is skipped for now (Telegram-only mode will still work)."
    printf "\nFollow these steps later:\n"
    printf "1) Open your Colab link:\n   %s\n" "$colab_url"
    printf "2) Run it and download the generated rclone.conf file.\n"
    printf "3) Upload/copy that file to this server and replace:\n   %s/rclone.conf\n" "$PROJECT_DIR"
    printf "4) Re-run this script (or restart containers).\n\n"
  fi
fi

log_step "Starting services"
start_compose

printf "\n"
log_ok "Setup completed."
printf "Next checks:\n"
printf "  - docker compose ps\n"
printf "  - docker logs -f telegram-bot\n"
printf "  - docker logs -f telegram-bot-api\n"

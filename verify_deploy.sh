#!/usr/bin/env bash
# Post-deploy smoke test for the AtharvAyur API on EC2.
#
# Usage:
#   ./verify_deploy.sh                          # default host 3.144.81.108
#   ./verify_deploy.sh 3.144.81.108
#   EC2_HOST=ec2-....amazonaws.com ./verify_deploy.sh
#
# Optional (for Docker log check over SSH):
#   SSH_KEY=~/Downloads/Atharvayur.pem ./verify_deploy.sh
#   EC2_USER=ec2-user  (default)

set -euo pipefail

EC2_HOST="${1:-${EC2_HOST:-3.144.81.108}}"
EC2_USER="${EC2_USER:-ec2-user}"
API_PORT="${API_PORT:-8000}"
SSH_KEY="${SSH_KEY:-}"
REPO_PATH="${REPO_PATH:-~/AtharvAyur/backend}"

API_BASE="http://${EC2_HOST}:${API_PORT}"
FAILURES=()

log() { printf '%s\n' "$*"; }
fail() { FAILURES+=("$1"); log "FAIL: $1"; }

# Expand leading ~ in paths (env vars passed as ~/foo are not always expanded).
expand_path() {
  local p="$1"
  if [[ "$p" == "~/"* ]]; then
    printf '%s' "${HOME}/${p#~/}"
  elif [[ "$p" == "~" ]]; then
    printf '%s' "${HOME}"
  else
    printf '%s' "$p"
  fi
}

resolve_ssh_key() {
  local tried=()
  local candidate

  if [[ -n "${SSH_KEY:-}" ]]; then
    candidate="$(expand_path "$SSH_KEY")"
    tried+=("$candidate")
    if [[ -f "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
    fail "SSH_KEY is set to '${SSH_KEY}' (resolved: ${candidate}) but that file does not exist"
    return 1
  fi

  for candidate in \
    "${HOME}/Downloads/Atharvayur.pem" \
    "${HOME}/.ssh/Atharvayur.pem" \
    "${HOME}/.ssh/atharvayur.pem"; do
    tried+=("$candidate")
    if [[ -f "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done

  fail "SSH key not found. Tried: ${tried[*]}"
  fail "Download Atharvayur.pem from AWS (EC2 → Key pairs) or set SSH_KEY=/full/path/to/key.pem"
  fail "To skip log check: SKIP_SSH_LOGS=1 ./verify_deploy.sh"
  return 1
}

# --- 1. /health ---
log "Checking ${API_BASE}/health ..."
HEALTH_BODY=""
if ! HEALTH_BODY="$(curl -fsS --connect-timeout 10 --max-time 30 "${API_BASE}/health" 2>&1)"; then
  fail "GET /health unreachable: ${HEALTH_BODY}"
else
  if printf '%s' "$HEALTH_BODY" | grep -qE '"status"[[:space:]]*:[[:space:]]*"ok"'; then
    log "OK: /health returned status ok"
  else
    fail "GET /health unexpected body: ${HEALTH_BODY}"
  fi
fi

# --- 2. /openapi.json contains api/v1/chat ---
log "Checking ${API_BASE}/openapi.json for api/v1/chat ..."
OPENAPI_BODY=""
if ! OPENAPI_BODY="$(curl -fsS --connect-timeout 10 --max-time 60 "${API_BASE}/openapi.json" 2>&1)"; then
  fail "GET /openapi.json unreachable: ${OPENAPI_BODY}"
else
  if printf '%s' "$OPENAPI_BODY" | grep -q 'api/v1/chat'; then
    log "OK: OpenAPI spec includes api/v1/chat"
  else
    fail "OpenAPI spec does not contain api/v1/chat (v2 route may not be deployed)"
  fi
fi

# --- 3. Docker logs on EC2 — no 500s in last 5 minutes ---
if [[ "${SKIP_SSH_LOGS:-0}" == "1" ]]; then
  log "Skipping SSH log check (SKIP_SSH_LOGS=1)"
else
  log "Checking API logs on ${EC2_USER}@${EC2_HOST} (last 5m) ..."
  RESOLVED_KEY=""
  if RESOLVED_KEY="$(resolve_ssh_key)"; then
    chmod 400 "$RESOLVED_KEY" 2>/dev/null || true
    LOGS=""
    REMOTE_REPO="$(expand_path "$REPO_PATH")"
    if ! LOGS="$(ssh -i "$RESOLVED_KEY" \
      -o BatchMode=yes \
      -o ConnectTimeout=15 \
      -o StrictHostKeyChecking=accept-new \
      "${EC2_USER}@${EC2_HOST}" \
      "cd ${REMOTE_REPO} && docker compose -f docker-compose.aws.yml logs --since 5m api 2>&1" 2>&1)"; then
      fail "SSH or docker logs failed: ${LOGS}"
    else
      MATCHES="$(printf '%s' "$LOGS" | grep -E '500|Internal Server Error' || true)"
      if [[ -n "$MATCHES" ]]; then
        fail "Found 500 / Internal Server Error in api logs (last 5m):"
        printf '%s\n' "$MATCHES" | head -20
      else
        log "OK: no 500 errors in api logs (last 5m)"
      fi
    fi
  fi
fi

# --- Result ---
if ((${#FAILURES[@]} > 0)); then
  log ""
  log "Deploy verification failed (${#FAILURES[@]} check(s)):"
  for msg in "${FAILURES[@]}"; do
    log "  - ${msg}"
  done
  exit 1
fi

log ""
log "Success"

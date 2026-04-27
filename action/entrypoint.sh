#!/usr/bin/env bash
set -euo pipefail

read_input() {
  local underscored="$1"
  local hyphenated="$2"
  local value
  value="$(printenv "INPUT_${underscored}" 2>/dev/null || true)"
  if [ -z "${value}" ]; then
    value="$(printenv "INPUT_${hyphenated}" 2>/dev/null || true)"
  fi
  printf '%s' "${value}"
}

is_true() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    true|1|yes|y|on) return 0 ;;
    *) return 1 ;;
  esac
}

json_value() {
  python3 - "$1" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(0)
print(payload.get("posture", ""))
PY
}

PR_URL="$(read_input PR_URL PR-URL)"
GUARDRAILS_PATH="$(read_input GUARDRAILS_PATH GUARDRAILS-PATH)"
RUN_CHECKS="$(read_input RUN_CHECKS RUN-CHECKS)"
POST_COMMENT="$(read_input POST_COMMENT POST-COMMENT)"
LLM_REVIEW="$(read_input LLM_REVIEW LLM-REVIEW)"
LLM_COMMAND="$(read_input LLM_COMMAND LLM-COMMAND)"

if [ -z "${GH_TOKEN:-}" ] && [ -n "${GITHUB_TOKEN:-}" ]; then
  export GH_TOKEN="${GITHUB_TOKEN}"
fi

GUARDRAILS_PATH="${GUARDRAILS_PATH:-forgebench.yml}"
OUT_DIR="${GITHUB_WORKSPACE:-$PWD}/forgebench-output"

if [ -z "${PR_URL}" ] && [ -n "${GITHUB_EVENT_PATH:-}" ] && [ -f "${GITHUB_EVENT_PATH}" ]; then
  PR_URL="$(python3 - "${GITHUB_EVENT_PATH}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
pull_request = payload.get("pull_request") or {}
print(pull_request.get("html_url") or "")
PY
)"
fi

if [ -z "${PR_URL}" ]; then
  echo "ForgeBench action error: pr-url is required outside pull_request events." >&2
  exit 2
fi

command=(forgebench review-pr "${PR_URL}" --repo "${GITHUB_WORKSPACE:-$PWD}" --out "${OUT_DIR}")

if [ -f "${GITHUB_WORKSPACE:-$PWD}/${GUARDRAILS_PATH}" ]; then
  command+=(--guardrails "${GITHUB_WORKSPACE:-$PWD}/${GUARDRAILS_PATH}")
elif [ -f "${GUARDRAILS_PATH}" ]; then
  command+=(--guardrails "${GUARDRAILS_PATH}")
else
  echo "ForgeBench action: guardrails file not found at ${GUARDRAILS_PATH}; using generic review rules."
fi

if is_true "${RUN_CHECKS}"; then
  command+=(--run-checks)
fi

if is_true "${POST_COMMENT}"; then
  command+=(--post-comment)
else
  command+=(--dry-run)
fi

if is_true "${LLM_REVIEW}"; then
  command+=(--llm-review)
  if [ -n "${LLM_COMMAND}" ]; then
    command+=(--llm-provider command --llm-command "${LLM_COMMAND}")
  fi
fi

echo "Running: ${command[*]}"
"${command[@]}"

REPORT_JSON="${OUT_DIR}/forgebench-report.json"
REPORT_MD="${OUT_DIR}/forgebench-report.md"
PR_COMMENT="${OUT_DIR}/pr-comment.md"
POSTURE="$(json_value "${REPORT_JSON}")"

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  {
    echo "posture=${POSTURE}"
    echo "report-path=${REPORT_MD}"
    echo "pr-comment-path=${PR_COMMENT}"
  } >> "${GITHUB_OUTPUT}"
fi

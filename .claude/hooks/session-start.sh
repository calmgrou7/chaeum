#!/bin/bash
# Claude Code 클라우드 세션 시작 시 Python 의존성을 설치합니다.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

python3 -m pip install --quiet --disable-pip-version-check --break-system-packages \
  -r requirements.txt ruff

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PYTHONPATH="."' >> "$CLAUDE_ENV_FILE"
fi

#!/bin/bash
# Claude Code 클라우드 세션 시작 시 Python 의존성을 설치합니다.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# 재개·compact 등으로 다시 실행될 때는 이미 설치돼 있으면 건너뜀 (네트워크 없이 즉시 종료)
if python3 -c "import importlib.util as u, sys; sys.exit(any(u.find_spec(m) is None for m in ('anthropic', 'requests', 'bs4', 'pandas', 'jinja2', 'dotenv')))" \
  && command -v ruff >/dev/null 2>&1; then
  :
else
  python3 -m pip install --quiet --disable-pip-version-check --break-system-packages \
    -r requirements.txt ruff
fi

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PYTHONPATH="."' >> "$CLAUDE_ENV_FILE"
fi

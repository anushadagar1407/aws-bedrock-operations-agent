#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python_bin="${PYTHON_BIN:-.venv13/bin/python}"
if [[ ! -x "$python_bin" ]]; then
  python_bin="python3"
fi

"$python_bin" -m pytest -q
"$python_bin" -m ruff check src tests evaluations
npm --prefix infra test -- --runInBand
npm --prefix infra run typecheck
npm --prefix infra run synth >/dev/null
npm --prefix web test -- --run
npm --prefix web run typecheck
npm --prefix web run build

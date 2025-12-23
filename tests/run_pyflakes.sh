#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_ROOT="${ROOT_DIR}"
OUT_FILE="${ROOT_DIR}/tests/pyflakes.txt"

cd "${PYTHON_ROOT}"
pyflakes $(find "${PYTHON_ROOT}" \
	-type d -name "legacy" -prune -o \
	-type f -name "*.py" -print) > "${OUT_FILE}" 2>&1 || true
RESULT=$(wc -l < "${OUT_FILE}")
if [ "${RESULT}" -eq 0 ]; then
	echo "No errors found!!!"
	exit 0
fi
echo "Found ${RESULT} pyflakes errors"
exit 1

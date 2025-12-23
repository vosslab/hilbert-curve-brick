#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMP_DIR="$(mktemp -d)"

cleanup() {
	rm -rf "${TEMP_DIR}"
}
trap cleanup EXIT

python3 "${ROOT_DIR}/hilbert-curve-brick.py" \
	-d 2 \
	-o "${TEMP_DIR}" \
	--no-grid \
	-b 1 \
	-e 3

PNG_COUNT=$(ls "${TEMP_DIR}"/*.png 2>/dev/null | wc -l)
if [ "${PNG_COUNT}" -lt 1 ]; then
	echo "Smoke test failed: no PNG files were created."
	exit 1
fi

echo "Smoke test passed: ${PNG_COUNT} PNG files created."

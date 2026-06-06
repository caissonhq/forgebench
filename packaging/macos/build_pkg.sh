#!/usr/bin/env bash
# Build a macOS .pkg installer from a binary bundle directory.
set -euo pipefail

VERSION="${1:?Usage: build_pkg.sh VERSION BUNDLE_DIR}"
BUNDLE_DIR="${2:?Usage: build_pkg.sh VERSION BUNDLE_DIR}"
OUT_DIR="${3:-dist}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STAGE="${OUT_DIR}/pkg-root"
PKG_ROOT="${STAGE}/opt/forgebench"
IDENTIFIER="dev.forgebench.pkg"
OUTPUT="${OUT_DIR}/forgebench-${VERSION}-macos.pkg"

rm -rf "${STAGE}"
mkdir -p "${PKG_ROOT}/bin"
cp -R "${BUNDLE_DIR}/venv" "${PKG_ROOT}/"
cp "${BUNDLE_DIR}/bin/forgebench" "${PKG_ROOT}/bin/forgebench"
chmod +x "${PKG_ROOT}/bin/forgebench"

cat > "${STAGE}/forgebench-launcher" <<'EOF'
#!/usr/bin/env bash
export FORGEBENCH_INSTALL=bundle
exec /opt/forgebench/venv/bin/python -m forgebench.cli "$@"
EOF
chmod +x "${STAGE}/forgebench-launcher"
cp "${STAGE}/forgebench-launcher" "${PKG_ROOT}/bin/forgebench"

POSTINSTALL="${OUT_DIR}/postinstall"
cat > "${POSTINSTALL}" <<'EOF'
#!/bin/bash
ln -sf /opt/forgebench/bin/forgebench /usr/local/bin/forgebench 2>/dev/null || true
EOF
chmod +x "${POSTINSTALL}"

pkgbuild \
  --root "${PKG_ROOT}" \
  --identifier "${IDENTIFIER}" \
  --version "${VERSION}" \
  --install-location "/opt/forgebench" \
  --scripts "${OUT_DIR}" \
  "${OUTPUT}.component.pkg"

productbuild \
  --package "${OUTPUT}.component.pkg" \
  "${OUTPUT}"

echo "Built ${OUTPUT}"
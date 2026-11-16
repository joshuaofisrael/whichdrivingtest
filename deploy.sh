#!/bin/sh
# Build, QA, and the legal gate. Does not commit and does not ping IndexNow.
# ./deploy.sh           preview QA. Passes while GA4_ID is still empty.
# ./deploy.sh --launch  launch build. Fails until GA4_ID is a G- measurement id,
#                       and fails if any page lacks the Cloudflare beacon or the GA4 loader.
set -e
cd "$(dirname "$0")"
LAUNCH=0
if [ "${1:-}" = "--launch" ]; then
  LAUNCH=1
fi
if [ "$LAUNCH" = 1 ]; then
  if ! python3 -c 'import sys; sys.path.insert(0,"_build"); from config import NOINDEX; sys.exit(1 if NOINDEX else 0)'; then
    echo "Launch refused: set NOINDEX = False in _build/config.py"
    exit 1
  fi
fi
if ls _research/b*.json >/dev/null 2>&1; then
  python3 _build/verify_quotes.py
fi
python3 _build/build.py
if [ "$LAUNCH" = 1 ]; then
  python3 _build/check.py --launch
else
  python3 _build/check.py
fi
python3 _build/legal_gate.py check --no-queue
echo "build ok"

#!/bin/sh
# Build and check. Does not commit. Refuses to ping IndexNow while noindex is on.
set -e
cd "$(dirname "$0")"
if ls _research/b*.json >/dev/null 2>&1; then
  python3 _build/verify_quotes.py
fi
python3 _build/build.py
python3 _build/check.py

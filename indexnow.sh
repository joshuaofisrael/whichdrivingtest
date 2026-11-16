#!/bin/sh
# Ping IndexNow after the domain is live. Refuses while NOINDEX is still on.
cd "$(dirname "$0")" || exit 1
if python3 -c 'import sys; sys.path.insert(0,"_build"); from config import NOINDEX; sys.exit(0 if NOINDEX else 1)'; then
  echo "IndexNow skipped: NOINDEX is still true. Turn it off only when whichdrivingtest.com is live."
  exit 0
fi
python3 - << 'PY'
import json, urllib.request, pathlib, sys
key = pathlib.Path("_build/config.py").read_text()
# key file is served at the apex
sys.path.insert(0, "_build")
from config import INDEXNOW_KEY, DOMAIN
urls = []
text = pathlib.Path("sitemap.xml").read_text()
import re
urls = re.findall(r"<loc>(.*?)</loc>", text)
body = json.dumps({"host": "whichdrivingtest.com", "key": INDEXNOW_KEY, "keyLocation": f"https://whichdrivingtest.com/{INDEXNOW_KEY}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as res:
        print(res.status)
except Exception as exc:
    print(exc)
    sys.exit(1)
PY

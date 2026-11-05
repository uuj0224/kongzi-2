"""Fetch the same BGE model from ModelScope, verify SHA256, never execute remote code."""
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.parse
import time

def fetch(url):
    for attempt in range(3):
        try:
            return urllib.request.urlopen(url, timeout=180).read()
        except (OSError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


ROOT = Path(__file__).resolve().parents[1]
REVISION = "02ed473a14d4a4b3b9a61399080c77ccb485820b"
BASE = "https://modelscope.cn/api/v1/models/BAAI/bge-small-zh-v1.5/repo/"
TARGET = ROOT / "data/models/bge-small-zh-v1.5"

if __name__ == "__main__":
    query = urllib.parse.urlencode({"Revision":REVISION,"Recursive":"true"})
    manifest = json.loads(fetch(BASE + "files?" + query))
    TARGET.mkdir(parents=True, exist_ok=True)
    for item in manifest["Data"]["Files"]:
        name = item["Path"]
        if item["Type"] != "blob" or name == "pytorch_model.bin" or name.startswith("."):
            continue
        dest = TARGET / name
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == item["Sha256"]:
            continue
        url = BASE + "files?" + urllib.parse.urlencode({"Revision":REVISION,"FilePath":name})
        content = fetch(url)
        if hashlib.sha256(content).hexdigest() != item["Sha256"]:
            raise ValueError("Checksum mismatch: " + name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        print(name, len(content), flush=True)
    (TARGET / "download_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print("Verified model saved to", TARGET)

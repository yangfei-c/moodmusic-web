from pathlib import Path
import os
import urllib.request

PROJECT_ROOT = Path("/workspace")
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "semantic_db.json": os.environ.get("SEMANTIC_DB_URL"),
    "last.ckpt": os.environ.get("TEXT_CKPT_URL"),
}

for filename, url in FILES.items():
    if not url:
        raise RuntimeError(f"Missing environment variable for {filename}")

    target = DATA_DIR / filename

    if target.exists() and target.stat().st_size > 0:
        print(f"{filename} already exists, skip download.")
        continue

    print(f"Downloading {filename} from {url}")
    urllib.request.urlretrieve(url, target)
    print(f"Saved to {target}, size={target.stat().st_size}")
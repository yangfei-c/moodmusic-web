from __future__ import annotations

import os
import sys
import time
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", "/workspace"))
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RUNTIME_FILES = {
    "semantic_db.json": os.environ.get("SEMANTIC_DB_URL"),
    "last.ckpt": os.environ.get("TEXT_CKPT_URL"),
}


def download_file(url: str, target: Path, retries: int = 3) -> None:
    for attempt in range(1, retries + 1):
        try:
            print(f"Downloading {target.name} from {url}", flush=True)
            with urllib.request.urlopen(url, timeout=120) as response:
                total = response.headers.get("Content-Length")
                tmp_target = target.with_suffix(target.suffix + ".tmp")
                downloaded = 0
                with open(tmp_target, "wb") as f:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            print(
                                f"{target.name}: {downloaded / 1024 / 1024:.1f} MB / {int(total) / 1024 / 1024:.1f} MB",
                                flush=True,
                            )
                tmp_target.replace(target)
            print(f"Saved {target} ({target.stat().st_size / 1024 / 1024:.1f} MB)", flush=True)
            return
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"Attempt {attempt}/{retries} failed for {target.name}: {exc}", flush=True)
            if attempt == retries:
                raise
            time.sleep(5 * attempt)


def main() -> int:
    missing = [name for name, url in RUNTIME_FILES.items() if not url]
    if missing:
        print(
            "Missing environment variables for: "
            + ", ".join(missing)
            + ". Required: SEMANTIC_DB_URL and TEXT_CKPT_URL",
            flush=True,
        )
        return 1

    for filename, url in RUNTIME_FILES.items():
        target = DATA_DIR / filename
        if target.exists() and target.stat().st_size > 0:
            print(f"{filename} already exists at {target}; skip download.", flush=True)
            continue
        download_file(url, target)

    print("Runtime data is ready.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

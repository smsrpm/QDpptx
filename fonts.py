"""Install fonts that decks commonly use but Linux servers lack, so LibreOffice
lays text out with the same widths and line breaks as PowerPoint.

1. Microsoft's freely distributable "core fonts for the web" (Arial, Trebuchet MS,
   Verdana, Georgia, Times New Roman, ...), fetched in their original packaging from
   the official SourceForge mirror, checked against known SHA-256 hashes, and
   unpacked with `cabextract` (see packages.txt).
2. Any .ttf/.otf/.ttc files placed in this repo's `fonts/` folder (for other fonts
   you are licensed to use, e.g. a brand font).
"""

import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests

FONT_DIR = Path.home() / ".fonts"
REPO_FONTS = Path(__file__).parent / "fonts"
COREFONTS_URL = "https://downloads.sourceforge.net/corefonts/{name}.exe"
COREFONTS = {
    "arial32": "85297a4d146e9c87ac6f74822734bdee5f4b2a722d7eaa584b7f2cbf76f478f6",
    "arialb32": "a425f0ffb6a1a5ede5b979ed6177f4f4f4fdef6ae7c302a7b7720ef332fec0a8",
    "trebuc32": "5a690d9bb8510be1b8b4fe49f1f2319651fe51bbe54775ddddd8ef0bd07fdac9",
    "verdan32": "c1cb61255e363166794e47664e2f21af8e3a26cb6346eb8d2ae2fa85dd5aad96",
    "georgi32": "2c2c7dcda6606ea5cf08918fb7cd3f3359e9e84338dc690013f20cd42e930301",
    "times32": "db56595ec6ef5d3de5c24994f001f03b2a13e37cee27bc25c58f6f43e8f807ab",
    "courie32": "bb511d861655dde879ae552eb86b134d6fae67cb58502e6ff73ec5d9151f3384",
    "comic32": "9c6df3feefde26d4e41d4a4fe5db2a89f9123a772594d7f59afd062625cd204e",
    "impact32": "6061ef3b7401d9642f5dfdb5f2b376aa14663f6275e60a51207ad4facf2fccfb",
}
FONT_EXTS = {".ttf", ".otf", ".ttc"}


def install_fonts() -> list[str]:
    """Install missing fonts; return a list of problems (empty if all went well)."""
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    changed = False

    cabextract = shutil.which("cabextract")
    for name, sha in COREFONTS.items():
        marker = FONT_DIR / f".{name}.done"
        if marker.exists():
            continue
        if not cabextract:
            problems.append("cabextract not installed; Microsoft core fonts skipped")
            break
        try:
            blob = requests.get(COREFONTS_URL.format(name=name), timeout=60).content
            if hashlib.sha256(blob).hexdigest() != sha:
                raise ValueError("checksum mismatch")
            with tempfile.TemporaryDirectory() as tmp:
                exe = Path(tmp) / f"{name}.exe"
                exe.write_bytes(blob)
                subprocess.run([cabextract, "-q", "-L", "-F", "*.ttf", "-d", str(FONT_DIR), str(exe)],
                               check=True, capture_output=True, timeout=60)
            marker.touch()
            changed = True
        except Exception as exc:
            problems.append(f"{name}: {exc}")

    if REPO_FONTS.is_dir():
        for f in REPO_FONTS.rglob("*"):
            if f.suffix.lower() in FONT_EXTS:
                dest = FONT_DIR / f.name
                if not dest.exists() or dest.stat().st_size != f.stat().st_size:
                    shutil.copyfile(f, dest)
                    changed = True

    if changed and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f", str(FONT_DIR)], capture_output=True, timeout=120)
    return problems

"""Streamlit PPTX viewer: renders each slide as PowerPoint lays it out
(master/template, layout, positions, fonts) and steps through the deck.

Rendering pipeline: LibreOffice (headless) converts .pptx -> PDF, then
PyMuPDF rasterises each PDF page to a PNG image.
"""

import base64
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote

import pymupdf
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="PPTX Viewer", layout="centered")
st.title("PPTX Viewer")

VIEWER_HTML = (Path(__file__).parent / "viewer.html").read_text(encoding="utf-8")
SOFFICE = shutil.which("soffice") or shutil.which("libreoffice")


@st.cache_data(show_spinner=False, max_entries=5)
def render_slides(data: bytes, zoom: float = 2.0) -> list[bytes]:
    """Return one PNG (bytes) per slide."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "deck.pptx"
        src.write_bytes(data)
        subprocess.run(
            [SOFFICE, "--headless", "--norestore",
             f"-env:UserInstallation=file://{tmp}/profile",
             "--convert-to", "pdf", "--outdir", tmp, str(src)],
            check=True, capture_output=True, timeout=180,
        )
        with pymupdf.open(Path(tmp) / "deck.pdf") as pdf:
            matrix = pymupdf.Matrix(zoom, zoom)
            return [page.get_pixmap(matrix=matrix).tobytes("png") for page in pdf]


if not SOFFICE:
    st.error("LibreOffice is not installed, so slides cannot be rendered.")
    st.stop()

DECKS_DIR = Path(__file__).parent / "decks"
TOP = "(top level)"


def secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)
    except Exception:  # no secrets file configured
        return default


# The deck library is read live from GitHub, so new uploads appear without a reboot.
# Override these in Streamlit's Secrets if the repo or branch changes.
GITHUB_REPO = secret("GITHUB_REPO", "smsrpm/QDpptx")
GITHUB_BRANCH = secret("GITHUB_BRANCH", "claude/streamlit-powerpoint-reader-qy3svu")
GITHUB_TOKEN = secret("GITHUB_TOKEN")  # optional; required only for a private repo


def gh_get(url: str, raw: bool = False) -> requests.Response:
    headers = {"Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp


@st.cache_data(ttl=30, show_spinner=False)
def github_decks() -> dict[str, str]:
    """Map each .pptx path under decks/ (relative to it) to its git blob SHA."""
    tree = gh_get(f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/"
                  f"{quote(GITHUB_BRANCH, safe='')}?recursive=1").json()["tree"]
    return {item["path"][len("decks/"):]: item["sha"] for item in tree
            if item["type"] == "blob" and item["path"].startswith("decks/")
            and item["path"].lower().endswith(".pptx")}


@st.cache_data(show_spinner=False, max_entries=10)
def github_file(sha: str) -> bytes:
    """Download one file by blob SHA (a new upload gets a new SHA, so this never goes stale)."""
    return gh_get(f"https://api.github.com/repos/{GITHUB_REPO}/git/blobs/{sha}",
                  raw=True).content


def local_decks() -> dict[str, Path]:
    """Fallback: the copy of decks/ deployed with the app."""
    if not DECKS_DIR.is_dir():
        return {}
    return {f.relative_to(DECKS_DIR).as_posix(): f for f in DECKS_DIR.rglob("*.pptx")}


def group_by_folder(paths) -> dict[str, list[str]]:
    """Map each folder (relative to decks/) to the deck paths directly in it."""
    folders: dict[str, list[str]] = {}
    for p in sorted(paths, key=str.lower):
        folder, _, name = p.rpartition("/")
        if name.startswith("~$"):  # PowerPoint lock files
            continue
        folders.setdefault(folder or TOP, []).append(p)
    # Top level first, then folders alphabetically (parents before subfolders).
    return dict(sorted(folders.items(),
                       key=lambda kv: (kv[0] != TOP, kv[0].lower().split("/"))))


source = st.radio("Source", ["Library", "Upload"], horizontal=True,
                  label_visibility="collapsed")

if source == "Library":
    try:
        remote = github_decks()
        load = lambda p: github_file(remote[p])  # noqa: E731
        paths = remote
    except Exception as exc:  # offline, rate-limited, bad token, etc.
        st.caption(f"Couldn't reach GitHub ({exc.__class__.__name__}); "
                   "showing the copy deployed with the app.")
        local = local_decks()
        load = lambda p: local[p].read_bytes()  # noqa: E731
        paths = local
    decks = group_by_folder(paths)
    if not decks:
        st.info("No .pptx files found in the repository's `decks/` folder yet.")
        st.stop()
    folder_col, file_col, refresh_col = st.columns([5, 5, 1], vertical_alignment="bottom")
    folder = folder_col.selectbox("Folder", list(decks))
    chosen = file_col.selectbox("File", decks[folder], format_func=lambda p: p.rpartition("/")[2])
    if refresh_col.button("↻", help="Check GitHub for new files"):
        github_decks.clear()
        st.rerun()
    try:
        with st.spinner("Loading deck…"):
            data = load(chosen)
    except Exception as exc:
        st.error(f"Could not load this file: {exc}")
        st.stop()
else:
    uploaded = st.file_uploader("Upload a .pptx file", type="pptx")
    if not uploaded:
        st.stop()
    data = uploaded.getvalue()

try:
    with st.spinner("Rendering slides…"):
        slides = render_slides(data)
except Exception as exc:  # conversion failures, corrupt files, timeouts
    st.error(f"Could not render this file: {exc}")
    st.stop()

if not slides:
    st.warning("This deck has no slides.")
    st.stop()

# Slide display, navigation, keyboard and full screen run in the browser.
slide_w, slide_h = struct.unpack(">II", slides[0][16:24])  # PNG header size
uris = ["data:image/png;base64," + base64.b64encode(s).decode() for s in slides]
viewer = VIEWER_HTML.replace("__SLIDES__", json.dumps(uris))
# Fits Streamlit's centered column (~704px): slide + control bar + hint.
components.html(viewer, height=round(704 * slide_h / slide_w) + 100)

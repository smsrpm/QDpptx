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

import pymupdf
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


def list_decks() -> dict[str, list[Path]]:
    """Map each folder (relative to decks/) to the .pptx files directly in it."""
    folders: dict[str, list[Path]] = {}
    for f in sorted(DECKS_DIR.rglob("*.pptx"), key=lambda p: str(p).lower()):
        if f.name.startswith("~$"):  # PowerPoint lock files
            continue
        rel = f.parent.relative_to(DECKS_DIR).as_posix()
        folders.setdefault(TOP if rel == "." else rel, []).append(f)
    # Top level first, then folders alphabetically (parents before subfolders).
    return dict(sorted(folders.items(),
                       key=lambda kv: (kv[0] != TOP, kv[0].lower().split("/"))))


source = st.radio("Source", ["Library", "Upload"], horizontal=True,
                  label_visibility="collapsed")

if source == "Library":
    decks = list_decks() if DECKS_DIR.is_dir() else {}
    if not decks:
        st.info("No .pptx files found in the repository's `decks/` folder yet.")
        st.stop()
    folder_col, file_col = st.columns(2)
    folder = folder_col.selectbox("Folder", list(decks))
    chosen = file_col.selectbox("File", decks[folder], format_func=lambda p: p.name)
    data = chosen.read_bytes()
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

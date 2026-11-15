"""Streamlit PPTX viewer: renders each slide as PowerPoint lays it out
(master/template, layout, positions, fonts) and steps through the deck.

Rendering pipeline: LibreOffice (headless) converts .pptx -> PDF, then
PyMuPDF rasterises each PDF page to a PNG image.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pymupdf
import streamlit as st

st.set_page_config(page_title="PPTX Viewer", layout="centered")
st.title("PPTX Viewer")

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

uploaded = st.file_uploader("Upload a .pptx file", type="pptx")
if not uploaded:
    st.stop()

try:
    with st.spinner("Rendering slides…"):
        slides = render_slides(uploaded.getvalue())
except Exception as exc:  # conversion failures, corrupt files, timeouts
    st.error(f"Could not render this file: {exc}")
    st.stop()

if not slides:
    st.warning("This deck has no slides.")
    st.stop()

# Reset position when a new file is uploaded.
if st.session_state.get("file_id") != uploaded.file_id:
    st.session_state.file_id = uploaded.file_id
    st.session_state.idx = 0

n = len(slides)


def step(delta: int):
    st.session_state.idx = max(0, min(n - 1, st.session_state.idx + delta))


prev_col, mid_col, next_col = st.columns([1, 2, 1])
prev_col.button("◀ Prev", on_click=step, args=(-1,),
                disabled=st.session_state.idx == 0, use_container_width=True)
next_col.button("Next ▶", on_click=step, args=(1,),
                disabled=st.session_state.idx >= n - 1, use_container_width=True)
mid_col.markdown(
    f"<div style='text-align:center'>Slide {st.session_state.idx + 1} of {n}</div>",
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.image(slides[st.session_state.idx], use_container_width=True)

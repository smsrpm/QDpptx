"""Minimal Streamlit PPTX viewer: upload a deck, step through its slides."""

import io

import streamlit as st
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

st.set_page_config(page_title="PPTX Viewer", layout="centered")
st.title("PPTX Viewer")


@st.cache_data
def load_slides(data: bytes):
    """Return a list of slides, each a list of ('text'|'image'|'table', payload)."""
    prs = Presentation(io.BytesIO(data))
    slides = []
    for slide in prs.slides:
        items = []
        # Top-to-bottom, left-to-right reading order.
        shapes = sorted(slide.shapes, key=lambda s: (s.top or 0, s.left or 0))
        for shape in shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                items.append(("image", shape.image.blob))
            elif shape.has_table:
                rows = [[c.text for c in r.cells] for r in shape.table.rows]
                items.append(("table", rows))
            elif shape.has_text_frame and shape.text_frame.text.strip():
                if shape == slide.shapes.title:
                    items.append(("text", "### " + shape.text_frame.text.strip()))
                    continue
                lines = [
                    "  " * p.level + "- " + "".join(r.text for r in p.runs)
                    for p in shape.text_frame.paragraphs
                    if "".join(r.text for r in p.runs).strip()
                ]
                items.append(("text", "\n".join(lines)))
        slides.append(items)
    return slides


uploaded = st.file_uploader("Upload a .pptx file", type="pptx")
if not uploaded:
    st.stop()

slides = load_slides(uploaded.getvalue())
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
    items = slides[st.session_state.idx]
    if not items:
        st.caption("(No text, image or table content on this slide.)")
    for kind, payload in items:
        if kind == "text":
            st.markdown(payload)
        elif kind == "image":
            st.image(payload)
        elif kind == "table":
            st.table(payload)

# QDpptx

Minimal Streamlit proof of concept for viewing `.pptx` slides as laid out in PowerPoint
(master/template, layouts, positions, shapes, images) and stepping through the deck.

How it works: LibreOffice (headless) converts the deck to PDF, and PyMuPDF turns each page into an image.

## Run locally

Requires LibreOffice (`soffice` on PATH).

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud

`packages.txt` installs LibreOffice Impress plus fonts that match the size and spacing of
Calibri/Cambria (Carlito/Caladea), so text wraps the same way it does in PowerPoint.

## Known limits

Rendering is LibreOffice's, so it is very close to PowerPoint but not pixel-identical:
fonts not installed on the server are substituted, and animations, transitions and
embedded video are shown as static content.

# QDpptx

Minimal Streamlit proof of concept for presenting PDFs and viewing `.pptx` slides as laid out in PowerPoint
(master/template, layouts, positions, shapes, images) and stepping through the deck.

How it works: LibreOffice (headless) converts the deck to PDF, and PyMuPDF turns each page into an image.

## Deck library

Put `.pptx` and `.pdf` files in the `decks/` folder (subfolders allowed). The app's **Library** view
lets you pick a folder, then a file. **Upload** opens a one-off file from your device.
See `decks/README.md` for adding files on github.com.

The library is read live from GitHub, so new or replaced files appear within ~30 seconds
(or immediately with the **↻** button), with no app reboot. If GitHub can't be reached, the app
falls back to the copy of `decks/` deployed with it.

Optional settings (Streamlit Cloud → app ⋮ → Settings → Secrets):

```toml
GITHUB_REPO = "smsrpm/QDpptx"                               # default
GITHUB_BRANCH = "claude/streamlit-powerpoint-reader-qy3svu" # default
GITHUB_TOKEN = "github_pat_..."  # needed for a private repo; avoids GitHub's anonymous rate limit
```

## Presenting

- **⛶ Full screen** button (or **F**, or double-click the slide) shows the slide full screen.
- **>** / **<** (also → / ←, Page Down / Page Up, and most presenter clickers) move forward / back.
- **Esc** leaves full screen.
- **Phones/tablets:** swipe left/right to move; in full screen, tap the right/left side of the slide.
  On iPhone (where browsers can't go full screen) the slide fills the browser window instead,
  with an **✕** button to exit. Rotate to landscape for the biggest view.

## Home-screen icon

Streamlit serves its own page, so "Add to Home Screen" on the app address always shows Streamlit's
logo. The `docs/` folder is a small launcher page with the QDpptx icon and name that opens the app
in a full-window frame. It is published with GitHub Pages:

1. On github.com: **Settings → Pages → Build and deployment → Source: Deploy from a branch**,
   branch `claude/streamlit-powerpoint-reader-qy3svu`, folder `/docs`, **Save**.
2. After a minute, open **https://smsrpm.github.io/QDpptx/** on the phone and use
   **Share → Add to Home Screen** (iPhone) or **⋮ → Add to Home screen** (Android).
3. Delete any older shortcut first: iOS never updates the icon of an existing shortcut.

The icon source is `docs/qdpptx-icon.svg`. If the app address changes, edit the two addresses in
`docs/index.html`.

## Run locally

Requires LibreOffice (`soffice` on PATH).

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud

`packages.txt` installs LibreOffice Impress, `cabextract`, and fonts that match the size and spacing
of Calibri/Cambria (Carlito/Caladea). On first start the app (`fonts.py`) also downloads Microsoft's
free core fonts (Arial, Trebuchet MS, Verdana, Georgia, Times New Roman, …) from their
official SourceForge mirror, checks each download's SHA-256, and installs them, so text wraps where
PowerPoint wraps it. Put any other fonts your decks use in `fonts/`.

## Known limits

Rendering is LibreOffice's, so it is very close to PowerPoint but not pixel-identical:
fonts not installed on the server are substituted, and animations, transitions and
embedded video are shown as static content.

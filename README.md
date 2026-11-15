# QDpptx

Minimal Streamlit proof of concept for viewing `.pptx` slides as laid out in PowerPoint
(master/template, layouts, positions, shapes, images) and stepping through the deck.

How it works: LibreOffice (headless) converts the deck to PDF, and PyMuPDF turns each page into an image.

## Deck library

Put `.pptx` files in the `decks/` folder (subfolders allowed). The app's **Library** view
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

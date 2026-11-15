# QDpptx

Minimal Streamlit proof of concept for viewing `.pptx` content and stepping through slides.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Shows each slide's text (bullets with indent), images and tables in reading order. It does not render the slide layout, so the original styling is not reproduced.

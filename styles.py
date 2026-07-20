"""
styles.py
=========
All CSS for EcoTrace lives here as plain strings, injected into the
Streamlit app via st.markdown(..., unsafe_allow_html=True). Two
palettes (light / dark) are provided; get_css(dark_mode) returns the
full stylesheet for the requested mode.
"""

import os
import base64

LIGHT = {
    "bg": "#faf9f4",
    "panel": "#ffffff",
    "text": "#1f241f",
    "muted": "#6b7280",
    "border": "#e6e4dc",
    "green": "#2f4a3d",
    "green_soft": "#eef2ee",
    "terracotta": "#c17a5e",
    "terracotta_soft": "#f7e9e2",
    "chip_bg": "#eef1ea",
    "bg_image": "media/background.jpeg",
    "bg_overlay": "linear-gradient(135deg, rgba(255,255,255,0.78) 0%, rgba(248,244,236,0.72) 100%)",
}

DARK = {
    "bg": "#181a17",
    "panel": "#22251f",
    "text": "#f0efe9",
    "muted": "#a2a49b",
    "border": "#33362e",
    "green": "#7fae94",
    "green_soft": "#26302a",
    "terracotta": "#e0977a",
    "terracotta_soft": "#3a2a24",
    "chip_bg": "#2a2d25",
    "bg_image": "media/bg8.jpeg",
    "bg_overlay": "linear-gradient(135deg, rgba(9, 12, 10, 0.78) 0%, rgba(18, 24, 18, 0.72) 100%)",
}


def _encode_image(path: str) -> str:
    if not os.path.exists(path):
        return ""
    ext = os.path.splitext(path)[1].lower().lstrip('.')
    mime = {
        'jpg': 'jpeg',
        'jpeg': 'jpeg',
        'png': 'png',
        'svg': 'svg+xml',
        'webp': 'webp',
    }.get(ext, 'jpeg')
    with open(path, 'rb') as image_file:
        data = image_file.read()
    return f"data:image/{mime};base64,{base64.b64encode(data).decode('ascii')}"


def get_css(dark_mode: bool = False) -> str:
    c = DARK if dark_mode else LIGHT
    template = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Playfair+Display:wght@600;700&display=swap');

:root {
  --bg: __BG__;
  --panel: __PANEL__;
  --text: __TEXT__;
  --muted: __MUTED__;
  --accent: __ACCENT__;
  --accent-soft: __ACCENT_SOFT__;
  --card-border: __CARD_BORDER__;
  --bg-image: __BG_IMAGE__;
  --bg-overlay: __BG_OVERLAY__;
}

html, body, body > div, .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stMain"], [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
    color: var(--text) !important;
    background: transparent !important;
    min-height: 100%;
}

.block-container, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--bg-overlay), url('__BG_IMAGE__') center/cover no-repeat fixed !important;
    background-size: cover !important;
    background-color: var(--bg) !important;
    min-height: 100vh;
}

.block-container {
    padding: 2rem 2.5rem 3rem !important;
}

.app-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1.4rem 1rem;
}

h1, h2, h3, .ecotrace-serif {
    font-family: 'Playfair Display', serif;
    color: var(--text);
}

/* modern nav */
.ecotrace-navbar {
    display:flex; align-items:center; gap:1rem; padding:0.75rem 0.25rem; margin-bottom:1.25rem;
}
.ecotrace-logo {
    font-family: 'Playfair Display', serif; font-weight:700; font-size:1.4rem; display:flex; align-items:center; gap:0.6rem;
}
.ecotrace-logo-icon {
    background: var(--accent-soft); color: var(--accent); border-radius:8px; padding:0.35rem 0.55rem;
}

/* cards */
.eco-card {
    background: rgba(255,255,255,0.86); border-radius:14px; padding:1.25rem; margin-bottom:1rem; border:1px solid var(--card-border);
    box-shadow: 0 6px 18px rgba(17,24,39,0.06); transition: transform 0.12s ease, box-shadow 0.12s ease;
    backdrop-filter: blur(10px);
}
.eco-card:hover { transform: translateY(-4px); box-shadow: 0 12px 30px rgba(17,24,39,0.08); }

.eco-chip { background: var(--accent-soft); color: var(--accent); padding:0.25rem 0.6rem; border-radius:999px; font-weight:700; font-size:0.8rem; }
.eco-badge-warn { background:#fff4f2; color: #c2410c; padding:0.35rem 0.8rem; border-radius:10px; font-weight:700 }
.eco-savings-pill { background: linear-gradient(90deg, rgba(95,191,122,0.12), rgba(63,143,90,0.08)); padding:0.3rem 0.8rem; border-radius:10px; color:var(--text); font-weight:700 }

.eco-muted { color: var(--muted); }
.eco-hero-number { font-family:'Playfair Display', serif; color: var(--accent); font-size:2.2rem; }

/* Buttons */
div.stButton > button { border-radius:10px; padding:0.6rem 0.9rem; border:1px solid var(--card-border); background: var(--panel); color: var(--text); font-weight:600; }
div.stButton > button:hover { border-color: var(--accent); color: var(--accent); box-shadow: 0 6px 18px rgba(63,143,90,0.06); }
.stButton>button.primary, .eco-primary-btn button { background: var(--accent) !important; color: #fff !important; border: none !important; }

/* radio pills */
div[role="radiogroup"] label { background: var(--panel); border:1px solid var(--card-border); border-radius:12px; padding:0.6rem 1rem !important; margin-right:0 !important; }

hr { border-color: var(--card-border); }

/* responsive tweaks */
@media (max-width: 900px) {
  .app-container { padding: 0.75rem; }
}
</style>
"""
    # Replace tokens with actual values
    bg_image = _encode_image(c["bg_image"])
    if bg_image:
        template = template.replace("__BG_IMAGE__", bg_image)
    else:
        template = template.replace("__BG_IMAGE__", "none")

    out = (
        template.replace("__BG__", c["bg"])
        .replace("__PANEL__", c["panel"])
        .replace("__TEXT__", c["text"])
        .replace("__MUTED__", c["muted"])
        .replace("__ACCENT__", c["green"])
        .replace("__ACCENT_SOFT__", c["green_soft"])
        .replace("__CARD_BORDER__", c["border"])
        .replace("__BG_OVERLAY__", c["bg_overlay"])
    )
    return out

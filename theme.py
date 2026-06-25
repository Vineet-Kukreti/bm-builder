"""
"Forest & Gold" — a clean, editorial LIGHT design system for the tool chrome.

Deep forest-green primary + antique-gold accent on a warm cream canvas, black/white
text. Restrained (no AI-purple gradients/glows); colour is purposeful — green for
primary actions & the active tab, gold for accents/focus, semantic colours for status.
Base colours/font/radius come from `.streamlit/config.toml`; this layers the craft.

Call `inject()` once per run (app.py does, right after set_page_config). Also exposes
`chip()` and `page_header()`.
"""
import html as _html

import streamlit as strl

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root{
  --green:#13402b; --green-press:#0e3220; --green-hi:#1d5a3c; --green-soft:#eaf1ec; --green-line:#c9ddd0;
  --gold:#b89339; --gold-deep:#937326; --gold-soft:#f6efd9; --gold-line:#e8d9ac;
  --ink:#171411; --ink2:#3c372f; --muted:#6f675b; --faint:#a8a092;
  --line:#e8e2d6; --line2:#f0ece1; --soft:#f6f3eb; --card:#ffffff; --canvas:#faf8f2;
  --ok:#15803d; --okbg:#eef6f0; --okln:#c4e3cf;
  --warn:#b45309; --warnbg:#fbf3e6; --warnln:#ecd9b0;
  --bad:#b3261e; --badbg:#fbeeed; --badln:#f2c9c5;
  --shadow-sm:0 1px 2px rgba(23,20,17,.05);
  --shadow:0 8px 26px -14px rgba(23,20,17,.28), 0 2px 6px -4px rgba(23,20,17,.08);
  --ring:0 0 0 3px rgba(184,147,57,.30);
}

/* ---- Canvas + typography ------------------------------------------------- */
html, body, .stApp{
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
  font-family:'Plus Jakarta Sans', -apple-system, 'Segoe UI', Roboto, sans-serif; color:var(--ink); }
.stApp{ background:var(--canvas); }
[data-testid="stHeader"]{ background:transparent; }
footer, [data-testid="stStatusWidget"]{ visibility:hidden; height:0; }
.block-container{ padding-top:2.1rem; padding-bottom:5rem; max-width:1280px; }
[data-testid="stVerticalBlock"]{ gap:.8rem; }

.stApp h1,.stApp h2,.stApp h3,.stApp h4{ color:var(--ink); letter-spacing:-.021em; font-weight:750; line-height:1.18; }
.stApp h1{ font-size:1.85rem; margin-bottom:.25rem; }
.stApp h2{ font-size:1.32rem; }
.stApp h3{ font-size:1.08rem; }
.stApp h4{ font-size:.98rem; }
.stApp p,.stApp li{ line-height:1.6; color:var(--ink2); }
.stApp strong{ color:var(--ink); font-weight:700; }
.stApp a{ color:var(--green); font-weight:600; text-decoration:underline; text-underline-offset:2px;
  text-decoration-color:var(--gold); }
.stApp a:hover{ color:var(--green-hi); text-decoration-color:var(--gold-deep); }
.stApp [data-testid="stCaptionContainer"], .stApp small{ color:var(--muted); }

/* ---- Buttons — forest-green primary, calm secondary w/ gold hover -------- */
.stButton>button, .stDownloadButton>button, .stFormSubmitButton>button, .stLinkButton>a{
  border-radius:9px; font-weight:600; padding:.48rem 1rem; letter-spacing:-.003em;
  transition:transform .1s ease, box-shadow .14s ease, border-color .12s ease, background-color .12s ease, color .12s ease; }
.stButton>button:not([kind="primary"]), .stDownloadButton>button,
.stFormSubmitButton>button:not([kind="primary"]), .stLinkButton>a{
  background:var(--card); border:1px solid var(--line); color:var(--ink2); }
.stButton>button:not([kind="primary"]):hover, .stDownloadButton>button:hover,
.stFormSubmitButton>button:not([kind="primary"]):hover, .stLinkButton>a:hover{
  transform:translateY(-1px); box-shadow:var(--shadow-sm); border-color:var(--gold); color:var(--green);
  text-decoration:none; }
.stButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"]{
  background:var(--green); border:1px solid var(--green); }
/* Streamlit nests the label — force white text on every child */
.stButton>button[kind="primary"], .stButton>button[kind="primary"] *,
.stFormSubmitButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"] *{ color:#ffffff !important; }
.stButton>button[kind="primary"]:hover, .stFormSubmitButton>button[kind="primary"]:hover{
  background:var(--green-hi); transform:translateY(-1px); box-shadow:var(--shadow); }
/* Destructive action (per-project Delete) — red, key-scoped (keys are 'delproj_<name>') */
[class*="st-key-delproj_"] button{ background:var(--bad) !important; border:1px solid var(--bad) !important; }
[class*="st-key-delproj_"] button, [class*="st-key-delproj_"] button *{ color:#ffffff !important; }
[class*="st-key-delproj_"] button:hover:not(:disabled){ filter:brightness(.92);
  transform:translateY(-1px); box-shadow:var(--shadow); }
[class*="st-key-delproj_"] button:disabled{ opacity:.5; }
/* Roadmap feature delete — small red ✕ cross (keys are 'rm_del_<id>_<name>') */
[class*="st-key-rm_del_"] button{ color:var(--bad) !important; border-color:var(--badln) !important;
  font-weight:800; padding:.35rem .6rem; line-height:1; }
[class*="st-key-rm_del_"] button:hover{ background:var(--badbg) !important; border-color:var(--bad) !important; }
.stButton>button:focus-visible, .stDownloadButton>button:focus-visible,
.stFormSubmitButton>button:focus-visible, .stLinkButton>a:focus-visible{ outline:none; box-shadow:var(--ring); }

/* ---- Cards / bordered containers ---------------------------------------- */
[data-testid="stVerticalBlockBorderWrapper"]{
  border-radius:14px; border:1px solid var(--line); background:var(--card); box-shadow:var(--shadow-sm);
  transition:box-shadow .18s ease, border-color .18s ease; }
[data-testid="stVerticalBlockBorderWrapper"]:hover{ box-shadow:var(--shadow); border-color:var(--gold-line); }

/* ---- Inputs ------------------------------------------------------------- */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"]>div, [data-baseweb="base-input"]{
  border-radius:9px; background:var(--card); }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within,
[data-baseweb="select"]>div:focus-within{ border-color:var(--gold)!important; box-shadow:var(--ring); }
.stTextInput label,.stTextArea label,.stSelectbox label,.stMultiSelect label,.stNumberInput label,
.stSlider label,.stRadio label,.stCheckbox label,.stFileUploader label{ font-weight:600; color:var(--ink2); }
[data-testid="stFileUploaderDropzone"]{ border-radius:11px; border:1.5px dashed var(--gold-line); background:var(--soft); }
[data-testid="stFileUploaderDropzone"]:hover{ border-color:var(--gold); background:var(--gold-soft); }

/* ---- Tabs — selected = solid green pill + white text (high contrast) ----- */
.stTabs [data-baseweb="tab-list"]{ gap:5px; border-bottom:1px solid var(--line); padding-bottom:3px; }
.stTabs [data-baseweb="tab"]{ border-radius:9px; font-weight:650; color:var(--muted); padding:.36rem .9rem; }
.stTabs [data-baseweb="tab"]:hover{ background:var(--soft); color:var(--ink); }
.stTabs [data-baseweb="tab"][aria-selected="true"]{ background:var(--green); }
.stTabs [data-baseweb="tab"][aria-selected="true"], .stTabs [data-baseweb="tab"][aria-selected="true"] *{
  color:#ffffff !important; }
.stTabs [data-baseweb="tab-highlight"]{ background-color:transparent; height:0; }   /* fill is the indicator */
.stTabs [data-baseweb="tab-border"]{ background-color:var(--line); }

/* ---- Expanders / metrics ------------------------------------------------- */
[data-testid="stExpander"]{ border-radius:12px; border:1px solid var(--line); overflow:hidden;
  background:var(--card); box-shadow:var(--shadow-sm); }
[data-testid="stExpander"] summary{ font-weight:600; color:var(--ink2); padding:.5rem .85rem; }
[data-testid="stExpander"] summary:hover{ color:var(--green); background:var(--soft); }
[data-testid="stMetric"]{ background:var(--card); border:1px solid var(--line); border-radius:12px;
  padding:13px 17px; box-shadow:var(--shadow-sm); }
[data-testid="stMetricValue"]{ font-weight:800; letter-spacing:-.02em; color:var(--green); }
[data-testid="stMetricLabel"]{ color:var(--muted); }

/* ---- Progress — a SOLID green fill on a clear light track, so the % is obvious.
   NOTE: Streamlit nests progressbar > BarContainer (full width = the track) > Bar
   (width = the value = the fill). The previous CSS coloured the BarContainer, so any
   value looked nearly full. Colour the track and the inner Bar separately. ----------- */
div[data-testid="stProgress"] [role="progressbar"]{ min-height:16px; }
div[data-testid="stProgress"] [role="progressbar"] > div{          /* track (empty) */
  background:#eae4d7 !important; background-image:none !important;
  border:1px solid #d3cab6; border-radius:999px; overflow:hidden; min-height:16px; }
div[data-testid="stProgress"] [role="progressbar"] > div > div{    /* fill (= the %) */
  background:var(--green) !important; background-image:none !important;
  border-radius:999px; transition:width .25s ease; }

/* ---- Alerts / tables ---------------------------------------------------- */
[data-testid="stAlert"]{ border-radius:11px; border:1px solid var(--line); box-shadow:none; padding:.6rem .85rem; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"]{ border-radius:11px; overflow:hidden; border:1px solid var(--line); }

/* ---- Sidebar — blends with the canvas ----------------------------------- */
section[data-testid="stSidebar"]{ background:var(--canvas); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] .block-container{ padding-top:1.3rem; }
section[data-testid="stSidebar"] [data-testid="stExpander"]{ box-shadow:none; background:transparent; }

/* ---- Misc --------------------------------------------------------------- */
hr, [data-testid="stDivider"]{ border-color:var(--line); }
[data-testid="stToast"]{ border-radius:12px; box-shadow:var(--shadow); }
::-webkit-scrollbar{ height:10px; width:10px; }
::-webkit-scrollbar-thumb{ background:#d8d0bf; border-radius:8px; border:2px solid transparent; background-clip:content-box; }
::-webkit-scrollbar-thumb:hover{ background:var(--faint); background-clip:content-box; }
::-webkit-scrollbar-track{ background:transparent; }

/* ---- Utility: chips + header + phase stepper ---------------------------- */
.osw-chip{ display:inline-flex; align-items:center; gap:5px; font-size:.72rem; font-weight:650;
  padding:2px 10px; border-radius:7px; background:var(--soft); color:var(--ink2); border:1px solid var(--line);
  letter-spacing:.005em; white-space:nowrap; }
.osw-chip.gray{ background:var(--soft); color:var(--muted); border-color:var(--line); }
.osw-chip.green{ background:var(--green-soft); color:var(--green); border-color:var(--green-line); }
.osw-chip.gold{ background:var(--gold-soft); color:var(--gold-deep); border-color:var(--gold-line); }
.osw-chip.amber{ background:var(--warnbg); color:var(--warn); border-color:var(--warnln); }
.osw-chip.red{ background:var(--badbg); color:var(--bad); border-color:var(--badln); }

.osw-head{ display:flex; align-items:center; gap:11px; margin:.1rem 0 .12rem; }
.osw-head .t{ font-size:1.5rem; font-weight:800; letter-spacing:-.025em; line-height:1.15; color:var(--ink); }
.osw-sub{ color:var(--muted); font-size:.92rem; margin:-.02rem 0 .55rem; }
.osw-rule{ height:2px; background:linear-gradient(90deg, var(--gold) 0%, var(--gold-line) 22%, transparent 55%);
  border-radius:2px; margin:.1rem 0 .85rem; }

.osw-rail{ display:flex; flex-wrap:wrap; align-items:center; gap:5px; margin:.1rem 0 .3rem;
  padding:7px 9px; background:var(--card); border:1px solid var(--line); border-radius:12px; box-shadow:var(--shadow-sm); }
.osw-step{ display:inline-flex; align-items:center; gap:5px; font-size:.76rem; font-weight:600;
  padding:4px 11px; border-radius:7px; border:1px solid transparent; background:transparent;
  color:var(--faint); white-space:nowrap; transition:background .12s ease, color .12s ease; }
.osw-step.done{ color:var(--green); background:var(--green-soft); }
.osw-step.unlocked{ color:var(--ink2); }
.osw-step.unlocked:hover{ background:var(--soft); }
.osw-step.current{ background:var(--green); color:#fff; }
.osw-step.locked{ color:var(--faint); }
.osw-step.stale{ color:var(--gold-deep); background:var(--gold-soft); }
.osw-rail .osw-arrow{ color:var(--faint); font-size:.62rem; }
</style>
"""


def inject():
    strl.markdown(_CSS, unsafe_allow_html=True)


def chip(text, kind=""):
    """Inline pill badge. kind ∈ {'', 'gray', 'green', 'gold', 'amber', 'red'}. Returns HTML.
    `text` is HTML-escaped (it may be a user-supplied project name)."""
    cls = ("osw-chip " + kind).strip()
    return f'<span class="{cls}">{_html.escape(str(text), quote=False)}</span>'


def page_header(title, subtitle="", badge_html=""):
    """A consistent screen header: title + optional badge chip + subtitle + a gold hairline rule.
    `title`/`subtitle` are escaped; `badge_html` is trusted HTML (e.g. from chip())."""
    badge = f" {badge_html}" if badge_html else ""
    t = _html.escape(str(title), quote=False)
    sub = (f'<div class="osw-sub">{_html.escape(str(subtitle), quote=False)}</div>'
           if subtitle else "")
    strl.markdown(f'<div class="osw-head"><span class="t">{t}</span>{badge}</div>{sub}'
                  '<div class="osw-rule"></div>', unsafe_allow_html=True)

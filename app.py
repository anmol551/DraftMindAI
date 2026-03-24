import time, yaml, os, json, io, re, sys
import streamlit as st
import streamlit.components.v1 as components
from utils import save_text_file, strip_markdown
from generators.introduction_gen import generate_introduction
from generators.methodology_gen import generate_methodology
from generators.implementation_gen import generate_implementation
from generators.abstract_gen import generate_abstract
from generators.result_gen import generate_result_conclusion
from keywords import generate_keywords
from get_citation import get_ref_citation
from doc_convertor.code import (
    parse_structure, validate, refine_with_llm, generate_docx, generate_formatted_txt,
    apply_global_citation_deduplication
)
import chardet

# ── Optional extraction libraries ──
try:
    import docx as _docx_mod
    _DOCX_OK = True
except ImportError:
    _DOCX_OK = False

try:
    import pypdf as _pypdf_mod
    _PYPDF_OK = True
except ImportError:
    _PYPDF_OK = False

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DRAFTMIND AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── DRAFTMIND AI — PREMIUM PRODUCT THEME ─────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Geist+Mono:wght@300;400;500&display=swap');

/* ═══════════════════════════════════════════
   DESIGN TOKENS
═══════════════════════════════════════════ */
:root {
  /* Core palette — Golden Ember */
  --c-bg:          #0C0A09;
  --c-bg-raised:   #111009;
  --c-surface:     #171410;
  --c-surface-hi:  #1E1A15;
  --c-border:      rgba(255,255,255,0.07);
  --c-border-hi:   rgba(249,115,22,0.25);
  --c-border-sun:  rgba(250,204,21,0.20);

  --c-amber:       #F97316;
  --c-amber-d:     #C45E0F;
  --c-sun:         #FACC15;
  --c-sun-d:       #CA9F0C;
  --c-amber-a10:   rgba(249,115,22,0.10);
  --c-amber-a18:   rgba(249,115,22,0.18);
  --c-amber-a30:   rgba(249,115,22,0.30);
  --c-sun-a10:     rgba(250,204,21,0.10);

  --c-green:       #4ADE80;
  --c-green-bg:    rgba(74,222,128,0.08);
  --c-green-bd:    rgba(74,222,128,0.20);
  --c-red:         #F87171;
  --c-red-bg:      rgba(248,113,113,0.08);
  --c-red-bd:      rgba(248,113,113,0.18);
  --c-blue:        #60A5FA;

  /* Typography */
  --c-text-pri:    #F5F0EA;
  --c-text-sec:    rgba(245,240,234,0.60);
  --c-text-ter:    rgba(245,240,234,0.35);
  --c-text-inv:    #0C0A09;

  /* Spacing */
  --sp-1: 4px;   --sp-2: 8px;  --sp-3: 12px;
  --sp-4: 16px;  --sp-5: 20px; --sp-6: 24px;
  --sp-8: 32px;  --sp-10: 40px;

  /* Type */
  --font-sans: 'Plus Jakarta Sans', sans-serif;
  --font-mono: 'Geist Mono', 'Courier New', monospace;
  --r: 8px;
  --r-lg: 12px;
}

/* ═══════════════════════════════════════════
   RESET & BASE
═══════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
  background: var(--c-bg) !important;
  font-family: var(--font-sans) !important;
  color: var(--c-text-pri) !important;
  font-size: 14px !important;
  line-height: 1.55 !important;
  -webkit-font-smoothing: antialiased !important;
}

/* Single warm glow — top-left, subtle */
.stApp::before {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 900px 600px at -100px -80px,
      rgba(249,115,22,0.11) 0%, transparent 70%);
}

.block-container {
  padding: 0 0 6rem !important;
  max-width: 960px !important;
  margin: 0 auto !important;
}
.main > div { padding: 0 !important; }
[data-testid="stAppViewBlockContainer"] { padding-top: 0 !important; }
[data-testid="stMainBlockContainer"] {
  max-width: 960px !important; margin: 0 auto !important;
  padding-left: 2.5rem !important; padding-right: 2.5rem !important;
}
#MainMenu, footer, header, [data-testid="stToolbar"] { display: none !important; }

/* ═══════════════════════════════════════════
   TOPBAR — minimal, sticky
═══════════════════════════════════════════ */
.topbar {
  position: sticky; top: 0; z-index: 200;
  height: 52px;
  background: rgba(12,10,9,0.88);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-bottom: 1px solid var(--c-border);
  padding: 0 28px;
  display: flex; align-items: center; gap: 14px;
}
.topbar-wordmark {
  font-family: var(--font-sans);
  font-size: 15px; font-weight: 800;
  letter-spacing: -0.2px;
  color: var(--c-text-pri);
  margin: 0;
}
.topbar-wordmark span { color: var(--c-amber); }
.topbar-divider {
  width: 1px; height: 16px;
  background: var(--c-border);
  flex-shrink: 0;
}
.topbar-subtitle {
  font-size: 11px; font-weight: 500;
  letter-spacing: 0.6px; text-transform: uppercase;
  color: var(--c-text-ter); margin: 0;
}
.topbar-badge {
  margin-left: auto;
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.4px; text-transform: uppercase;
  color: var(--c-green);
  background: var(--c-green-bg);
  border: 1px solid var(--c-green-bd);
  border-radius: 999px; padding: 3px 10px;
}
.topbar-badge::before {
  content: '';
  width: 5px; height: 5px; border-radius: 50%;
  background: var(--c-green);
  box-shadow: 0 0 6px var(--c-green);
  animation: live-pulse 2.4s ease-in-out infinite;
}
@keyframes live-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.85); }
}

/* ═══════════════════════════════════════════
   SIDEBAR — structured nav rail
═══════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: var(--c-surface) !important;
  border-right: 1px solid var(--c-border) !important;
  width: 272px !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }

.sb-brand {
  padding: 20px 18px 16px;
  border-bottom: 1px solid var(--c-border);
}
.sb-logo-row {
  display: flex; align-items: center; gap: 10px; margin-bottom: 2px;
}
.sb-logo-mark {
  width: 28px; height: 28px; border-radius: 7px;
  background: linear-gradient(135deg, var(--c-amber), var(--c-sun));
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; color: var(--c-text-inv); font-weight: 800;
  flex-shrink: 0;
}
.sb-title {
  font-family: var(--font-sans);
  font-size: 14px; font-weight: 700;
  color: var(--c-text-pri);
  letter-spacing: -0.1px; margin: 0;
}
.sb-sub {
  font-size: 11px; font-weight: 400;
  color: var(--c-text-ter); margin: 0;
  padding-left: 38px;
}

.sb-section {
  padding: 16px 18px 6px;
}
.sb-section-label {
  font-family: var(--font-mono);
  font-size: 10px; font-weight: 500;
  letter-spacing: 1.2px; text-transform: uppercase;
  color: var(--c-text-ter);
  margin: 0 0 8px;
  display: flex; align-items: center; gap: 6px;
}
.sb-section-label::after {
  content: ''; flex: 1; height: 1px;
  background: var(--c-border);
}

/* Pipeline step items */
.step-row {
  display: flex; align-items: center; gap: 9px;
  padding: 5px 18px; line-height: 1.3;
}
.step-dot {
  width: 18px; height: 18px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 9px; font-weight: 700;
  border: 1px solid var(--c-border);
  background: transparent; color: var(--c-text-ter);
  font-family: var(--font-mono);
}
.step-dot.done {
  background: var(--c-green-bg);
  border-color: var(--c-green-bd);
  color: var(--c-green);
}
.step-dot.active {
  border-color: var(--c-amber);
  color: var(--c-amber);
  box-shadow: 0 0 0 2px rgba(249,115,22,0.15);
}

/* Status tiles */
.stat-tile {
  margin: 0 14px 6px;
  background: var(--c-bg-raised);
  border: 1px solid var(--c-border);
  border-radius: var(--r);
  padding: 9px 12px;
  position: relative; overflow: hidden;
}
.stat-tile::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, var(--c-amber), var(--c-sun) 40%, transparent 70%);
}
.stat-value {
  font-family: var(--font-mono);
  font-size: 18px; font-weight: 400;
  color: var(--c-amber); margin: 0; line-height: 1.2;
  letter-spacing: -0.5px;
}
.stat-label {
  font-size: 10px; font-weight: 600;
  letter-spacing: 0.8px; text-transform: uppercase;
  color: var(--c-text-ter); margin: 2px 0 0;
}

/* ═══════════════════════════════════════════
   CONTENT LAYOUT
═══════════════════════════════════════════ */
.content-wrap { padding: 28px 0 160px; }

/* Page header */
.page-hd {
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--c-border);
}
.page-hd-eyebrow {
  font-family: var(--font-mono);
  font-size: 10px; font-weight: 500;
  letter-spacing: 2px; text-transform: uppercase;
  color: var(--c-amber); margin: 0 0 6px;
}
.page-hd-title {
  font-size: 26px; font-weight: 700;
  color: var(--c-text-pri); margin: 0 0 5px;
  letter-spacing: -0.5px; line-height: 1.2;
}
.page-hd-sub {
  font-size: 13px; color: var(--c-text-sec); margin: 0;
  font-weight: 400; line-height: 1.5;
}

/* ═══════════════════════════════════════════
   CARDS
═══════════════════════════════════════════ */
.card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: 20px 22px 18px;
  margin-bottom: 16px;
  position: relative;
  overflow: hidden;
  transition: border-color 0.15s ease;
}
.card:hover { border-color: rgba(255,255,255,0.11); }
.card-header {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 14px;
}
.card-icon {
  width: 30px; height: 30px; border-radius: 7px;
  background: var(--c-amber-a10);
  border: 1px solid var(--c-border-hi);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; flex-shrink: 0;
}
.card-title {
  font-size: 13px; font-weight: 600;
  color: var(--c-text-pri); margin: 0;
  letter-spacing: -0.1px;
}
.card-sub {
  font-size: 11px; color: var(--c-text-ter);
  margin: 1px 0 0; font-weight: 400;
}

/* Backward compat: section-card maps to card */
.section-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: 20px 22px 18px;
  margin-bottom: 16px;
  position: relative; overflow: hidden;
}
.section-card:hover { border-color: rgba(255,255,255,0.11); }
.section-heading {
  font-size: 12px; font-weight: 700;
  letter-spacing: 0.8px; text-transform: uppercase;
  color: var(--c-text-sec); margin: 0 0 14px;
  display: flex; align-items: center; gap: 8px;
}
.section-heading::before {
  content: '';
  width: 3px; height: 12px; border-radius: 2px;
  background: linear-gradient(180deg, var(--c-amber), var(--c-sun));
  flex-shrink: 0;
}

/* ═══════════════════════════════════════════
   UPLOAD ZONES
═══════════════════════════════════════════ */
.upload-zone {
  background: var(--c-bg-raised);
  border: 1px dashed rgba(255,255,255,0.10);
  border-radius: var(--r);
  padding: 24px 20px;
  text-align: center;
  transition: all 0.18s ease;
  cursor: pointer;
}
.upload-zone:hover {
  border-color: var(--c-amber);
  background: var(--c-amber-a10);
}
.upload-icon {
  font-size: 22px; margin-bottom: 6px;
  opacity: 0.5; line-height: 1;
}
.upload-title {
  font-size: 13px; font-weight: 600;
  color: var(--c-text-pri); margin: 0 0 3px;
}
.upload-sub {
  font-size: 11px; color: var(--c-text-ter); line-height: 1.5;
}
.upload-sub code {
  font-family: var(--font-mono);
  font-size: 10px; color: var(--c-amber);
  background: var(--c-amber-a10);
  padding: 1px 4px; border-radius: 3px;
}

/* ═══════════════════════════════════════════
   SUCCESS / LOADED BANNERS
═══════════════════════════════════════════ */
.json-loaded-banner {
  background: var(--c-green-bg);
  border: 1px solid var(--c-green-bd);
  border-radius: var(--r);
  padding: 10px 14px;
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 10px;
}
.jlb-icon { font-size: 16px; opacity: 0.9; line-height: 1; }
.jlb-text {
  font-size: 13px; font-weight: 600;
  color: var(--c-green);
}
.jlb-sub {
  font-size: 11px; color: var(--c-text-sec);
  margin-top: 1px;
  font-family: var(--font-mono);
}

/* ═══════════════════════════════════════════
   FORM CONTROLS
═══════════════════════════════════════════ */
/* Widget labels */
[data-testid="stWidgetLabel"] p,
.stTextArea label, .stTextInput label, .stSelectbox label {
  font-family: var(--font-mono) !important;
  font-size: 10px !important; font-weight: 500 !important;
  letter-spacing: 1.2px !important; text-transform: uppercase !important;
  color: var(--c-text-ter) !important;
  margin-bottom: 5px !important;
}

/* Text inputs + textareas */
.stTextArea textarea, .stTextInput input,
[data-baseweb="textarea"] textarea,
[data-baseweb="input"] input {
  background: var(--c-bg-raised) !important;
  border: 1px solid var(--c-border) !important;
  border-radius: var(--r) !important;
  color: var(--c-text-pri) !important;
  font-family: var(--font-sans) !important;
  font-size: 13px !important;
  line-height: 1.55 !important;
  transition: border-color 0.15s, box-shadow 0.15s !important;
  caret-color: var(--c-amber) !important;
}
.stTextArea textarea:focus, .stTextInput input:focus,
[data-baseweb="textarea"] textarea:focus,
[data-baseweb="input"] input:focus {
  border-color: var(--c-amber) !important;
  box-shadow: 0 0 0 2px rgba(249,115,22,0.15) !important;
  outline: none !important;
  background: var(--c-surface-hi) !important;
}
.stTextArea textarea::placeholder, .stTextInput input::placeholder {
  color: var(--c-text-ter) !important;
}

/* Selectbox */
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-baseweb="select"] > div {
  background: var(--c-bg-raised) !important;
  border: 1px solid var(--c-border) !important;
  border-radius: var(--r) !important;
  color: var(--c-text-pri) !important;
  transition: border-color 0.15s !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
[data-baseweb="select"] > div:hover {
  border-color: rgba(255,255,255,0.14) !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] div { color: var(--c-text-pri) !important; background: transparent !important; }
[data-baseweb="select"] svg { fill: var(--c-text-ter) !important; }
[data-baseweb="menu"] {
  background: #1E1A15 !important;
  border: 1px solid var(--c-border) !important;
  border-radius: var(--r) !important;
  box-shadow: 0 16px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.04) !important;
}
[data-baseweb="menu"] li {
  background: transparent !important;
  color: var(--c-text-sec) !important;
  font-size: 13px !important;
  padding: 8px 12px !important;
}
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [aria-selected="true"] {
  background: var(--c-amber-a10) !important;
  color: var(--c-text-pri) !important;
}

/* File uploader */
[data-testid="stFileUploader"] { background: transparent !important; border-radius: var(--r) !important; }
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] > div {
  background: var(--c-bg-raised) !important;
  border: 1px dashed rgba(255,255,255,0.10) !important;
  border-radius: var(--r) !important;
  transition: all 0.18s ease !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--c-amber) !important;
  background: var(--c-amber-a10) !important;
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] div,
[data-testid="stFileUploaderDropzoneInstructions"] small,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small {
  color: var(--c-text-ter) !important;
  background: transparent !important;
  font-family: var(--font-sans) !important;
}
[data-testid="stFileUploader"] button {
  background: var(--c-surface-hi) !important;
  border: 1px solid var(--c-border) !important;
  color: var(--c-amber) !important;
  border-radius: var(--r) !important;
  font-size: 12px !important; font-weight: 600 !important;
  font-family: var(--font-sans) !important;
  padding: 5px 12px !important;
  transition: all 0.15s !important;
}
[data-testid="stFileUploader"] button:hover {
  background: var(--c-amber-a18) !important;
  border-color: var(--c-amber) !important;
}

/* ═══════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════ */
.stButton > button {
  background: var(--c-surface-hi) !important;
  color: var(--c-text-sec) !important;
  border: 1px solid var(--c-border) !important;
  border-radius: var(--r) !important;
  font-family: var(--font-sans) !important;
  font-size: 13px !important; font-weight: 500 !important;
  letter-spacing: -0.1px !important;
  transition: all 0.15s ease !important;
  width: 100% !important; padding: 8px 16px !important;
}
.stButton > button:hover {
  background: var(--c-amber-a10) !important;
  border-color: var(--c-border-hi) !important;
  color: var(--c-text-pri) !important;
}

/* Primary CTA */
.primary-btn > button {
  background: var(--c-amber) !important;
  border-color: var(--c-amber) !important;
  color: #0C0A09 !important;
  font-weight: 700 !important; font-size: 13px !important;
  padding: 10px 20px !important;
  letter-spacing: 0.1px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 0 0 1px rgba(249,115,22,0.4) !important;
  transition: all 0.15s ease !important;
}
.primary-btn > button:hover {
  background: #FB923C !important;
  border-color: #FB923C !important;
  box-shadow: 0 4px 16px rgba(249,115,22,0.35) !important;
  transform: translateY(-1px) !important;
}

/* Destructive */
.danger-btn > button {
  background: transparent !important;
  border-color: var(--c-red-bd) !important;
  color: var(--c-red) !important;
  font-size: 12px !important;
}
.danger-btn > button:hover {
  background: var(--c-red-bg) !important;
  border-color: var(--c-red) !important;
}

/* Download */
[data-testid="stDownloadButton"] > button {
  background: var(--c-amber) !important;
  border-color: var(--c-amber) !important;
  color: #0C0A09 !important;
  font-weight: 700 !important; font-size: 13px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.3) !important;
  border-radius: var(--r) !important;
  padding: 10px 20px !important;
  transition: all 0.15s !important;
}
[data-testid="stDownloadButton"] > button:hover {
  background: #FB923C !important;
  border-color: #FB923C !important;
  box-shadow: 0 4px 16px rgba(249,115,22,0.35) !important;
  transform: translateY(-1px) !important;
}

/* ═══════════════════════════════════════════
   GEN PIPELINE CARDS
═══════════════════════════════════════════ */
.gen-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r);
  padding: 14px 16px; margin-bottom: 10px;
}
.gen-card-title {
  font-size: 13px; font-weight: 600;
  color: var(--c-text-pri); margin: 0 0 8px;
  display: flex; align-items: center; gap: 8px;
}
.step-badge {
  font-family: var(--font-mono);
  background: var(--c-amber-a10);
  border: 1px solid var(--c-border-hi);
  border-radius: 4px; padding: 1px 6px;
  font-size: 10px; font-weight: 500;
  color: var(--c-amber); letter-spacing: 0.5px;
}
.step-badge.done {
  background: var(--c-green-bg);
  border-color: var(--c-green-bd);
  color: var(--c-green);
}

/* ═══════════════════════════════════════════
   ALERTS & NOTIFICATIONS
═══════════════════════════════════════════ */
[data-testid="stAlert"],
.stSuccess, .stInfo, .stWarning, .stError {
  background: var(--c-surface-hi) !important;
  border: 1px solid var(--c-border) !important;
  border-radius: var(--r) !important;
  font-size: 13px !important;
}
[data-testid="stAlert"][kind="success"],
.stSuccess {
  background: var(--c-green-bg) !important;
  border-color: var(--c-green-bd) !important;
}
[data-testid="stAlert"][kind="info"],
.stInfo {
  background: rgba(96,165,250,0.06) !important;
  border-color: rgba(96,165,250,0.18) !important;
}
[data-testid="stAlert"][kind="warning"],
.stWarning {
  background: var(--c-amber-a10) !important;
  border-color: var(--c-border-hi) !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div { color: var(--c-text-sec) !important; }
[data-testid="stAlert"] svg { fill: var(--c-text-ter) !important; }

/* ═══════════════════════════════════════════
   TABS
═══════════════════════════════════════════ */
[data-testid="stTabs"] [role="tablist"] {
  background: transparent !important;
  border-bottom: 1px solid var(--c-border) !important;
  gap: 0 !important;
  padding: 0 !important;
}
[data-testid="stTabs"] [role="tab"] {
  font-family: var(--font-sans) !important;
  font-size: 13px !important; font-weight: 500 !important;
  color: var(--c-text-ter) !important;
  padding: 10px 16px !important;
  letter-spacing: -0.1px !important;
  text-transform: none !important;
  border-bottom: 2px solid transparent !important;
  transition: color 0.15s !important;
}
[data-testid="stTabs"] [role="tab"]:hover { color: var(--c-text-sec) !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  color: var(--c-text-pri) !important;
  border-bottom-color: var(--c-amber) !important;
  font-weight: 600 !important;
}
[data-testid="stTabs"] [role="tabpanel"] { padding-top: 22px !important; }

/* ═══════════════════════════════════════════
   EXPANDERS
═══════════════════════════════════════════ */
[data-testid="stExpander"] {
  background: var(--c-surface) !important;
  border: 1px solid var(--c-border) !important;
  border-radius: var(--r) !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {
  color: var(--c-text-sec) !important;
  font-size: 13px !important; font-weight: 500 !important;
}
[data-testid="stExpander"] > div > div { background: transparent !important; }

/* ═══════════════════════════════════════════
   MISC
═══════════════════════════════════════════ */
.nexus-divider {
  height: 1px; background: var(--c-border); margin: 20px 0;
}

.stSpinner > div { border-top-color: var(--c-amber) !important; }
[data-testid="stSpinner"] p { color: var(--c-text-ter) !important; }

::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(249,115,22,0.25); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--c-amber); }

.stMarkdown p, .stMarkdown li {
  font-size: 13px !important; line-height: 1.6 !important;
  color: var(--c-text-sec) !important;
}
.stMarkdown code, code {
  font-family: var(--font-mono) !important;
  font-size: 11px !important;
  color: var(--c-amber) !important;
  background: var(--c-amber-a10) !important;
  padding: 1px 5px !important; border-radius: 3px !important;
}
[data-testid="stRadio"] label span,
[data-testid="stCheckbox"] label span { color: var(--c-text-sec) !important; }

[data-testid="column"] { gap: 0 !important; }
.stVerticalBlock { gap: 10px !important; }

@keyframes fade-up {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate { animation: fade-up 0.4s cubic-bezier(0.16,1,0.3,1) both; }
</style>
""", unsafe_allow_html=True)


# ─── Topbar ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
  <p class="topbar-wordmark">Draft<span>Mind</span> AI</p>
  <div class="topbar-divider"></div>
  <p class="topbar-subtitle">Dissertation Generator</p>
  <div class="topbar-badge">System Ready</div>
</div>
""", unsafe_allow_html=True)

# ─── Helpers ─────────────────────────────────────────────────────────────────
directory = "OutputFiles"

def read_file_auto_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw = f.read()
        enc = chardet.detect(raw)['encoding']
        return raw.decode(enc or 'utf-8', errors='replace')

def _list_to_str(val):
    if isinstance(val, list):
        return "\n".join(str(item) for item in val)
    if isinstance(val, dict):
        return json.dumps(val, indent=2)
    return str(val) if val is not None else ""

def _extract_result_plot_summary(val):
    if isinstance(val, dict) and "table" in val:
        rows = []
        for row in val["table"]:
            rows.append(
                f"Plot {row.get('Plot_Number','')}: {row.get('Title','')} | "
                f"Type: {row.get('Type','')} | Insights: {row.get('Insights','')}"
            )
        return "\n\n".join(rows)
    return _list_to_str(val)

def _extract_result_table(val):
    if not isinstance(val, dict):
        return _list_to_str(val)
    lines = []
    for table_key, table_data in val.items():
        if isinstance(table_data, dict):
            lines.append(f"\n### {table_key.replace('_', ' ').title()}")
            note = table_data.get("note", "")
            if note:
                lines.append(f"Note: {note}")
            cols = table_data.get("columns", [])
            rows = table_data.get("rows", [])
            if cols:
                lines.append(" | ".join(cols))
                lines.append(" | ".join(["---"] * len(cols)))
            for row in rows:
                lines.append(" | ".join(str(c) for c in row))
    return "\n".join(lines)

def _extract_code_summary_with_values(val):
    if isinstance(val, dict):
        return json.dumps(val, indent=2)
    return _list_to_str(val)

# ─── Session state ────────────────────────────────────────────────────────────
if 'generation_step' not in st.session_state:
    st.session_state.generation_step = 0

if 'sections_generated' not in st.session_state:
    st.session_state.sections_generated = {
        'keywords': False, 'citations': False, 'abstract': False,
        'introduction': False, 'methodology': False,
        'implementation': False, 'results': False
    }

if 'json_loaded' not in st.session_state:
    st.session_state.json_loaded = False

if 'json_data' not in st.session_state:
    st.session_state.json_data = {}

if 'lr_loaded' not in st.session_state:
    st.session_state.lr_loaded = False

if 'lr_filename' not in st.session_state:
    st.session_state.lr_filename = ""

if 'generation_running' not in st.session_state:
    st.session_state.generation_running = False

if 'docx_bytes' not in st.session_state:
    st.session_state.docx_bytes = None

if 'formatted_txt' not in st.session_state:
    st.session_state.formatted_txt = None

if 'dl_names' not in st.session_state:
    st.session_state.dl_names = {}

if 'docx_format' not in st.session_state:
    st.session_state.docx_format = "1"

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
      <div class="sb-logo-row">
        <div class="sb-logo-mark">D</div>
        <p class="sb-title">DraftMind AI</p>
      </div>
      <p class="sb-sub">Academic Report Engine &middot; v1.0</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><div class="sb-section-label">Pipeline</div></div>', unsafe_allow_html=True)

    steps_meta = [
        ("Keywords & Citations", ["keywords", "citations"]),
        ("Abstract",             ["abstract"]),
        ("Introduction",         ["introduction"]),
        ("Methodology",          ["methodology"]),
        ("Implementation",       ["implementation"]),
        ("Results & Conclusion", ["results"]),
    ]

    _sg = st.session_state.get("sections_generated", {})
    _gstep = st.session_state.get("generation_step", 0)

    for i, (name, keys) in enumerate(steps_meta):
        done   = all(_sg.get(k, False) for k in keys)
        active = (_gstep == i + 1)
        dot_cls = "done" if done else ("active" if active else "")
        icon    = "✓" if done else str(i + 1)
        txt_color = "var(--c-green)" if done else ("var(--c-amber)" if active else "var(--c-text-ter)")
        st.markdown(f"""
        <div class="step-row">
          <div class="step-dot {dot_cls}">{icon}</div>
          <span style="color:{txt_color};font-size:12px;font-weight:500">{name}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><div class="sb-section-label">Status</div></div>', unsafe_allow_html=True)

    _json_loaded = st.session_state.get("json_loaded", False)
    _lr_loaded   = st.session_state.get("lr_loaded", False)
    _gen_count   = sum(1 for v in _sg.values() if v)

    _jcolor = "var(--c-green)" if _json_loaded else "var(--c-red)"
    _jicon  = "●" if _json_loaded else "○"
    _jtext  = "JSON Loaded" if _json_loaded else "Manual Input"

    _lcolor = "var(--c-green)" if _lr_loaded else "var(--c-red)"
    _licon  = "●" if _lr_loaded else "○"
    _ltext  = "LR Loaded" if _lr_loaded else "No LR File"

    st.markdown(f"""
    <div class="stat-tile">
      <p class="stat-value" style="font-size:13px;color:{_jcolor}">{_jicon} {_jtext}</p>
      <p class="stat-label">JSON Data</p>
    </div>
    <div class="stat-tile">
      <p class="stat-value" style="font-size:13px;color:{_lcolor}">{_licon} {_ltext}</p>
      <p class="stat-label">Literature Review</p>
    </div>
    <div class="stat-tile">
      <p class="stat-value">{_gen_count}<span style="font-size:14px;color:var(--c-text-ter)">/7</span></p>
      <p class="stat-label">Sections Done</p>
    </div>
    """, unsafe_allow_html=True)

    if _json_loaded:
        st.markdown('<div class="sb-section"><div class="sb-section-label">Actions</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
        if st.button("✕ Clear JSON & Reset"):
            st.session_state.json_loaded = False
            st.session_state.json_data = {}
            st.session_state.generation_step = 0
            st.session_state.sections_generated = {k: False for k in st.session_state.sections_generated}
            st.session_state.lr_loaded = False
            st.session_state.lr_filename = ""
            st.session_state.docx_bytes = None
            st.session_state.formatted_txt = None
            st.session_state.dl_names = {}
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ─── Main Content ─────────────────────────────────────────────────────────────
st.markdown('<div class="content-wrap animate">', unsafe_allow_html=True)

st.markdown("""
<div class="page-hd">
  <p class="page-hd-eyebrow">DraftMind AI</p>
  <h1 class="page-hd-title">Dissertation Auto-Generation</h1>
  <p class="page-hd-sub">Upload a project JSON and Literature Review to auto-fill all fields, then run the 7-step generation pipeline.</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD ROW — JSON + LR in 2 columns
# ══════════════════════════════════════════════════════════════════════════════

def extract_text_from_upload(uploaded_file):
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    if name.endswith(".txt"):
        enc = chardet.detect(raw)['encoding'] or 'utf-8'
        return raw.decode(enc, errors='replace')
    elif name.endswith(".pdf"):
        if _PYPDF_OK:
            try:
                reader = _pypdf_mod.PdfReader(io.BytesIO(raw))
                return "\n\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as e:
                return f"[PDF extraction failed: {e}]"
        else:
            return "[PDF extraction unavailable — please install pypdf]"
    elif name.endswith(".docx"):
        if _DOCX_OK:
            try:
                doc = _docx_mod.Document(io.BytesIO(raw))
                return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            except Exception as e:
                return f"[DOCX extraction failed: {e}]"
        else:
            return "[DOCX extraction unavailable — please install python-docx]"
    else:
        enc = chardet.detect(raw)['encoding'] or 'utf-8'
        return raw.decode(enc, errors='replace')

col_json, col_lr = st.columns(2)

with col_json:
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">JSON Project Upload</div>', unsafe_allow_html=True)

        if st.session_state.json_loaded:
            loaded_title = st.session_state.json_data.get("title", "Untitled Project")[:70]
            st.markdown(f"""
            <div class="json-loaded-banner">
              <span class="jlb-icon">✦</span>
              <div>
                <div class="jlb-text">JSON Successfully Loaded</div>
                <div class="jlb-sub">{loaded_title}…</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.info("All fields have been pre-filled from the JSON.")
        else:
            st.markdown("""
            <div class="upload-zone">
              <div class="upload-icon">⬆</div>
              <div class="upload-title">Upload Project JSON</div>
              <div class="upload-sub">Drop your <code>project_analysis.json</code> here</div>
            </div>
            """, unsafe_allow_html=True)

            uploaded_json = st.file_uploader(
                "Select JSON file",
                type=["json"],
                label_visibility="collapsed",
                key="json_uploader"
            )

            if uploaded_json is not None:
                try:
                    raw = uploaded_json.read().decode("utf-8")
                    data = json.loads(raw)
                    st.session_state.json_data = data
                    st.session_state.json_loaded = True
                    st.success("JSON parsed successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to parse JSON: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

with col_lr:
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Literature Review Upload</div>', unsafe_allow_html=True)

        if st.session_state.lr_loaded:
            st.markdown(f"""
            <div class="json-loaded-banner">
              <span class="jlb-icon">✦</span>
              <div>
                <div class="jlb-text">Literature Review Loaded</div>
                <div class="jlb-sub">{st.session_state.lr_filename}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.info("LR saved — will be inserted after Introduction.")
            st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
            # if st.button("✕  Remove LR File", key="remove_lr"):
            #     st.session_state.lr_loaded = False
            #     st.session_state.lr_filename = ""
            #     st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="upload-zone">
              <div class="upload-icon">⬆</div>
              <div class="upload-title">Upload Literature Review</div>
              <div class="upload-sub">Supports <code>.pdf</code>, <code>.txt</code>, <code>.docx</code></div>
            </div>
            """, unsafe_allow_html=True)

            uploaded_lr = st.file_uploader(
                "Select LR file",
                type=["pdf", "txt", "docx"],
                label_visibility="collapsed",
                key="lr_uploader"
            )

            if uploaded_lr is not None:
                try:
                    lr_text = extract_text_from_upload(uploaded_lr)
                    ref_match = re.search(r'(?i)\n\s*references?\s*\n', lr_text)
                    if ref_match:
                        lr_body = lr_text[:ref_match.start()].strip()
                        lr_refs = lr_text[ref_match.end():].strip()
                    else:
                        lr_body = lr_text.strip()
                        lr_refs = ""

                    os.makedirs("OutputFiles", exist_ok=True)

                    # Append research gap as a final subsection of the LR chapter
                    rg_content = ""
                    if st.session_state.json_loaded:
                        rg_raw = st.session_state.json_data.get("research_gap", "")
                        rg_content = rg_raw.strip() if isinstance(rg_raw, str) else ""

                    if rg_content:
                        lr_with_gap = (
                            lr_body.strip()
                            + "\n\nResearch Gap\n"
                            + "-" * 40 + "\n"
                            + rg_content
                        )
                    else:
                        lr_with_gap = lr_body.strip()

                    save_text_file(lr_with_gap, "OutputFiles/lr.txt")
                    if lr_refs:
                        save_text_file(lr_refs, "OutputFiles/references_lr.txt")

                    st.session_state.lr_loaded = True
                    st.session_state.lr_filename = uploaded_lr.name
                    st.success(f"Literature Review saved — {len(lr_body.split())} words extracted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to process LR file: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="nexus-divider"></div>', unsafe_allow_html=True)

# ── Helper to get default value ──
def default(key, fallback="", transform=None):
    if st.session_state.json_loaded and key in st.session_state.json_data:
        val = st.session_state.json_data[key]
        if transform:
            return transform(val)
        return _list_to_str(val)
    return fallback

# ── Silently populate input files from JSON data ──
title          = default("title")
format_val_raw = "1"   # will be set from tab_input below
question       = default("research_question")
objective      = default("research_objectives", transform=lambda v: "\n".join(v) if isinstance(v, list) else _list_to_str(v))
data_details   = default("data_details")
pipeline_val   = default("code_pipeline")

literature_review_summary = default("literature_review_summary")
research_gaps             = default("research_gap")
base_paper_summary        = default("base_paper_summary")
base_paper_citation       = default("base_paper_reference")
code_summary              = default("code_summary")
code_summary_with_values  = default("code_summary_with_values", transform=_extract_code_summary_with_values)
webapp_summary            = default("web_app_summary")
webapp_test               = default("web_app_test_cases")
novelty                   = default("novelty")
result_plot_summary       = default("result_plot_summary", transform=_extract_result_plot_summary)
result_table_summary      = default("result_table", transform=_extract_result_table)
failed_attempt_summary    = default("failed_attempts")

# Save all input files silently
os.makedirs("InputFiles", exist_ok=True)
save_text_file(data_details,      "InputFiles/dd.txt")
save_text_file(pipeline_val,      "InputFiles/pipeline.txt")
save_text_file(literature_review_summary, "InputFiles/lrs.txt")
save_text_file(research_gaps,     "InputFiles/rg.txt")
save_text_file(base_paper_summary,"InputFiles/bps.txt")
save_text_file(code_summary,      "InputFiles/cs.txt")
save_text_file(code_summary_with_values, "InputFiles/csvs.txt")
save_text_file(webapp_summary,    "InputFiles/ws.txt")
save_text_file(webapp_test,       "InputFiles/wat.txt")
save_text_file(novelty,           "InputFiles/novelty.txt")
save_text_file(result_plot_summary + "\n\n" + result_table_summary, "InputFiles/rs.txt")
save_text_file(result_plot_summary + "\n\n" + failed_attempt_summary, "InputFiles/fa.txt")

# ══════════════════════════════════════════════════════════════════════════════
# EXTRACT DATA PROMPT — raw template
# ══════════════════════════════════════════════════════════════════════════════
_ED_PROMPT_RAW = (
    "Data Details:\n"
    "DATA_DETAILS_PLACEHOLDER\n\n"
    "Attached files to analyse [ZIP], it will contain:\n"
    "Proposal\n"
    "Literature Review\n"
    "Complete code in ipynb format\n\n"
    "title: Fetch it from the attached proposal\n"
    "Research question: Fetch it from the attached proposal\n"
    "Research objectives: Fetch these from the attached proposal\n"
    "acc_value: best accuracy values achieved\n\n"
    "## LITERATURE REVIEW SUMMARY\n"
    "Analyze the given Literature Review and generate a structured summary while preserving all essential technical content and citations. Before summarization, conduct a background search to understand the topic thoroughly. The summary should be 15-20% of the original length while maintaining clarity, coherence, and completeness. Summary Must Include: Topic Overview, Importance of the Chosen Field (with Citations), Key Technical Content, Findings & Insights, Limitations Identified, Unresolved Issues, Preserve Citations. Parameters: Word Limit 525-700 words for 3,500 words. Technical Accuracy: Maintain integrity of complex concepts. Mention all important values like performance percentage. Citation Integrity: Do not remove or alter any references.\n\n"
    "## RESEARCH GAP\n"
    "Using the literature review that I have already collected and the research pipeline on which I have completed my research code, write a proper research gap. This research gap should be in a way that it points to those methods which I have used in the code and were missing or suggested in the literature. Do not explicitly mention my research. Word count: 300 words.\n\n"
    "## BASE PAPER\n"
    "can you find only one research paper which is based on {title} and having accuracy below {acc_value} research paper should be from the past 2 years.\n"
    "Instructions:\n"
    "1. What is the complete flow or pipeline of research\n"
    "2. Details of the data getting used.\n"
    "3. What is the accuracy of all the algorithms used?\n"
    "4. Which algorithm achieved best accuracy and what is it\n"
    "5. What is the novel or unique element in the research\n"
    "6. What are the future recommendations of the research paper?\n"
    "All in 500 words. Provide reference in Harvard style.\n\n"
    "## CODE SUMMARY\n"
    "Summarize the following code into 2-3 concise paragraphs while preserving all essential technical details. Summary must include: Overview, Key Components, Execution Flow, Core Logic, Web App Elements (if any). Format: Paragraph-based, 15-20% of original length. Word count: 300 words.\n\n"
    "## CODE SUMMARY WITH VALUES\n"
    "Analyze the given code (~1000 lines). Extract a list of libraries used and segment into: Statistical Analysis, Exploratory Data Analysis (EDA) with plot details, Data Preprocessing, Feature Engineering, Train Split Information, Model Details (including layers for deep learning), Model Results & Performance Evaluation table. Format: Structured and well-organized.\n\n"
    "## WEBAPP SUMMARY\n"
    "Analyze the given web application code and generate a concise summary (150-200 words) covering: Overview, Python Framework Used, Libraries & Dependencies, User Input Handling, Main Functions & Features, Prediction Function.\n\n"
    "## WEBAPP TEST CASES\n"
    "Provide me the insight of the web test result in 150 words with mentioning each of the values and don't use parenthesis to mention values'()'\n\n"
    "## NOVELTY\n"
    "You are an elite software researcher. Write a single well-structured paragraph of exactly ~300 words explaining the novelty of the code. Focus on: unique algorithmic improvements, distinctive architectural decisions, efficiency enhancements, novel engineering techniques, scalability/maintainability improvements, trade-offs made. Maintain a formal research-oriented tone similar to a top-tier conference paper (NeurIPS, ICSE, SOSP).\n\n"
    "## RESULTS PLOT SUMMARY\n"
    "Requirements: 1. Create a table. 2. Mention all plots individually. Table columns: Title, Type of plot, Insights. Charts: Explainable AI, ROC, AUC, Training and loss neural network, comparison curve, confusion matrix. Note: Do not include plots from data exploration/preprocessing steps. For comparison plots mention insight as 'will be taken from table'.\n\n"
    "## RESULTS TABLE\n"
    "Generate a table for: Performance Table: Include all models, all metrics (as extracted from the code), and highlight the best-performing model.\n\n"
    "## FAILED ATTEMPT\n"
    "Write a concise section titled 'Failed Attempts and Design Iterations'. Begin with a 25-35 word introduction. Describe unsuccessful/suboptimal methods and why they failed. Provide technical reasoning for each failure.\n\n"
    "## REFERENCES\n"
    "From the research pipeline/code, write approx 15 important keywords. For each keyword find a reference paper related to {title}. Parameters: Keyword, title, reference, citation. Reference in Harvard style.\n\n"
    "## Output format (JSON):\n"
    "{\n"
    "  'title': <title>,\n"
    "  'research_question': <Research question>,\n"
    "  'research_objectives': <Research objectives>,\n"
    "  'data_details': <Data Details>,\n"
    "  'literature_review_summary': <LR summary>,\n"
    "  'research_gap': <research gap>,\n"
    "  'best_accuracy': <acc_value>,\n"
    "  'base_paper_summary': <summary>,\n"
    "  'base_paper_reference': <reference>,\n"
    "  'code_summary': <code summary>,\n"
    "  'code_summary_with_values': <code summary with values>,\n"
    "  'web_app_summary': <web app summary>,\n"
    "  'web_app_test_cases': <web app test cases>,\n"
    "  'novelty': <novelty>,\n"
    "  'result_plot_summary': <result plot summary>,\n"
    "  'result_table': <result table>,\n"
    "  'failed_attempts': <failed attempts>,\n"
    "  'references': <references>\n"
    "}"
)

# ══════════════════════════════════════════════════════════════════════════════
# TABS — Prompt (first) | Input Fields | Input Files
# ══════════════════════════════════════════════════════════════════════════════
tab_prompt, tab_gen, tab_files = st.tabs(["📋 Prompt", "⚡ Generation Pipeline", "📦 Input Files"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PROMPT (Extract Data Prompt)
# ══════════════════════════════════════════════════════════════════════════════
with tab_prompt:
    st.markdown('<div class="section-card"><div class="section-heading">Extract Data Prompt</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size:12px;color:var(--c-text-sec);margin:0 0 18px">
      Enter your data details below. They will be injected into the prompt automatically.
      Copy the full prompt and send it together with your ZIP file to an AI tool.
    </p>
    """, unsafe_allow_html=True)

    eda_data_details = st.text_area(
        "Data Details",
        value=data_details,
        height=130,
        key="eda_data_details_input",
        placeholder="e.g. Dataset: Heart disease dataset from Kaggle. 303 rows, 14 columns including Age, Cholesterol, Target..."
    )

    _dd = eda_data_details.strip() if eda_data_details.strip() else "<paste your data details here>"
    full_ed_prompt = _ED_PROMPT_RAW.replace("DATA_DETAILS_PLACEHOLDER", _dd)
    save_text_file(full_ed_prompt, "InputFiles/ed.txt")

    st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-heading" style="margin-bottom:10px">Full Prompt Preview</div>', unsafe_allow_html=True)

    st.text_area(
        "prompt_preview",
        value=full_ed_prompt,
        height=340,
        key="ed_prompt_preview",
        label_visibility="collapsed"
    )

    _escaped = full_ed_prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    components.html(f"""
<style>
  #ed-copy-btn {{
    background: var(--c-surface-hi, #1E1A15); color: #F97316; border: 1px solid rgba(249,115,22,0.25);
    border-radius: 8px; padding: 10px 22px; font-size: 13px; font-family: 'DM Sans', sans-serif;
    cursor: pointer; letter-spacing: 0.5px; transition: all 0.2s; margin-top: 4px;
  }}
  #ed-copy-btn:hover {{ background: rgba(249,115,22,0.18); box-shadow: 0 4px 14px rgba(249,115,22,0.25); }}
</style>
<textarea id="ed-hidden" readonly style="position:fixed;top:-9999px;left:-9999px;opacity:0;">{_escaped}</textarea>
<button id="ed-copy-btn" onclick="
  var el = document.getElementById('ed-hidden');
  el.value = el.textContent;
  el.select();
  el.setSelectionRange(0, 99999);
  try {{
    document.execCommand('copy');
    this.textContent = 'Copied!';
  }} catch(e) {{
    navigator.clipboard.writeText(el.textContent).then(() => {{ this.textContent = 'Copied!'; }});
  }}
  var btn = this;
  setTimeout(function() {{ btn.textContent = 'Copy Full Prompt'; }}, 1800);
">Copy Full Prompt</button>
""", height=56)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — GENERATION PIPELINE (Format selector + Pipeline)
# ══════════════════════════════════════════════════════════════════════════════
with tab_gen:

    # ── Format selector ──
    st.markdown('<div class="section-card"><div class="section-heading">Document Format</div>', unsafe_allow_html=True)
    format_val = st.selectbox("Select Format", ["1", "2", "3", "4"])
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="nexus-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # GENERATION PIPELINE (inline in Input Fields tab)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""
<h2 style="font-family:'Syne',sans-serif;font-size:20px;color:#FFFFFF;margin:0 0 6px">
  Document Generation
  <span style="color:var(--c-amber)">Pipeline</span>
</h2>
<p style="font-size:12px;color:var(--c-text-sec);margin:0 0 22px">
  Click <strong style="color:var(--c-amber)">Start</strong> — all sections will be generated automatically in sequence.
</p>
""", unsafe_allow_html=True)

    # Update config before generation
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)

        config["TITLE"]               = title
        config["FORMAT"]              = format_val
        config['RESEARCH_QUESTION']   = question
        config['RESEARCH_OBJECTIVES'] = objective
        config["BASE_PAPER_CITATION"] = base_paper_citation
        config["PROMPT"]              = "ed.txt"

        with open("config.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
    except Exception:
        pass

    _step_labels = ["Keywords", "Citations", "Abstract", "Intro", "Method", "Impl.", "Results"]
    _step_keys   = ["keywords", "citations", "abstract", "introduction", "methodology", "implementation", "results"]
    _cur_step    = st.session_state.get("generation_step", 0)
    _is_running  = st.session_state.get("generation_running", False)

    # ── Progress tracker ──
    prog_cols = st.columns(7)
    for i, (lbl, key) in enumerate(zip(_step_labels, _step_keys)):
        with prog_cols[i]:
            done   = st.session_state.sections_generated.get(key, False)
            active = _is_running and (_cur_step == i)
            if done:
                bg      = "var(--c-green-bg)"
                border  = "var(--c-green-bd)"
                top_clr = "var(--c-green)"
                icon    = "\u2713"
                lbl_clr = "var(--c-green)"
            elif active:
                bg      = "var(--c-amber-a10)"
                border  = "var(--c-amber)"
                top_clr = "var(--c-amber)"
                icon    = str(i + 1)
                lbl_clr = "var(--c-amber)"
            else:
                bg      = "var(--surface)"
                border  = "var(--c-border)"
                top_clr = "var(--c-border)"
                icon    = str(i + 1)
                lbl_clr = "rgba(255,255,255,0.40)"
            glow = "box-shadow:0 0 0 2px rgba(249,115,22,0.20);" if active else ""
            st.markdown(f"""
            <div style="text-align:center;padding:10px 4px;background:{bg};
                        border:1px solid {border};border-radius:8px;
                        border-top:2px solid {top_clr};{glow}transition:all 0.3s ease;">
              <div style="font-size:16px;color:{lbl_clr}">{icon}</div>
              <div style="font-size:10px;color:{lbl_clr};letter-spacing:1px;text-transform:uppercase;margin-top:4px">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── LR status row ──
    _lr_done      = st.session_state.get("lr_loaded", False)
    _lr_color     = "var(--c-green-bg)" if _lr_done else "var(--c-red-bg)"
    _lr_border    = "var(--c-green-bd)" if _lr_done else "var(--c-red-bd)"
    _lr_txt_color = "var(--c-green)" if _lr_done else "var(--c-red)"
    _lr_icon      = "\u2713" if _lr_done else "\u25cb"
    _lr_msg       = "Literature Review uploaded \u2014 will be inserted after Introduction in the final document." if _lr_done else "No Literature Review uploaded \u2014 it will be skipped in the final document."
    st.markdown(f"""
    <div style="margin-top:10px;padding:10px 16px;background:{_lr_color};border:1px solid {_lr_border};
                border-radius:8px;display:flex;align-items:center;gap:10px;">
      <span style="font-size:16px;color:{_lr_txt_color};flex-shrink:0">{_lr_icon}</span>
      <span style="font-size:11px;color:{_lr_txt_color};letter-spacing:0.3px">{_lr_msg}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    all_done = _cur_step >= 7

    _step_funcs = [
        (generate_keywords,                                                      "keywords",       "Step 1/7 \u00b7 Generating keywords\u2026"),
        (lambda: get_ref_citation(st.session_state["json_data"]["references"]),  "citations",      "Step 2/7 \u00b7 Generating citations\u2026"),
        (generate_abstract,                                                      "abstract",       "Step 3/7 \u00b7 Generating abstract\u2026"),
        (generate_introduction,                                                  "introduction",   "Step 4/7 \u00b7 Generating introduction\u2026"),
        (generate_methodology,                                                   "methodology",    "Step 5/7 \u00b7 Generating methodology\u2026"),
        (generate_implementation,                                                "implementation", "Step 6/7 \u00b7 Generating implementation\u2026"),
        (generate_result_conclusion,                                             "results",        "Step 7/7 \u00b7 Generating results & conclusion\u2026"),
    ]

    if not all_done:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        start_clicked = st.button("\u2726  Start Generation Process")
        st.markdown('</div>', unsafe_allow_html=True)

        if _is_running and 0 <= _cur_step < 7:
            fn, key, label = _step_funcs[_cur_step]
            with st.spinner(label):
                fn()
            st.session_state.sections_generated[key] = True
            st.session_state.generation_step = _cur_step + 1
            if _cur_step + 1 >= 7:
                st.session_state.generation_running = False
            st.rerun()

        elif start_clicked and not _is_running:
            st.session_state.generation_running = True
            st.session_state.generation_step    = 0
            for k in st.session_state.sections_generated:
                st.session_state.sections_generated[k] = False
            st.rerun()

    # ── Final Download ──
    if st.session_state.generation_step >= 7:
        st.markdown('<div class="nexus-divider"></div>', unsafe_allow_html=True)
        st.markdown("""
    <div style="background:var(--c-green-bg);border:1px solid var(--c-green-bd);border-radius:10px;padding:20px 22px;margin-bottom:16px;display:flex;align-items:center;gap:14px">
      <div style="width:36px;height:36px;border-radius:8px;background:var(--c-green-bg);border:1px solid var(--c-green-bd);display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0">✓</div>
      <div>
        <p style="font-size:14px;font-weight:700;color:var(--c-green);margin:0 0 2px;letter-spacing:-0.1px">Generation Complete</p>
        <p style="font-size:12px;color:var(--c-text-sec);margin:0">All 7 sections generated. Your dissertation report is ready to download.</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

        sections = [
            ("abstract.txt",        "ABSTRACT"),
            ("introduction.txt",    "1. INTRODUCTION"),
            ("lr.txt",              "2. LITERATURE REVIEW"),
            ("methodology.txt",     "3. METHODOLOGY"),
            ("implementation.txt",  "4. IMPLEMENTATION"),
            ("results.txt",         "5. RESULTS AND CONCLUSION"),
            ("conclusion.txt",      "6. CONCLUSION"),
        ]

        doc_title = title.strip().upper() if title.strip() else "DISSERTATION REPORT"
        separator = "=" * 70
        combined_content = f"{separator}\n{doc_title}\n{separator}\n\n"

        def _strip_internal_label(text):
            import re as _re
            text = _re.sub(r"^#{1,6}\s*", "", text, flags=_re.MULTILINE)
            lines = text.splitlines()
            while lines and not lines[0].strip():
                lines.pop(0)
            if lines and lines[0].strip().isupper() and len(lines[0].strip()) < 80:
                lines.pop(0)
            if lines and set(lines[0].strip()) <= {"-"}:
                lines.pop(0)
            while lines and not lines[0].strip():
                lines.pop(0)
            return "\n".join(lines).strip()

        for fn, heading in sections:
            fp = os.path.join(directory, fn)
            try:
                raw_text = read_file_auto_encoding(fp).strip()
                section_text = _strip_internal_label(raw_text)
                if section_text:
                    combined_content += f"{separator}\n{heading}\n{separator}\n\n{section_text}\n\n\n"
            except FileNotFoundError:
                if fn != "lr.txt":
                    st.warning(f"{fn} not found — skipping.")

        all_ref_lines = []

        def _parse_refs(raw_text):
            raw_text = raw_text.strip()
            if not raw_text:
                return []
            entries = [e.strip() for e in re.split(r'\n{2,}', raw_text) if e.strip()]
            if len(entries) <= 1:
                entries = [e.strip() for e in re.split(r'\n(?=[A-Z])', raw_text) if e.strip()]
            return entries

        lr_refs_fp = os.path.join(directory, "references_lr.txt")
        try:
            all_ref_lines += _parse_refs(read_file_auto_encoding(lr_refs_fp))
        except FileNotFoundError:
            pass

        try:
            json_refs = st.session_state.json_data.get("references", [])
            if isinstance(json_refs, list):
                for item in json_refs:
                    if isinstance(item, dict) and "reference" in item:
                        all_ref_lines.append(item["reference"].strip())
                    elif isinstance(item, str) and item.strip():
                        all_ref_lines.append(item.strip())
            elif isinstance(json_refs, str) and json_refs.strip():
                all_ref_lines += _parse_refs(json_refs)
        except Exception:
            pass

        for ref_file in ["references.txt", "keywords.txt", "citations.txt"]:
            try:
                all_ref_lines += _parse_refs(read_file_auto_encoding(os.path.join(directory, ref_file)))
            except FileNotFoundError:
                pass

        def _norm_ref_key(text):
            # Stronger normalization: lowercase, alphanumeric only, first 100 chars
            return re.sub(r"[^a-z0-9]", "", text.lower())[:100]

        seen_keys = set()
        unique_refs = []
        for r in all_ref_lines:
            key = _norm_ref_key(r)
            if key and key not in seen_keys:
                seen_keys.add(key)
                unique_refs.append(r)

        unique_refs.sort(key=lambda x: re.sub(r'^[\d\.\s\[\]]+', '', x).lower())

        if unique_refs:
            refs_block = "\n\n".join(unique_refs)
            combined_content += f"{separator}\nREFERENCES\n{separator}\n\n{refs_block}\n"
        else:
            combined_content += f"{separator}\nREFERENCES\n{separator}\n\n[No references found]\n"

        safe_title = "".join(c for c in title if c.isalnum() or c in [' ', '_', '-']).strip().replace(" ", "_")
        dl_name_txt = f"{safe_title}_dissertation.txt"
        dl_name_docx = f"{safe_title}_dissertation.docx"

        # ── TXT to DOCX Conversion ──
        docx_ready = False
        try:
            # Only generate docx/formatted_txt once per session/run to avoid re-runs on download clicks
            selected_fmt = int(format_val)
            if (st.session_state.docx_bytes is None
                    or st.session_state.formatted_txt is None
                    or st.session_state.docx_format != format_val):
                st.session_state.docx_format = format_val
                tokens = parse_structure(combined_content)
                warnings = validate(tokens)
                # Remove repeated in-text citations globally
                tokens = apply_global_citation_deduplication(tokens)
                # use_llm=False to avoid token waste; prompts already handle numbering well
                tokens = refine_with_llm(tokens, use_llm=False)
                
                # Format DOCX
                docx_buf = io.BytesIO()
                generate_docx(tokens, warnings, docx_buf, format=selected_fmt)
                st.session_state.docx_bytes = docx_buf.getvalue()
                
                # Format clean TXT with accurate N.M hierarchical numbering
                clean_txt = generate_formatted_txt(tokens)
                st.session_state.formatted_txt = clean_txt.encode("utf-8")
                
                st.session_state.dl_names = {
                    "txt": dl_name_txt,
                    "docx": dl_name_docx
                }
            
            docx_ready = st.session_state.docx_bytes is not None
        except Exception as e:
            st.error(f"Failed to generate formatting: {e}")
            docx_ready = False

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                label="⬇  Download format .TXT",
                data=st.session_state.formatted_txt,
                file_name=st.session_state.dl_names.get("txt", dl_name_txt),
                mime="text/plain",
                use_container_width=True
            )
        with c2:
            if docx_ready:
                st.download_button(
                    label="⬇  Download format .DOCX",
                    data=st.session_state.docx_bytes,
                    file_name=st.session_state.dl_names.get("docx", dl_name_docx),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            else:
                st.button("❌ DOCX Error", disabled=True, use_container_width=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
        if st.button("↺  Start New Document"):
            st.session_state.generation_step = 0
            st.session_state.generation_running = False
            st.session_state.sections_generated = {k: False for k in st.session_state.sections_generated}
            st.session_state.json_loaded = False
            st.session_state.json_data = {}
            st.session_state.lr_loaded = False
            st.session_state.lr_filename = ""
            st.session_state.docx_bytes = None
            st.session_state.formatted_txt = None
            st.session_state.dl_names = {}
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — INPUT FILES
# ══════════════════════════════════════════════════════════════════════════════
with tab_files:
    import zipfile

    st.markdown("""
<h2 style="font-family:'Syne',sans-serif;font-size:20px;color:#FFFFFF;margin:0 0 6px">
  Input Files
  <span style="color:var(--c-amber)">Package</span>
</h2>
<p style="font-size:12px;color:var(--c-text-sec);margin:0 0 22px">
  Upload the four source files below. Once all are uploaded a ZIP will be
  available for download — ready to attach to any AI prompt tool.
</p>
""", unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-heading">Upload Source Files</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<p style="font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--c-text-sec);margin:0 0 6px">Literature Review</p>', unsafe_allow_html=True)
        up_lr_pkg = st.file_uploader(
            "Literature Review file",
            type=["pdf", "txt", "docx"],
            label_visibility="collapsed",
            key="pkg_lr"
        )

        st.markdown('<p style="font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--c-text-sec);margin:16px 0 6px">Code Notebook</p>', unsafe_allow_html=True)
        up_nb = st.file_uploader(
            "Code notebook file",
            type=["ipynb", "py", "txt"],
            label_visibility="collapsed",
            key="pkg_nb"
        )

    with col_b:
        st.markdown('<p style="font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--c-text-sec);margin:0 0 6px">Web Application File</p>', unsafe_allow_html=True)
        up_web = st.file_uploader(
            "Web application file",
            type=["py", "txt", "html", "js"],
            label_visibility="collapsed",
            key="pkg_web"
        )

        st.markdown('<p style="font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--c-text-sec);margin:16px 0 6px">Proposal File</p>', unsafe_allow_html=True)
        up_proposal = st.file_uploader(
            "Proposal file",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
            key="pkg_proposal"
        )

    st.markdown('</div>', unsafe_allow_html=True)

    _pkg_files = {
        "Literature Review":    up_lr_pkg,
        "Code Notebook":        up_nb,
        "Web Application File": up_web,
        "Proposal":             up_proposal,
    }
    _uploaded_count = sum(1 for f in _pkg_files.values() if f is not None)

    st.markdown('<div class="section-card"><div class="section-heading">Files Status</div>', unsafe_allow_html=True)
    status_cols = st.columns(4)
    for idx, (label, ufile) in enumerate(_pkg_files.items()):
        with status_cols[idx]:
            _ok    = ufile is not None
            _color = "var(--emerald)" if _ok else "var(--mist)"
            _icon  = "✓" if _ok else "○"
            _name  = ufile.name if _ok else "—"
            st.markdown(f"""
            <div style="text-align:center;padding:12px 6px;background:var(--c-surface-hi);border:1px solid var(--c-border);
                        border-radius:8px;border-top:2px solid {'var(--c-green)' if _ok else 'var(--c-border)'}">
              <div style="font-size:18px;color:{_color}">{_icon}</div>
              <div style="font-size:10px;color:{_color};letter-spacing:1px;text-transform:uppercase;margin-top:4px">{label}</div>
              <div style="font-size:10px;color:var(--c-text-sec);margin-top:4px;word-break:break-all">{_name}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if _uploaded_count > 0:
        _name_map = {
            "Literature Review":    ("lr",       up_lr_pkg),
            "Code Notebook":        ("notebook",  up_nb),
            "Web Application File": ("web_app",   up_web),
            "Proposal":             ("proposal",  up_proposal),
        }

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for _label, (_base, _uf) in _name_map.items():
                if _uf is not None:
                    _ext  = os.path.splitext(_uf.name)[1]
                    _uf.seek(0)
                    zf.writestr(f"InputFiles/{_base}{_ext}", _uf.read())

        zip_buf.seek(0)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.download_button(
            label=f"⬇  Download ZIP ({_uploaded_count} file{'s' if _uploaded_count != 1 else ''})",
            data=zip_buf.getvalue(),
            file_name="data.zip",
            mime="application/zip"
        )

        _contents = [f"InputFiles/{_base}{os.path.splitext(_uf.name)[1]}"
                     for _, (_base, _uf) in _name_map.items() if _uf is not None]
        st.markdown(
            f"<p style='font-size:11px;color:var(--c-text-sec);margin:8px 0 0'>"
            f"ZIP contains: {', '.join(_contents)}</p>",
            unsafe_allow_html=True
        )
    else:
        st.info("Upload at least one file above to enable ZIP download.")

st.markdown('</div>', unsafe_allow_html=True)  # close content-wrap
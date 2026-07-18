"""
Theme module.

Streamlit's native theming (`.streamlit/config.toml`) only covers basic
colors -- it can't produce gradient KPI cards, hover animations, or a
true runtime dark/light toggle (config.toml is fixed at app startup).
This module injects custom CSS to deliver the enterprise-analytics look
(Stripe/Databricks/Linear-inspired) requested, and reads/writes
st.session_state so the toggle persists across reruns within a session.

IMPORTANT: this file is the single source of truth for color. Two things
that used to fight each other are now handled here in one place:
  1. Custom components (KPI cards, badges) -- via CSS variables.
  2. Streamlit's OWN built-in widgets (buttons, inputs, dataframes,
     tabs, alerts, metrics, expanders, etc.) -- these do NOT automatically
     follow CSS variables set on :root, because Streamlit/BaseWeb apply
     their own inline-ish styling. They need explicit, targeted overrides
     keyed off `data-testid`/`data-baseweb` attributes.
  3. Plotly charts -- these have their own template system entirely
     separate from CSS. A chart drawn with the default template will
     render a white or mismatched plot area even when the rest of the
     app is dark. `apply_plotly_theme()` fixes this globally, once,
     rather than requiring every page's ~30 `st.plotly_chart(...)`
     call sites to be edited individually.
"""

import streamlit as st
import plotly.io as pio
import plotly.graph_objects as go

from config import COLOR_PRIMARY, COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING, COLOR_PURPLE


def init_theme_state():
    """Ensure a theme mode exists in session_state before any page reads it."""
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "light"


def toggle_theme():
    st.session_state.theme_mode = "dark" if st.session_state.theme_mode == "light" else "light"


def _light_vars() -> str:
    return """
        --bg-primary: #FFFFFF;
        --bg-secondary: #F5F7FA;
        --bg-card: #FFFFFF;
        --bg-input: #FFFFFF;
        --bg-hover: #EEF1F5;
        --text-primary: #1A1A1A;
        --text-secondary: #6B7280;
        --text-on-primary: #FFFFFF;
        --border-color: #E5E7EB;
        --shadow-color: rgba(15, 23, 42, 0.06);
        --code-bg: #F1F3F5;
    """


def _dark_vars() -> str:
    return """
        --bg-primary: #0E1117;
        --bg-secondary: #161B22;
        --bg-card: #1C222E;
        --bg-input: #1C222E;
        --bg-hover: #262D3A;
        --text-primary: #E6EDF3;
        --text-secondary: #9CA3AF;
        --text-on-primary: #FFFFFF;
        --border-color: #2D333B;
        --shadow-color: rgba(0, 0, 0, 0.35);
        --code-bg: #161B22;
    """


def current_mode() -> str:
    return st.session_state.get("theme_mode", "light")


def apply_plotly_theme():
    """
    Registers a custom Plotly template ("app_theme") whose colors follow
    the active light/dark mode, and makes it the DEFAULT for every figure
    created for the rest of this script run.

    Because Streamlit re-runs the whole script top-to-bottom on every
    interaction, calling this once (from inject_global_css, before any
    page builds a chart) is enough to theme every chart on every page --
    no need to touch each individual `px.bar(...)` / `go.Figure(...)`
    call site.

    Note: this sets *defaults*. A chart that explicitly hardcodes a color
    (e.g. `"color": "black"`) will still override the template for that
    one property -- that has to be fixed at the call site (see the gauge
    chart fix in churn_ltv_prediction.py).
    """
    mode = current_mode()
    if mode == "dark":
        base = pio.templates["plotly_dark"]
        font_color = "#E6EDF3"
        grid_color = "#2D333B"
        secondary_grid = "#3D4451"
    else:
        base = pio.templates["plotly_white"]
        font_color = "#1A1A1A"
        grid_color = "#E5E7EB"
        secondary_grid = "#D1D5DB"

    themed = go.layout.Template(base)
    themed.layout.paper_bgcolor = "rgba(0,0,0,0)"
    themed.layout.plot_bgcolor = "rgba(0,0,0,0)"
    themed.layout.font.color = font_color
    themed.layout.title.font.color = font_color
    themed.layout.legend.font.color = font_color
    themed.layout.xaxis.gridcolor = grid_color
    themed.layout.yaxis.gridcolor = grid_color
    themed.layout.xaxis.linecolor = secondary_grid
    themed.layout.yaxis.linecolor = secondary_grid
    themed.layout.xaxis.zerolinecolor = grid_color
    themed.layout.yaxis.zerolinecolor = grid_color
    themed.layout.colorway = [COLOR_PRIMARY, COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING, COLOR_PURPLE]

    pio.templates["app_theme"] = themed
    pio.templates.default = "app_theme"


def plotly_gauge_colors() -> dict:
    """
    Theme-aware colors for the churn-probability gauge (and any other
    gauge/indicator chart), so it doesn't hardcode light-mode-only colors
    like a black threshold line or pastel step backgrounds that vanish
    or clash in dark mode.
    """
    mode = current_mode()
    if mode == "dark":
        return {
            "step_low": "rgba(44,160,44,0.25)",
            "step_mid": "rgba(255,127,14,0.25)",
            "step_high": "rgba(214,39,40,0.25)",
            "threshold_line": "#E6EDF3",
            "axis_color": "#9CA3AF",
        }
    return {
        "step_low": "#e8f5e9",
        "step_mid": "#fff3e0",
        "step_high": "#ffebee",
        "threshold_line": "#1A1A1A",
        "axis_color": "#6B7280",
    }


def inject_global_css():
    """
    Call this once at the very top of every page (after st.set_page_config).
    Injects CSS variables for the current theme mode plus the shared
    component styles (cards, animations, badges) every page reuses, AND
    reskins Streamlit's native widgets so they follow the same variables,
    AND sets the matching Plotly template as default for this run.
    """
    mode = current_mode()
    vars_block = _dark_vars() if mode == "dark" else _light_vars()

    apply_plotly_theme()

    st.markdown(
        f"""
        <style>
        :root {{
            {vars_block}
            --color-primary: {COLOR_PRIMARY};
            --color-danger: {COLOR_DANGER};
            --color-success: {COLOR_SUCCESS};
            --color-warning: {COLOR_WARNING};
            --color-purple: {COLOR_PURPLE};
        }}

        /* ==================================================================
           BASE APP
        ================================================================== */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-color: var(--bg-primary);
            color: var(--text-primary);
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        [data-testid="stHeader"] {{ background-color: transparent; }}

        /* Body text, captions, lists -- Streamlit sometimes sets its own
           inline color on these, so we need !important to actually win. */
        [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] span,
        [data-testid="stCaptionContainer"], label, .stMarkdown {{
            color: var(--text-primary) !important;
        }}
        [data-testid="stCaptionContainer"] p {{
            color: var(--text-secondary) !important;
        }}
        a, a:visited {{ color: var(--color-primary) !important; }}

        h1, h2, h3 {{
            font-family: -apple-system, "Segoe UI", sans-serif;
            font-weight: 700;
            letter-spacing: -0.01em;
            color: var(--text-primary) !important;
        }}

        hr {{ border-color: var(--border-color) !important; }}

        /* ==================================================================
           SIDEBAR
        ================================================================== */
        section[data-testid="stSidebar"] {{
            background-color: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
        }}
        section[data-testid="stSidebar"] * {{ color: var(--text-primary); }}

        /* ==================================================================
           INPUTS: text input, number input, text area, selectbox, multiselect
        ================================================================== */
        .stTextInput input, .stNumberInput input, .stDateInput input,
        .stTextArea textarea {{
            background-color: var(--bg-input) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-color) !important;
        }}
        div[data-baseweb="select"] > div {{
            background-color: var(--bg-input) !important;
            border-color: var(--border-color) !important;
            color: var(--text-primary) !important;
        }}
        div[data-baseweb="popover"] li, ul[role="listbox"] li {{
            background-color: var(--bg-card) !important;
            color: var(--text-primary) !important;
        }}
        div[data-baseweb="tag"] {{
            background-color: var(--color-primary) !important;
        }}

        /* Slider track/handle stay legible in both modes */
        div[data-testid="stSlider"] [data-baseweb="slider"] > div > div {{
            background: var(--border-color);
        }}

        /* Checkbox / radio / toggle labels */
        .stCheckbox label, .stRadio label, .stToggle label {{
            color: var(--text-primary) !important;
        }}

        /* ==================================================================
           BUTTONS
        ================================================================== */
        .stButton button, .stDownloadButton button, .stFormSubmitButton button {{
            background-color: var(--color-primary);
            color: var(--text-on-primary) !important;
            border: 1px solid var(--color-primary);
            border-radius: 8px;
            transition: filter 0.15s ease;
        }}
        .stButton button:hover, .stDownloadButton button:hover {{
            filter: brightness(1.12);
        }}
        .stButton button[kind="secondary"] {{
            background-color: transparent;
            color: var(--color-primary) !important;
        }}

        /* ==================================================================
           TABS
        ================================================================== */
        .stTabs [data-baseweb="tab-list"] {{
            border-bottom: 1px solid var(--border-color);
        }}
        .stTabs [data-baseweb="tab"] {{
            color: var(--text-secondary);
        }}
        .stTabs [aria-selected="true"] {{
            color: var(--color-primary) !important;
            border-bottom-color: var(--color-primary) !important;
        }}

        /* ==================================================================
           EXPANDER
        ================================================================== */
        [data-testid="stExpander"] {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
        }}
        [data-testid="stExpander"] summary {{
            color: var(--text-primary) !important;
        }}

        /* ==================================================================
           METRICS (st.metric)
        ================================================================== */
        [data-testid="stMetric"] {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 0.75rem 1rem;
        }}
        [data-testid="stMetricLabel"] {{ color: var(--text-secondary) !important; }}
        [data-testid="stMetricValue"] {{ color: var(--text-primary) !important; }}

        /* ==================================================================
           DATAFRAMES / TABLES
        ================================================================== */
        [data-testid="stDataFrame"], [data-testid="stTable"] {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }}

        /* ==================================================================
           ALERTS (info / success / warning / error)
        ================================================================== */
        div[data-testid="stAlert"] {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary) !important;
        }}
        div[data-testid="stAlert"] p {{ color: var(--text-primary) !important; }}

        /* ==================================================================
           CODE BLOCKS
        ================================================================== */
        code {{
            background-color: var(--code-bg) !important;
            color: var(--text-primary) !important;
        }}
        pre {{
            background-color: var(--code-bg) !important;
            border: 1px solid var(--border-color);
        }}

        /* ==================================================================
           CUSTOM COMPONENTS (KPI cards, badges, skeletons, animations)
        ================================================================== */
        .kpi-card {{
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            box-shadow: 0 1px 3px var(--shadow-color);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            position: relative;
            overflow: hidden;
        }}
        .kpi-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 20px var(--shadow-color);
        }}
        .kpi-card::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: var(--kpi-accent, var(--color-primary));
            border-radius: 16px 16px 0 0;
        }}
        .kpi-label {{
            font-size: 0.82rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 0.35rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .kpi-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.1;
            font-family: -apple-system, "Segoe UI", sans-serif;
        }}
        .kpi-delta {{
            font-size: 0.8rem;
            font-weight: 600;
            margin-top: 0.4rem;
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
        }}
        .kpi-delta.positive {{ color: var(--color-success); }}
        .kpi-delta.negative {{ color: var(--color-danger); }}
        .kpi-delta.neutral {{ color: var(--text-secondary); }}

        .status-badge {{
            display: inline-block;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-green {{ background: rgba(44,160,44,0.15); color: var(--color-success); }}
        .badge-amber {{ background: rgba(255,127,14,0.15); color: var(--color-warning); }}
        .badge-red   {{ background: rgba(214,39,40,0.15); color: var(--color-danger); }}

        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}
        .fade-in {{ animation: fadeInUp 0.45s ease both; }}

        @keyframes shimmer {{
            0% {{ background-position: -400px 0; }}
            100% {{ background-position: 400px 0; }}
        }}
        .skeleton {{
            border-radius: 12px;
            height: 90px;
            background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--border-color) 37%, var(--bg-secondary) 63%);
            background-size: 800px 100%;
            animation: shimmer 1.4s ease infinite;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            transition: box-shadow 0.2s ease;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    """
    Renders the app footer: developer name, project name, and tech stack.
    Call this once, at the bottom of app.py's main() router (after the
    page has rendered) -- since every page goes through that one router,
    the footer shows up at the bottom of every page automatically,
    without needing to add anything to each individual page file.
    """
    from config import AUTHOR_NAME, PROJECT_NAME, TECH_STACK

    badges_html = "".join(
        f'<span class="footer-badge">{tech}</span>' for tech in TECH_STACK
    )

    st.markdown(
        f"""
        <style>
        .app-footer {{
            margin-top: 3rem;
            padding-top: 1.25rem;
            border-top: 1px solid var(--border-color);
            text-align: center;
        }}
        .footer-line {{
            font-size: 0.9rem;
            color: var(--text-primary);
            margin-bottom: 0.6rem;
        }}
        .footer-badge {{
            display: inline-block;
            margin: 0.15rem;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--text-secondary);
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
        }}
        </style>
        <div class="app-footer fade-in">
            <div class="footer-line">
                Developed by <strong>{AUTHOR_NAME}</strong> &nbsp;|&nbsp; {PROJECT_NAME}
            </div>
            <div>{badges_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, delta: str = None, delta_type: str = "neutral", accent: str = None):
    """
    Renders one gradient-accented KPI card via raw HTML/CSS (Streamlit has
    no native "colored top-border card" component, so this is built by
    hand rather than relying on st.metric, which can't be restyled this
    deeply without CSS injection like this).
    """
    accent_style = f'style="--kpi-accent: {accent};"' if accent else ""
    delta_html = f'<div class="kpi-delta {delta_type}">{delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="kpi-card fade-in" {accent_style}>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(text: str, level: str = "green") -> str:
    """Returns HTML for an inline status pill -- use inside st.markdown(..., unsafe_allow_html=True)."""
    return f'<span class="status-badge badge-{level}">{text}</span>'


def skeleton_row(n: int = 4):
    """Renders n shimmering skeleton placeholders in a row, for use while data loads."""
    cols = st.columns(n)
    for c in cols:
        with c:
            st.markdown('<div class="skeleton"></div>', unsafe_allow_html=True)

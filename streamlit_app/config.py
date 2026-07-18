"""
Central configuration for the Customer Subscription & Churn Intelligence
Platform Streamlit application.

Every file path and constant used across the app is defined once here,
so nothing is hardcoded separately in each page.

Author: Md Imamuddin
"""

import os

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_ROOT, "data")
ASSETS_DIR = os.path.join(APP_ROOT, "assets")

PROCESSED_DATA_PATH = os.path.join(DATA_DIR, "customer_churn_processed.csv")
ML_PREDICTIONS_PATH = os.path.join(DATA_DIR, "ml_predictions.csv")

LOG_DIR = os.path.join(APP_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "streamlit_app.log")

# ---------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------
APP_TITLE = "Customer Subscription & Churn Intelligence Platform"
APP_SUBTITLE = "Real data. Real models. Real business impact."
APP_ICON = "📊"

AUTHOR_NAME = "Md Imamuddin"
GITHUB_URL = 'https://github.com/Mdimam0786'
LINKEDIN_URL = " https://www.linkedin.com/in/md-imamuddin-5457391a9/"
RESUME_PATH = os.path.join(ASSETS_DIR, "resume.pdf")

# ---------------------------------------------------------------------
# Sidebar navigation — one place lists every page in the app
# ---------------------------------------------------------------------
NAV_SECTIONS = {
    "Overview": ["Home"],
    "Analytics": ["Exploratory Data Analysis", "Statistics", "SQL Insights"],
    "Explore": ["Customer Search", "Segment Search", "Geography Search", "Plan & Contract Search"],
    "Machine Learning": ["Churn & LTV Prediction", "Model Explainability (SHAP)"],
    "Project": ["Architecture", "Documentation", "About"],
}

# ---------------------------------------------------------------------
# Fallback KPI values, shown only for an instant before the real data
# finishes loading. Every page always computes and displays the real,
# live numbers right after.
# ---------------------------------------------------------------------
FALLBACK_TOTAL_CUSTOMERS = 7043
FALLBACK_CHURN_RATE_PCT = 26.54

# ---------------------------------------------------------------------
# Theme colors (matches the Power BI report's color palette)
# ---------------------------------------------------------------------
COLOR_PRIMARY = "#1F4E79"
COLOR_DANGER = "#D62728"
COLOR_SUCCESS = "#2CA02C"
COLOR_WARNING = "#FF7F0E"
COLOR_PURPLE = "#9467BD"

# ---------------------------------------------------------------------
# Footer (shown on every page)
# ---------------------------------------------------------------------
PROJECT_NAME = "Customer Subscription & Churn Intelligence Platform"
TECH_STACK = [
    "Python", "Pandas", "NumPy", "SciPy", "scikit-learn",
    "Streamlit", "Plotly", "SQL (PostgreSQL / SQLite)", "Power BI",
]

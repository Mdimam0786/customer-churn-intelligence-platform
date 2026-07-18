"""
Churn & LTV Prediction page.

Trains the REAL Phase 7 models (Gradient Boosting for churn, Random
Forest for CLTV) live against the real dataset, cached via
st.cache_resource so training happens once per session (~4 seconds
total, verified before building this page) rather than on every
prediction. A visitor fills out a hypothetical customer profile via a
form and gets a live churn probability + CLTV estimate -- the same
models, same features, same exclusion of IBM's own churn_score/cltv
fields from the churn model's inputs, exactly as documented in the
Phase 7 ML report.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING, COLOR_PRIMARY
from utils.data_loader import load_customer_data
from utils.logger import get_logger
from utils.theme import plotly_gauge_colors

logger = get_logger(__name__)

CHURN_NUMERIC = ["tenure_months", "monthly_charges", "total_charges", "addon_service_count"]
CHURN_CATEGORICAL = [
    "contract_type", "internet_service", "payment_method", "gender",
    "senior_citizen", "has_partner", "has_dependents", "paperless_billing",
    "multiple_lines", "online_security", "online_backup", "device_protection",
    "tech_support", "streaming_tv", "streaming_movies",
]
LTV_NUMERIC = ["tenure_months", "monthly_charges", "total_charges", "addon_service_count"]
LTV_CATEGORICAL = ["contract_type", "internet_service", "payment_method", "senior_citizen", "has_dependents"]

COST_OPTIMIZED_THRESHOLD = 0.10  # from the real Phase 7 business cost analysis


@st.cache_resource(show_spinner="Training the real Phase 7 churn model (one-time, ~2 seconds)...")
def train_churn_model(_df_len: int, df: pd.DataFrame) -> Pipeline:
    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), CHURN_NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), CHURN_CATEGORICAL),
    ])
    pipe = Pipeline([
        ("prep", preprocessor),
        ("clf", GradientBoostingClassifier(n_estimators=200, max_depth=2, learning_rate=0.05, random_state=42)),
    ])
    pipe.fit(df[CHURN_NUMERIC + CHURN_CATEGORICAL], df["churn_flag"])
    return pipe


@st.cache_resource(show_spinner="Training the real Phase 7 CLTV model (one-time, ~2 seconds)...")
def train_ltv_model(_df_len: int, df: pd.DataFrame) -> Pipeline:
    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), LTV_NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), LTV_CATEGORICAL),
    ])
    pipe = Pipeline([
        ("prep", preprocessor),
        ("reg", RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)),
    ])
    pipe.fit(df[LTV_NUMERIC + LTV_CATEGORICAL], df["cltv"])
    return pipe


def _gauge_chart(probability: float) -> go.Figure:
    color = COLOR_DANGER if probability >= 0.35 else COLOR_WARNING if probability >= 0.20 else COLOR_SUCCESS
    gauge_colors = plotly_gauge_colors()
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability * 100,
        number={"suffix": "%", "font": {"color": gauge_colors["threshold_line"]}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": gauge_colors["axis_color"]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 20], "color": gauge_colors["step_low"]},
                {"range": [20, 35], "color": gauge_colors["step_mid"]},
                {"range": [35, 100], "color": gauge_colors["step_high"]},
            ],
            "threshold": {
                "line": {"color": gauge_colors["threshold_line"], "width": 3},
                "thickness": 0.8,
                "value": COST_OPTIMIZED_THRESHOLD * 100,
            },
        },
    ))
    fig.update_layout(
        height=280,
        margin=dict(t=30, b=10, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": gauge_colors["threshold_line"]},
    )
    return fig


def render():
    st.title("🤖 Churn & LTV Prediction")
    st.caption(
        "Trains the real Phase 7 models live against the real dataset. Enter a hypothetical "
        "customer profile below and get a genuine model prediction — not a lookup table."
    )

    df = load_customer_data()
    churn_model = train_churn_model(len(df), df)
    ltv_model = train_ltv_model(len(df), df)

    st.info(
        "ℹ️ Per the Phase 7 design decision, IBM's own `churn_score` and `cltv` fields are "
        "excluded from these models' own inputs — they're trained only on independently "
        "observable business fields, so they generalize to a brand-new customer who won't "
        "have a vendor-assigned score yet."
    )

    st.markdown("### Enter a Hypothetical Customer Profile")

    with st.form("prediction_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            tenure_months = st.slider("Tenure (months)", 0, 72, 6)
            monthly_charges = st.slider("Monthly Charges ($)", 18.0, 120.0, 75.0)
            contract_type = st.selectbox("Contract Type", ["Month-to-month", "One year", "Two year"])
            internet_service = st.selectbox("Internet Service", ["Fiber optic", "DSL", "No"])
        with c2:
            payment_method = st.selectbox("Payment Method", [
                "Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)",
            ])
            gender = st.selectbox("Gender", ["Female", "Male"])
            senior_citizen = st.selectbox("Senior Citizen", ["No", "Yes"])
            has_partner = st.selectbox("Has Partner", ["No", "Yes"])
        with c3:
            has_dependents = st.selectbox("Has Dependents", ["No", "Yes"])
            paperless_billing = st.selectbox("Paperless Billing", ["Yes", "No"])
            multiple_lines = st.selectbox("Multiple Lines", ["No", "Yes", "No phone service"])

        st.markdown("**Add-on Services**")
        addon_cols = st.columns(6)
        addon_labels = ["online_security", "online_backup", "device_protection", "tech_support", "streaming_tv", "streaming_movies"]
        addon_values = {}
        internet_dependent_options = ["No", "Yes"] if internet_service != "No" else ["No internet service"]
        for i, svc in enumerate(addon_labels):
            with addon_cols[i]:
                addon_values[svc] = st.selectbox(svc.replace("_", " ").title(), internet_dependent_options, key=f"pred_{svc}")

        submitted = st.form_submit_button("🔮 Predict", type="primary", use_container_width=True)

    if submitted:
        addon_count = sum(1 for v in addon_values.values() if v == "Yes")
        total_charges_estimate = monthly_charges * max(tenure_months, 1)

        input_row = {
            "tenure_months": tenure_months, "monthly_charges": monthly_charges,
            "total_charges": total_charges_estimate, "addon_service_count": addon_count,
            "contract_type": contract_type, "internet_service": internet_service,
            "payment_method": payment_method, "gender": gender, "senior_citizen": senior_citizen,
            "has_partner": has_partner, "has_dependents": has_dependents,
            "paperless_billing": paperless_billing, "multiple_lines": multiple_lines,
            **addon_values,
        }
        input_df = pd.DataFrame([input_row])

        try:
            churn_proba = churn_model.predict_proba(input_df[CHURN_NUMERIC + CHURN_CATEGORICAL])[0, 1]
            predicted_ltv = ltv_model.predict(input_df[LTV_NUMERIC + LTV_CATEGORICAL])[0]

            st.markdown("---")
            st.markdown("### Prediction Results")

            col_gauge, col_metrics = st.columns([1, 1])
            with col_gauge:
                st.plotly_chart(_gauge_chart(churn_proba), use_container_width=True)
                risk_tier = "High Risk" if churn_proba >= 0.35 else "Moderate Risk" if churn_proba >= 0.20 else "Low Risk"
                risk_color = COLOR_DANGER if churn_proba >= 0.35 else COLOR_WARNING if churn_proba >= 0.20 else COLOR_SUCCESS
                st.markdown(
                    f'<div style="text-align:center;"><span style="background:{risk_color}22; color:{risk_color}; '
                    f'padding:0.3rem 1rem; border-radius:999px; font-weight:700;">{risk_tier}</span></div>',
                    unsafe_allow_html=True,
                )

            with col_metrics:
                st.metric("Predicted Churn Probability", f"{churn_proba*100:.1f}%")
                st.metric("Predicted CLTV", f"${predicted_ltv:,.0f}")
                above_threshold = churn_proba >= COST_OPTIMIZED_THRESHOLD
                st.metric(
                    "Recommended Action",
                    "🚨 Flag for outreach" if above_threshold else "✅ No action needed",
                )
                st.caption(
                    f"Using the Phase 7 business cost-optimized threshold (0.10, not the default 0.5) — "
                    f"this threshold assumes missing a real churner costs far more than a wasted retention offer."
                )

            with st.expander("View the exact feature values sent to the model"):
                st.dataframe(input_df.T.rename(columns={0: "Value"}), use_container_width=True)

            logger.info(f"Prediction made: churn_proba={churn_proba:.4f}, predicted_ltv={predicted_ltv:.2f}")

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            st.error(f"Prediction failed: {e}")

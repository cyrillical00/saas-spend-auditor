import streamlit as st
import pandas as pd
from sample_data import SAMPLE_VENDORS
from audit import categorize_vendors
from tabs import spend, security, waste, summary
from rate_limiter import get_client_ip, check_limit, record_run

st.set_page_config(
    page_title="SaaS Spend Auditor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #0F172A;
    color: #E2E8F0;
  }
  .stApp { background: #0F172A; }

  .app-header {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    border-bottom: 1px solid #334155;
    padding: 28px 0 20px 0;
    margin-bottom: 24px;
  }

  .stTabs [data-baseweb="tab-list"] {
    background: #1E293B;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
  }
  .stTabs [data-baseweb="tab"] {
    color: #64748B;
    font-size: 13px;
    font-weight: 500;
    border-radius: 6px;
    padding: 8px 20px;
  }
  .stTabs [aria-selected="true"] {
    background: #3B82F6 !important;
    color: white !important;
  }

  [data-testid="metric-container"] {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 16px;
  }

  .stButton > button, [data-testid="baseButton-primary"] {
    background: #3B82F6;
    color: white;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    border: none;
    border-radius: 6px;
  }
  .stDownloadButton > button {
    background: #1E293B;
    color: #94A3B8;
    border: 1px solid #334155;
    font-family: 'Inter', sans-serif;
  }

  hr { border-color: #1E293B; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
  <span style="font-size:10px;color:#3B82F6;letter-spacing:0.2em;text-transform:uppercase;">
    IT Operations · Portfolio Intelligence
  </span>
  <h1 style="font-size:32px;font-weight:700;color:#F1F5F9;margin:8px 0 4px;">
    SaaS Spend Auditor
  </h1>
  <p style="color:#64748B;font-size:13px;margin:0;">
    Analyze spend, security posture, and waste across your SaaS portfolio.
  </p>
</div>
""", unsafe_allow_html=True)

input_mode = st.radio(
    "Data source",
    ["Sample Data (50 vendors)", "Upload CSV"],
    horizontal=True,
    label_visibility="collapsed",
)

vendors = []

if input_mode == "Sample Data (50 vendors)":
    st.info(f"📋 **{len(SAMPLE_VENDORS)} vendors loaded** — realistic enterprise SaaS stack with pre-built waste, duplicate, and security findings.")
    vendors = SAMPLE_VENDORS

elif input_mode == "Upload CSV":
    st.markdown("""
    **Required columns:** `vendor`, `department`, `annual_cost`, `seat_count`, `seats_used`,
    `contract_type`, `renewal_date`, `sso_enabled`, `saml_enabled`, `scim_enabled`,
    `mfa_enforced`, `soc2_type2`, `soc2_type1`, `data_classification`, `owner_email`, `notes`

    Boolean fields: use `True`/`False`
    """)
    uploaded = st.file_uploader("Upload vendor CSV", type=["csv"])
    if uploaded:
        df_up = pd.read_csv(uploaded)
        bool_cols = ["sso_enabled", "saml_enabled", "scim_enabled", "mfa_enforced", "soc2_type2", "soc2_type1"]
        for col in bool_cols:
            if col in df_up.columns:
                df_up[col] = df_up[col].astype(str).str.lower().map({"true": True, "false": False, "1": True, "0": False})
        vendors = df_up.to_dict(orient="records")
        st.success(f"✓ {len(vendors)} vendors loaded")

client_ip = get_client_ip(dict(st.context.headers))
allowed, remaining = check_limit(client_ip)

run_col, info_col = st.columns([1, 3])
with run_col:
    run_clicked = st.button(
        f"Run Audit ({len(vendors)} vendors)",
        disabled=len(vendors) == 0 or not allowed,
        use_container_width=True,
    )
with info_col:
    if not allowed:
        st.error("Daily limit reached (5 audits/day). Come back tomorrow.")
    else:
        st.caption(f"{remaining} audit{'s' if remaining != 1 else ''} remaining today")

if run_clicked and vendors and allowed:
    with st.spinner("Categorizing vendors with Claude..."):
        try:
            categorized = categorize_vendors(vendors)
            df = pd.DataFrame(vendors)
            cat_map = {c["vendor"]: c for c in categorized}
            df["category"] = df["vendor"].apply(lambda v: cat_map.get(v, {}).get("category", "Uncategorized"))
            st.session_state["df"] = df
            st.session_state["categorized"] = categorized
            record_run(client_ip)
            st.success(f"✓ Audit complete — {len(vendors)} vendors analyzed")
        except Exception as e:
            st.error(f"Audit failed: {e}")

if "df" in st.session_state:
    df = st.session_state["df"]
    categorized = st.session_state.get("categorized", [])

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Spend Dashboard",
        "🔒 Security Audit",
        "⚠️ Waste Report",
        "📋 Executive Summary",
    ])

    with tab1:
        spend.render(df)
    with tab2:
        security.render(df)
    with tab3:
        waste.render(df, categorized)
    with tab4:
        summary.render(df, categorized)

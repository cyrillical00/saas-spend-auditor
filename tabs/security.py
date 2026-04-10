import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def render(df: pd.DataFrame):
    total = len(df)

    sso_pct = df["sso_enabled"].sum() / total * 100
    saml_pct = df["saml_enabled"].sum() / total * 100
    scim_pct = df["scim_enabled"].sum() / total * 100
    soc2_pct = df["soc2_type2"].sum() / total * 100
    mfa_pct = df["mfa_enforced"].sum() / total * 100

    st.subheader("Security Coverage")
    cols = st.columns(5)
    metrics = [
        ("SSO", sso_pct), ("SAML", saml_pct), ("SCIM", scim_pct),
        ("SOC2 T2", soc2_pct), ("MFA", mfa_pct),
    ]
    for col, (label, pct) in zip(cols, metrics):
        color = "#22C55E" if pct >= 80 else "#F59E0B" if pct >= 60 else "#EF4444"
        with col:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct,
                number={"suffix": "%", "font": {"color": "#F1F5F9", "size": 20}},
                title={"text": label, "font": {"color": "#94A3B8", "size": 12}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#475569"},
                    "bar": {"color": color},
                    "bgcolor": "#1E293B",
                    "bordercolor": "#334155",
                    "steps": [{"range": [0, 100], "color": "#0F172A"}],
                    "threshold": {"line": {"color": "#60A5FA", "width": 2}, "value": 80},
                },
            ))
            fig.update_layout(
                paper_bgcolor="#0A0A0F", font_color="#94A3B8",
                height=180, margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("High-Risk Vendors")
    high_risk = df[
        (df["data_classification"] == "High") &
        ((~df["sso_enabled"]) | (~df["soc2_type2"]) | (~df["mfa_enforced"]))
    ].copy()

    if not high_risk.empty:
        for _, row in high_risk.iterrows():
            gaps = []
            if not row["sso_enabled"]: gaps.append("No SSO")
            if not row["soc2_type2"]: gaps.append("No SOC2 T2")
            if not row["mfa_enforced"]: gaps.append("No MFA")
            gap_str = " · ".join(gaps)
            st.error(f"**{row['vendor']}** ({row['department']}) — High data classification — {gap_str}")
    else:
        st.success("No high-risk vendors detected.")

    st.divider()

    st.subheader("Vendor Security Posture")

    def bool_icon(val):
        return "✅" if val else "❌"

    display = df[["vendor", "department", "data_classification",
                  "sso_enabled", "saml_enabled", "scim_enabled",
                  "mfa_enforced", "soc2_type2"]].copy()
    for col in ["sso_enabled", "saml_enabled", "scim_enabled", "mfa_enforced", "soc2_type2"]:
        display[col] = display[col].apply(bool_icon)
    display.columns = ["Vendor", "Dept", "Data Class", "SSO", "SAML", "SCIM", "MFA", "SOC2 T2"]

    sel_class = st.multiselect("Filter by classification", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
    display = display[display["Data Class"].isin(sel_class)]
    st.dataframe(display, use_container_width=True, hide_index=True)

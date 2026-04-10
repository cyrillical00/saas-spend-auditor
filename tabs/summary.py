import streamlit as st
import pandas as pd
from audit import generate_executive_summary


def render(df: pd.DataFrame, categorized: list[dict]):
    st.subheader("Executive Summary")
    st.caption("Claude generates a boardroom-ready audit narrative from the full dataset.")

    if st.button("Generate Executive Summary", type="primary"):
        with st.spinner("Generating narrative..."):
            df_copy = df.copy()
            df_copy["utilization_pct"] = (df_copy["seats_used"] / df_copy["seat_count"].replace(0, 1) * 100).round(1)

            audit_data = {
                "total_vendors": len(df),
                "total_annual_spend": int(df["annual_cost"].sum()),
                "avg_utilization_pct": round(df_copy["utilization_pct"].mean(), 1),
                "low_utilization_vendors": df_copy[df_copy["utilization_pct"] < 60]["vendor"].tolist(),
                "duplicate_flags": [
                    {"vendor": c["vendor"], "duplicate_of": c["duplicate_of"], "note": c.get("consolidation_note")}
                    for c in categorized if c.get("duplicate_risk") == "High"
                ] if categorized else [],
                "sso_coverage_pct": round(df["sso_enabled"].sum() / len(df) * 100, 1),
                "scim_coverage_pct": round(df["scim_enabled"].sum() / len(df) * 100, 1),
                "soc2_coverage_pct": round(df["soc2_type2"].sum() / len(df) * 100, 1),
                "high_risk_vendors": df[
                    (df["data_classification"] == "High") & (~df["sso_enabled"])
                ]["vendor"].tolist(),
                "renewals_60_days": df[
                    pd.to_datetime(df["renewal_date"]) <= pd.Timestamp.now() + pd.Timedelta(days=60)
                ][["vendor", "annual_cost", "renewal_date"]].to_dict(orient="records"),
                "top_5_vendors_by_spend": df.nlargest(5, "annual_cost")[["vendor", "annual_cost"]].to_dict(orient="records"),
            }

            summary = generate_executive_summary(audit_data)
            st.session_state["exec_summary"] = summary

    if "exec_summary" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["exec_summary"])
        st.markdown("---")
        st.download_button(
            "Download Summary (.txt)",
            data=st.session_state["exec_summary"],
            file_name="saas_audit_executive_summary.txt",
            mime="text/plain",
        )

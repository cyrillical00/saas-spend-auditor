import streamlit as st
import pandas as pd


def render(df: pd.DataFrame, categorized: list[dict]):
    df = df.copy()
    df["utilization_pct"] = (df["seats_used"] / df["seat_count"].replace(0, 1) * 100).round(1)

    cat_map = {c["vendor"]: c for c in categorized} if categorized else {}
    df["duplicate_risk"] = df["vendor"].apply(lambda v: cat_map.get(v, {}).get("duplicate_risk", "None"))
    df["duplicate_of"] = df["vendor"].apply(lambda v: cat_map.get(v, {}).get("duplicate_of", None))
    df["consolidation_note"] = df["vendor"].apply(lambda v: cat_map.get(v, {}).get("consolidation_note", None))

    unused_seat_waste = df[df["utilization_pct"] < 60].apply(
        lambda r: r["annual_cost"] * (1 - r["utilization_pct"] / 100), axis=1
    ).sum()
    duplicate_spend = df[df["duplicate_risk"] == "High"]["annual_cost"].sum()
    renewal_risk_spend = df[
        pd.to_datetime(df["renewal_date"]) <= pd.Timestamp.now() + pd.Timedelta(days=60)
    ]["annual_cost"].sum()
    total_waste_estimate = unused_seat_waste * 0.4 + duplicate_spend * 0.5

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, f"${total_waste_estimate:,.0f}", "Est. Recoverable Waste"),
        (c2, str(len(df[df["utilization_pct"] < 60])), "Low Utilization Vendors"),
        (c3, str(len(df[df["duplicate_risk"] == "High"])), "Duplicate Tool Flags"),
        (c4, str(len(df[pd.to_datetime(df["renewal_date"]) <= pd.Timestamp.now() + pd.Timedelta(days=60)])), "Renewals in 60 Days"),
    ]:
        with col:
            st.metric(label, val)

    st.divider()

    st.subheader("Low Utilization (<60%)")
    low_util = df[df["utilization_pct"] < 60].sort_values("annual_cost", ascending=False)
    if not low_util.empty:
        display = low_util[["vendor", "department", "annual_cost", "seat_count", "seats_used", "utilization_pct"]].copy()
        display["annual_cost"] = display["annual_cost"].apply(lambda x: f"${x:,.0f}")
        display["utilization_pct"] = display["utilization_pct"].astype(str) + "%"
        display.columns = ["Vendor", "Dept", "Annual Cost", "Seats", "Used", "Utilization"]
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.success("No low-utilization vendors.")

    st.divider()

    st.subheader("Duplicate Tool Detection")
    dups = df[df["duplicate_risk"].isin(["High", "Medium"])].sort_values("duplicate_risk")
    if not dups.empty:
        for _, row in dups.iterrows():
            badge = "🔴" if row["duplicate_risk"] == "High" else "🟡"
            note = row["consolidation_note"] or ""
            st.warning(f"{badge} **{row['vendor']}** (${row['annual_cost']:,.0f}/yr) — duplicates **{row['duplicate_of']}** — {note}")
    else:
        st.success("No duplicates flagged.")

    st.divider()

    st.subheader("Upcoming Renewals (60 days)")
    df["renewal_dt"] = pd.to_datetime(df["renewal_date"])
    upcoming = df[df["renewal_dt"] <= pd.Timestamp.now() + pd.Timedelta(days=60)].sort_values("renewal_dt")
    if not upcoming.empty:
        display = upcoming[["vendor", "department", "annual_cost", "renewal_date", "contract_type"]].copy()
        display["annual_cost"] = display["annual_cost"].apply(lambda x: f"${x:,.0f}")
        display.columns = ["Vendor", "Dept", "Annual Cost", "Renewal Date", "Contract"]
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.info("No renewals in the next 60 days.")

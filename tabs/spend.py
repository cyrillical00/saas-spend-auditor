import streamlit as st
import plotly.express as px
import pandas as pd


def render(df: pd.DataFrame):
    total_spend = df["annual_cost"].sum()
    vendor_count = len(df)
    avg_utilization = (df["seats_used"] / df["seat_count"].replace(0, 1)).mean() * 100
    monthly_equiv = total_spend / 12

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, f"${total_spend:,.0f}", "Total Annual Spend"),
        (c2, str(vendor_count), "Vendors"),
        (c3, f"{avg_utilization:.0f}%", "Avg Utilization"),
        (c4, f"${monthly_equiv:,.0f}", "Monthly Run Rate"),
    ]:
        with col:
            st.metric(label, val)

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Spend by Category")
        cat_spend = df.groupby("category")["annual_cost"].sum().sort_values(ascending=True)
        fig = px.bar(
            x=cat_spend.values, y=cat_spend.index, orientation="h",
            color=cat_spend.values,
            color_continuous_scale=["#1E3A5F", "#3B82F6", "#60A5FA"],
            labels={"x": "Annual Cost ($)", "y": ""},
        )
        fig.update_layout(
            plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
            font_color="#94A3B8", showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=0, b=0),
        )
        fig.update_xaxes(gridcolor="#1E293B", tickprefix="$", tickformat=",.0f")
        fig.update_yaxes(gridcolor="#1E293B")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Spend by Department")
        dept_spend = df.groupby("department")["annual_cost"].sum().sort_values(ascending=False)
        fig2 = px.pie(
            values=dept_spend.values, names=dept_spend.index,
            color_discrete_sequence=px.colors.sequential.Blues_r,
            hole=0.45,
        )
        fig2.update_layout(
            plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
            font_color="#94A3B8",
            legend=dict(font=dict(color="#94A3B8")),
            margin=dict(l=0, r=0, t=0, b=0),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Utilization vs. Cost")
    df_scatter = df.copy()
    df_scatter["utilization_pct"] = (df_scatter["seats_used"] / df_scatter["seat_count"].replace(0, 1) * 100).round(1)
    fig3 = px.scatter(
        df_scatter, x="utilization_pct", y="annual_cost",
        hover_name="vendor", color="category",
        size="annual_cost", size_max=40,
        labels={"utilization_pct": "Utilization (%)", "annual_cost": "Annual Cost ($)"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig3.add_vline(x=60, line_dash="dash", line_color="#EF4444", annotation_text="60% threshold")
    fig3.update_layout(
        plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
        font_color="#94A3B8",
        legend=dict(font=dict(color="#94A3B8")),
    )
    fig3.update_xaxes(gridcolor="#1E293B")
    fig3.update_yaxes(gridcolor="#1E293B", tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Top Vendors by Spend")
    top = df.nlargest(15, "annual_cost")[["vendor", "department", "annual_cost", "seat_count", "seats_used"]].copy()
    top["utilization"] = (top["seats_used"] / top["seat_count"].replace(0, 1) * 100).round(1).astype(str) + "%"
    top["annual_cost"] = top["annual_cost"].apply(lambda x: f"${x:,.0f}")
    top = top.drop(columns=["seat_count", "seats_used"])
    st.dataframe(top, use_container_width=True, hide_index=True)

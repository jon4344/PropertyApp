
import math
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Hitch Property Management Calculator", page_icon="🏠", layout="wide")
st.title("🏠 Hitch Property Management Calculator")
st.caption("Quick, flexible modelling for long-term (LTR) and short-term (STR) lets — with BTL SDLT estimate (England & NI).")

# ---------------------------- Helpers ----------------------------
def sdlt_btl_england(price: float) -> float:
    """
    SDLT for additional property (BTL) in England & NI (effective +5% surcharge on standard bands).
    Effective bands: 5% to £125k, 7% to £250k, 10% to £925k, 15% to £1.5m, 17% above.
    """
    bands = [(125000, 0.05), (250000, 0.07), (925000, 0.10), (1500000, 0.15), (float('inf'), 0.17)]
    tax = 0.0
    prev = 0.0
    for t, rate in bands:
        slice_amt = min(price, t) - prev
        if slice_amt > 0:
            tax += slice_amt * rate
            prev = t
        if price <= t:
            break
    return max(tax, 0.0)

def monthly_mortgage_payment(principal: float, annual_rate: float, years: int, interest_only: bool) -> float:
    r = annual_rate/100.0/12.0
    n = years*12
    if principal <= 0 or annual_rate < 0 or years <= 0:
        return 0.0
    if interest_only:
        return principal * r
    if r == 0:
        return principal / n
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

# ---------------------------- Sidebar ----------------------------
with st.sidebar:
    st.header("Purchase & Mortgage")
    price = st.number_input("Purchase price (£)", min_value=0.0, value=200000.0, step=1000.0, format="%.2f")
    deposit_pct = st.slider("Deposit (%)", 0.0, 100.0, 25.0, 1.0)
    deposit = price * deposit_pct / 100.0
    loan = max(price - deposit, 0.0)

    st.markdown("---")
    st.subheader("Mortgage")
    mtg_type = st.selectbox("Type", ["Repayment", "Interest-only"])
    rate = st.number_input("Interest rate (APR, %)", min_value=0.0, value=5.0, step=0.1, format="%.2f")
    term = st.number_input("Term (years)", min_value=1, value=25, step=1)
    monthly_payment = monthly_mortgage_payment(loan, rate, term, mtg_type == "Interest-only")

    st.markdown("---")
    st.subheader("Stamp Duty (BTL)")
    auto_sdlt = st.checkbox("Auto-calc SDLT (England/NI)", value=True)
    if auto_sdlt:
        sdlt = sdlt_btl_england(price)
        st.info(f"Calculated SDLT (BTL): **£{sdlt:,.0f}**")
    else:
        sdlt = st.number_input("Enter SDLT manually (£)", min_value=0.0, value=0.0, step=100.0)

    st.markdown("---")
    st.subheader("One-off purchase costs")
    legal = st.number_input("Legal & conveyancing (£)", min_value=0.0, value=1500.0, step=100.0)
    broker = st.number_input("Broker / arrangement fees (£)", min_value=0.0, value=500.0, step=50.0)
    survey = st.number_input("Survey & searches (£)", min_value=0.0, value=400.0, step=50.0)
    refurb = st.number_input("Refurb / furniture (£)", min_value=0.0, value=0.0, step=100.0)
    other_oa = st.number_input("Other one-off costs (£)", min_value=0.0, value=0.0, step=50.0)

    upfront_cash = deposit + sdlt + legal + broker + survey + refurb + other_oa
    st.success(f"**Upfront cash required:** £{upfront_cash:,.0f}")

# ---------------------------- Tabs ----------------------------
tab1, tab2, tab3 = st.tabs(["📄 Long-term let (LTR)", "🛏️ Short-term let (STR)", "📊 Summary & Chart"])

# ---------------------------- LTR ----------------------------
with tab1:
    st.subheader("Long-term rental inputs")
    colA, colB, colC = st.columns(3)
    with colA:
        monthly_rent = st.number_input("Monthly rent (£)", min_value=0.0, value=1000.0, step=25.0)
        voids_pct = st.slider("Voids (% of rent)", 0.0, 50.0, 5.0, 1.0)
        mgmt_pct_lt = st.slider("Management (% of rent)", 0.0, 25.0, 10.0, 0.5)
    with colB:
        maint_pct_lt = st.slider("Maintenance (% of rent)", 0.0, 25.0, 5.0, 0.5)
        service_chg = st.number_input("Service charge (annual, £)", min_value=0.0, value=0.0, step=50.0)
        ground_rent = st.number_input("Ground rent (annual, £)", min_value=0.0, value=0.0, step=25.0)
    with colC:
        insurance = st.number_input("Landlord insurance (annual, £)", min_value=0.0, value=250.0, step=25.0)
        letting_fees = st.number_input("Letting/refresh fees (annual, £)", min_value=0.0, value=0.0, step=50.0)
        other_mo = st.number_input("Other monthly costs (£)", min_value=0.0, value=0.0, step=25.0)

    # LTR calcs
    lt_revenue_mo = monthly_rent
    lt_revenue_yr = lt_revenue_mo * 12

    mgmt_mo = monthly_rent * mgmt_pct_lt / 100.0
    maint_mo = monthly_rent * maint_pct_lt / 100.0
    voids_mo = monthly_rent * voids_pct / 100.0
    fixed_mo = other_mo + (service_chg + ground_rent + insurance + letting_fees) / 12.0

    lt_opex_mo = mgmt_mo + maint_mo + voids_mo + fixed_mo
    lt_opex_yr = lt_opex_mo * 12
    lt_noi_mo = lt_revenue_mo - lt_opex_mo
    lt_noi_yr = lt_noi_mo * 12
    lt_mort_mo = monthly_payment
    lt_mort_yr = lt_mort_mo * 12
    lt_cash_mo = lt_noi_mo - lt_mort_mo
    lt_cash_yr = lt_cash_mo * 12
    lt_gross_yield = (lt_revenue_yr / price * 100.0) if price else 0.0
    lt_net_yield = (lt_noi_yr / price * 100.0) if price else 0.0
    lt_coc = (lt_cash_yr / upfront_cash * 100.0) if upfront_cash > 0 else 0.0

    # Display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Monthly revenue", f"£{lt_revenue_mo:,.0f}")
        st.metric("Monthly opex", f"£{lt_opex_mo:,.0f}")
        st.metric("Monthly mortgage", f"£{lt_mort_mo:,.0f}")
    with col2:
        st.metric("Monthly NOI", f"£{lt_noi_mo:,.0f}")
        st.metric("Monthly cashflow", f"£{lt_cash_mo:,.0f}")
        st.metric("Gross yield", f"{lt_gross_yield:,.2f}%")
    with col3:
        st.metric("Annual revenue", f"£{lt_revenue_yr:,.0f}")
        st.metric("Annual opex", f"£{lt_opex_yr:,.0f}")
        st.metric("Annual cashflow", f"£{lt_cash_yr:,.0f}")

    with st.expander("LTR breakdown (monthly & annual)"):
        lt_table = pd.DataFrame({
            "Metric": ["Revenue", "Operating costs", "NOI", "Mortgage", "Cashflow"],
            "Monthly (£)": [lt_revenue_mo, lt_opex_mo, lt_noi_mo, lt_mort_mo, lt_cash_mo],
            "Annual (£)": [lt_revenue_yr, lt_opex_yr, lt_noi_yr, lt_mort_yr, lt_cash_yr]
        })
        st.dataframe(lt_table, use_container_width=True)
        extra = pd.DataFrame({
            "Metric": ["Net yield (%)", "Cash-on-cash (%)"],
            "Value": [lt_net_yield, lt_coc]
        })
        st.dataframe(extra, use_container_width=True)

# ---------------------------- STR ----------------------------
with tab2:
    st.subheader("Short-term rental inputs")
    colA, colB, colC = st.columns(3)
    with colA:
        nightly = st.number_input("Nightly rate (£)", min_value=0.0, value=120.0, step=5.0)
        occupancy = st.slider("Occupancy (% of days in year)", 0.0, 100.0, 60.0, 1.0)
    with colB:
        avg_stay = st.radio("Average stay (nights)", [1, 2, 3, 4], index=1, horizontal=True)
        cost_per_clean = st.number_input("Cost per clean (incl. linen) (£)", min_value=0.0, value=60.0, step=5.0)
        mgmt_pct_str = st.slider("Management (% of revenue)", 0.0, 50.0, 15.0, 0.5)
    with colC:
        platform_pct = st.slider("Platform/OTA fee (% of revenue)", 0.0, 20.0, 3.0, 0.5)
        utilities_mo = st.number_input("Utilities (monthly, £)", min_value=0.0, value=250.0, step=10.0)
        rates_annual = st.number_input("Council tax / business rates (annual, £)", min_value=0.0, value=0.0, step=50.0)

    # STR core maths
    nights_year = 365 * (occupancy / 100.0)
    stays_year = nights_year / float(avg_stay)  # stays = nights / avg_stay
    cleaning_year = cost_per_clean * stays_year  # <-- Requested formula
    cleaning_mo = cleaning_year / 12.0

    revenue_year = nightly * nights_year
    mgmt_year = revenue_year * mgmt_pct_str / 100.0
    platform_year = revenue_year * platform_pct / 100.0
    fixed_year = utilities_mo * 12 + rates_annual

    opex_year = mgmt_year + platform_year + cleaning_year + fixed_year
    opex_mo = opex_year / 12.0

    noi_year = revenue_year - opex_year
    noi_mo = noi_year / 12.0

    mort_mo = monthly_payment
    mort_yr = mort_mo * 12.0

    cash_mo = noi_mo - mort_mo
    cash_yr = cash_mo * 12.0

    gross_yield_str = (revenue_year / price * 100.0) if price else 0.0
    net_yield_str = (noi_year / price * 100.0) if price else 0.0
    coc_str = (cash_yr / upfront_cash * 100.0) if upfront_cash > 0 else 0.0

    # Display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Monthly revenue", f"£{revenue_year/12:,.0f}")
        st.metric("Monthly opex", f"£{opex_mo:,.0f}")
        st.metric("Monthly mortgage", f"£{mort_mo:,.0f}")
    with col2:
        st.metric("Monthly NOI", f"£{noi_mo:,.0f}")
        st.metric("Monthly cashflow", f"£{cash_mo:,.0f}")
        st.metric("Gross yield", f"{gross_yield_str:,.2f}%")
    with col3:
        st.metric("Annual revenue", f"£{revenue_year:,.0f}")
        st.metric("Annual opex", f"£{opex_year:,.0f}")
        st.metric("Annual cashflow", f"£{cash_yr:,.0f}")

    st.caption(f"Cleaning cost = (365 × {occupancy:.0f}% ÷ {avg_stay}) × £{cost_per_clean} = £{cleaning_year:,.0f}/yr (≈ £{cleaning_mo:,.0f}/mo).")

    with st.expander("STR breakdown (monthly & annual)"):
        str_table = pd.DataFrame({
            "Metric": ["Revenue", "Operating costs", "NOI", "Mortgage", "Cashflow"],
            "Monthly (£)": [revenue_year/12, opex_mo, noi_mo, mort_mo, cash_mo],
            "Annual (£)": [revenue_year, opex_year, noi_year, mort_yr, cash_yr]
        })
        st.dataframe(str_table, use_container_width=True)
        extra = pd.DataFrame({
            "Metric": ["Net yield (%)", "Cash-on-cash (%)"],
            "Value": [net_yield_str, coc_str]
        })
        st.dataframe(extra, use_container_width=True)

# ---------------------------- Summary & Chart ----------------------------
with tab3:
    st.subheader("Summary")
    summary = pd.DataFrame({
        "Scenario": ["Long-term let", "Short-term let"],
        "Monthly cashflow (£)": [ ( (monthly_rent - (monthly_rent*mgmt_pct_lt/100.0 + monthly_rent*maint_pct_lt/100.0 + monthly_rent*voids_pct/100.0 + (service_chg+ground_rent+insurance+letting_fees)/12.0)) - monthly_payment ),
                                  cash_mo ],
        "Annual cashflow (£)": [ (( (monthly_rent - (monthly_rent*mgmt_pct_lt/100.0 + monthly_rent*maint_pct_lt/100.0 + monthly_rent*voids_pct/100.0 + (service_chg+ground_rent+insurance+letting_fees)/12.0)) - monthly_payment )*12),
                                 cash_yr ],
        "Cash-on-cash (%)": [
            ( (( (monthly_rent - (monthly_rent*mgmt_pct_lt/100.0 + monthly_rent*maint_pct_lt/100.0 + monthly_rent*voids_pct/100.0 + (service_chg+ground_rent+insurance+letting_fees)/12.0)) - monthly_payment )*12) / upfront_cash * 100.0 ) if upfront_cash>0 else 0.0,
            ( cash_yr / upfront_cash * 100.0 ) if upfront_cash>0 else 0.0
        ]
    })
    st.dataframe(summary, use_container_width=True)

    st.markdown("### Compare revenue, costs, and profit")
    show_annual = st.toggle("Show annual view", value=False)
    series = st.multiselect("Series", ["Revenue", "Costs", "Profit"], default=["Revenue", "Costs", "Profit"])

    # LTR monthly/annual
    ltr_rev_m = lt_revenue_mo
    ltr_costs_m = lt_opex_mo + lt_mort_mo
    ltr_profit_m = lt_cash_mo
    ltr_rev_y, ltr_costs_y, ltr_profit_y = lt_revenue_yr, lt_opex_yr+lt_mort_yr, lt_cash_yr

    # STR monthly/annual
    str_rev_m = revenue_year/12
    str_costs_m = opex_mo + mort_mo
    str_profit_m = cash_mo
    str_rev_y, str_costs_y, str_profit_y = revenue_year, opex_year+mort_yr, cash_yr

    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    if not show_annual:
        df = pd.DataFrame({
            "Month": months * 2,
            "Scenario": ["Long-term"]*12 + ["Short-term"]*12,
            "Revenue": [ltr_rev_m]*12 + [str_rev_m]*12,
            "Costs": [ltr_costs_m]*12 + [str_costs_m]*12,
            "Profit": [ltr_profit_m]*12 + [str_profit_m]*12
        })
        chart = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X('Month:N', sort=months),
            y=alt.Y(alt.repeat('column'), type='quantitative', title='£ per month'),
            color='Scenario:N'
        ).repeat(column=series).resolve_scale(y='independent')
        st.altair_chart(chart, use_container_width=True)
    else:
        df = pd.DataFrame({
            "Scenario": ["Long-term","Short-term"],
            "Revenue": [ltr_rev_y, str_rev_y],
            "Costs": [ltr_costs_y, str_costs_y],
            "Profit": [ltr_profit_y, str_profit_y]
        })
        chart = alt.Chart(df).transform_fold(
            series, as_=['Metric','Value']
        ).mark_bar().encode(
            x='Scenario:N', y='Value:Q', color='Metric:N'
        )
        st.altair_chart(chart, use_container_width=True)

st.markdown("---")
st.caption("NOTE: Cleaning cost = (365 × occupancy% ÷ average stay) × cost per clean. Example: 50% × 365 ÷ 2 × £60 = £5,475/yr (≈ £456/mo). If you expected £3,650/yr at 50%/£60/2 nights, that corresponds to an average stay of ~3 nights.")

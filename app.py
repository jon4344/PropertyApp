import math
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Hitch Property Management Calculator", page_icon="🏠", layout="wide")

st.title("🏠 Hitch Property Management Calculator")
st.caption("Quick, flexible modelling for long-term lets and short-term (Airbnb) lets — England & NI (SDLT)")

with st.expander("About & assumptions", expanded=False):
    st.markdown(
        """
- **SDLT**: Uses England & NI residential rates as of **1 April 2025**, with the **additional property surcharge at +5%** added to each band (buy-to-let/second home).
- **Mortgage**: Switch between **Repayment** and **Interest-only**.
- **Short-term lets**: Occupancy is % of **365 nights**. Cleaning cost is per **occupied night**.
- All values are in **GBP**. This is an estimate tool only — always confirm figures with your lender/conveyancer/accountant.
        """
    )

def sdlt_btl_england(price: float) -> float:
    """
    SDLT for additional property (BTL) in England & NI from 1 Apr 2025:
    Base bands: 0%, 2%, 5%, 10%, 12%
    BTL surcharge: +5% across all bands
    => Effective bands for additional property: 5%, 7%, 10%, 15%, 17%
    """
    bands = [
        (125000, 0.05),
        (250000, 0.07),
        (925000, 0.10),
        (1500000, 0.15),
        (float('inf'), 0.17)
    ]
    tax = 0.0
    prev = 0.0
    for threshold, rate in bands:
        slice_amount = min(price, threshold) - prev
        if slice_amount > 0:
            tax += slice_amount * rate
            prev = threshold
        if price <= threshold:
            break
    return max(tax, 0.0)

def monthly_mortgage_payment(principal: float, annual_rate: float, years: int, interest_only: bool) -> float:
    r = annual_rate / 100.0 / 12.0
    n = years * 12
    if principal <= 0 or annual_rate < 0 or years <= 0:
        return 0.0
    if interest_only:
        return principal * r
    if r == 0:
        return principal / n
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

with st.sidebar:
    st.header("Purchase & Mortgage")
    price = st.number_input("Purchase price (£)", min_value=0.0, value=100000.0, step=1000.0, format="%.2f")
    deposit_pct = st.slider("Deposit (%)", min_value=0.0, max_value=100.0, value=25.0, step=1.0)
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
        sdlt = st.number_input("Enter SDLT manually (£)", min_value=0.0, value=0.0, step=500.0)

    st.markdown("---")
    st.subheader("One-off purchase costs")
    legal = st.number_input("Legal & conveyancing (£)", min_value=0.0, value=1500.0, step=100.0)
    broker = st.number_input("Broker / arrangement fees (£)", min_value=0.0, value=500.0, step=50.0)
    survey = st.number_input("Survey & searches (£)", min_value=0.0, value=400.0, step=50.0)
    refurb = st.number_input("Refurb / furniture (£)", min_value=0.0, value=0.0, step=100.0)
    other_oa = st.number_input("Other one-off costs (£)", min_value=0.0, value=0.0, step=50.0)

    upfront_cash = deposit + sdlt + legal + broker + survey + refurb + other_oa
    st.success(f"**Upfront cash required:** £{upfront_cash:,.0f}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 Long-term let", "🛏️ Short-term (STR)", "📊 Summary", "📈 ROI Metrics", "🎯 Scenarios"])

with tab1:
    st.subheader("Long-term rental inputs")
    colA, colB, colC = st.columns(3)
    with colA:
        monthly_rent = st.number_input("Monthly rent (£)", min_value=0.0, value=800.0, step=25.0)
        voids_pct = st.slider("Voids (% of rent)", 0.0, 50.0, 5.0, 1.0)
        mgmt_pct_lt = st.slider("Management (% of rent)", 0.0, 25.0, 10.0, 0.5)
    with colB:
        maint_pct_lt = st.slider("Maintenance (% of rent)", 0.0, 25.0, 5.0, 0.5)
        service_chg = st.number_input("Service charge (annual, £)", min_value=0.0, value=0.0, step=50.0)
        ground_rent = st.number_input("Ground rent (annual, £)", min_value=0.0, value=0.0, step=25.0)
    with colC:
        insurance = st.number_input("Landlord insurance (annual, £)", min_value=0.0, value=250.0, step=25.0)
        other_mo = st.number_input("Other monthly costs (£)", min_value=0.0, value=0.0, step=25.0)
        letting_fees = st.number_input("Letting/refresh fees (annual, £)", min_value=0.0, value=0.0, step=50.0)

    # Calculations
    gross_month = monthly_rent
    mgmt_mo = monthly_rent * mgmt_pct_lt / 100.0
    maint_mo = monthly_rent * maint_pct_lt / 100.0
    voids_mo = monthly_rent * voids_pct / 100.0

    fixed_mo = other_mo + (service_chg + ground_rent + insurance + letting_fees) / 12.0
    non_mortgage_costs_mo = mgmt_mo + maint_mo + voids_mo + fixed_mo

    net_operating_income_mo = gross_month - non_mortgage_costs_mo
    cashflow_mo_lt = net_operating_income_mo - monthly_payment

    annual_rent = monthly_rent * 12
    gross_yield = (annual_rent / price * 100.0) if price else 0.0
    annual_net = cashflow_mo_lt * 12
    coc_return = (annual_net / upfront_cash * 100.0) if upfront_cash > 0 else 0.0

    st.markdown("### Results (Long-term)")
    # Unified monthly/annual metrics
    lt_revenue_mo = monthly_rent
    lt_revenue_yr = lt_revenue_mo * 12
    lt_opex_mo = mgmt_mo + maint_mo + voids_mo + fixed_mo
    lt_opex_yr = lt_opex_mo * 12
    lt_noi_mo = lt_revenue_mo - lt_opex_mo
    lt_noi_yr = lt_noi_mo * 12
    lt_mort_mo = monthly_payment
    lt_mort_yr = lt_mort_mo * 12
    lt_cash_mo = lt_noi_mo - lt_mort_mo
    lt_cash_yr = lt_cash_mo * 12
    lt_net_yield = (lt_noi_yr / price * 100.0) if price else 0.0
    lt_coc = (lt_cash_yr / upfront_cash * 100.0) if upfront_cash>0 else 0.0

    colm1, colm2, colm3 = st.columns(3)
    with colm1:
        st.metric("Monthly mortgage", f"£{lt_mort_mo:,.0f}")
        st.metric("Monthly revenue", f"£{lt_revenue_mo:,.0f}")
        st.metric("Monthly opex", f"£{lt_opex_mo:,.0f}")
    with colm2:
        st.metric("Monthly NOI", f"£{lt_noi_mo:,.0f}")
        st.metric("Monthly cashflow", f"£{lt_cash_mo:,.0f}")
        st.metric("Gross yield", f"{gross_yield:,.2f}%")
    with colm3:
        st.metric("Annual revenue", f"£{lt_revenue_yr:,.0f}")
        st.metric("Annual opex", f"£{lt_opex_yr:,.0f}")
        st.metric("Annual cashflow", f"£{lt_cash_yr:,.0f}")

    with st.expander("Full breakdown (monthly & annual)"):
        lt_table = pd.DataFrame({
            "Metric": ["Revenue", "Operating costs", "NOI", "Mortgage", "Cashflow"],
            "Monthly (£)": [lt_revenue_mo, lt_opex_mo, lt_noi_mo, lt_mort_mo, lt_cash_mo],
            "Annual (£)": [lt_revenue_yr, lt_opex_yr, lt_noi_yr, lt_mort_yr, lt_cash_yr]
        })
        st.dataframe(lt_table, use_container_width=True)
        extra = pd.DataFrame({
            "Metric": ["Gross yield (%)", "Net yield (%)", "Cash-on-cash (%)"],
            "Value": [gross_yield, lt_net_yield, lt_coc]
        })
        st.dataframe(extra, use_container_width=True)

with tab2:
    st.subheader("Short-term rental inputs")
    colA, colB, colC = st.columns(3)
    with colA:
        nightly = st.number_input("Nightly rate (£)", min_value=0.0, value=100.0, step=5.0)
        occupancy = st.slider("Occupancy (% of days in year)", 0.0, 100.0, 60.0, 1.0)
    with colB:
        cleaning_per_night = st.number_input("Cleaning cost per occupied night (£)", min_value=0.0, value=10.0, step=1.0)
        mgmt_pct_str = st.slider("Management (% of revenue)", 0.0, 50.0, 15.0, 0.5)
        platform_pct = st.slider("Platform/OTA fee (% of revenue)", 0.0, 20.0, 3.0, 0.5)
    with colC:
        utilities_mo = st.number_input("Utilities (monthly, £)", min_value=0.0, value=250.0, step=10.0)
        linen_mo = st.number_input("Linen/laundry (monthly, £)", min_value=0.0, value=60.0, step=5.0)
        rates_annual = st.number_input("Council tax / business rates (annual, £)", min_value=0.0, value=0.0, step=50.0)

    nights_year = 365 * (occupancy / 100.0)
    revenue_year = nightly * nights_year
    mgmt_year = revenue_year * mgmt_pct_str / 100.0
    platform_year = revenue_year * platform_pct / 100.0
    cleaning_year = cleaning_per_night * nights_year
    fixed_year = utilities_mo * 12 + linen_mo * 12 + rates_annual

    opex_year = mgmt_year + platform_year + cleaning_year + fixed_year
    noi_year = revenue_year - opex_year
    cashflow_year_str = noi_year - (monthly_payment * 12)
    cashflow_mo_str = cashflow_year_str / 12.0
    coc_return_str = (cashflow_year_str / upfront_cash * 100.0) if upfront_cash > 0 else 0.0

    st.markdown("### Results (Short-term)")
    # Unified monthly/annual metrics
    str_revenue_yr = revenue_year
    str_revenue_mo = str_revenue_yr / 12.0
    str_opex_yr = opex_year
    str_opex_mo = str_opex_yr / 12.0
    str_noi_yr = str_revenue_yr - str_opex_yr
    str_noi_mo = str_noi_yr / 12.0
    str_mort_mo = monthly_payment
    str_mort_yr = str_mort_mo * 12.0
    str_cash_mo = str_noi_mo - str_mort_mo
    str_cash_yr = str_cash_mo * 12.0
    str_gross_yield = (str_revenue_yr / price * 100.0) if price else 0.0
    str_net_yield = (str_noi_yr / price * 100.0) if price else 0.0
    str_coc = (str_cash_yr / upfront_cash * 100.0) if upfront_cash>0 else 0.0

    colm1, colm2, colm3 = st.columns(3)
    with colm1:
        st.metric("Monthly mortgage", f"£{str_mort_mo:,.0f}")
        st.metric("Monthly revenue", f"£{str_revenue_mo:,.0f}")
        st.metric("Monthly opex", f"£{str_opex_mo:,.0f}")
    with colm2:
        st.metric("Monthly NOI", f"£{str_noi_mo:,.0f}")
        st.metric("Monthly cashflow", f"£{str_cash_mo:,.0f}")
        st.metric("Gross yield", f"{str_gross_yield:,.2f}%")
    with colm3:
        st.metric("Annual revenue", f"£{str_revenue_yr:,.0f}")
        st.metric("Annual opex", f"£{str_opex_yr:,.0f}")
        st.metric("Annual cashflow", f"£{str_cash_yr:,.0f}")

    with st.expander("Full breakdown (monthly & annual)"):
        str_table = pd.DataFrame({
            "Metric": ["Revenue", "Operating costs", "NOI", "Mortgage", "Cashflow"],
            "Monthly (£)": [str_revenue_mo, str_opex_mo, str_noi_mo, str_mort_mo, str_cash_mo],
            "Annual (£)": [str_revenue_yr, str_opex_yr, str_noi_yr, str_mort_yr, str_cash_yr]
        })
        st.dataframe(str_table, use_container_width=True)
        extra = pd.DataFrame({
            "Metric": ["Gross yield (%)", "Net yield (%)", "Cash-on-cash (%)"],
            "Value": [str_gross_yield, str_net_yield, str_coc]
        })
        st.dataframe(extra, use_container_width=True)

with tab3:
    st.subheader("Deal summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Upfront cash required", f"£{upfront_cash:,.0f}")
    with col2:
        st.metric("Loan amount", f"£{loan:,.0f}")
    with col3:
        st.metric("Monthly mortgage", f"£{monthly_payment:,.0f}")

    # Recompute summary values
    monthly_rent_val = monthly_rent
    mgmt_mo_val = monthly_rent_val * mgmt_pct_lt / 100.0
    maint_mo_val = monthly_rent_val * maint_pct_lt / 100.0
    voids_mo_val = monthly_rent_val * voids_pct / 100.0
    fixed_mo_val = other_mo + (service_chg + ground_rent + insurance + letting_fees) / 12.0
    lt_cashflow = (monthly_rent_val - (mgmt_mo_val + maint_mo_val + voids_mo_val + fixed_mo_val)) - monthly_payment

    nights_year_sum = 365 * (occupancy / 100.0)
    revenue_year_sum = nightly * nights_year_sum
    mgmt_year_sum = revenue_year_sum * mgmt_pct_str / 100.0
    platform_year_sum = revenue_year_sum * platform_pct / 100.0
    cleaning_year_sum = cleaning_per_night * nights_year_sum
    fixed_year_sum = utilities_mo * 12 + linen_mo * 12 + rates_annual
    opex_year_sum = mgmt_year_sum + platform_year_sum + cleaning_year_sum + fixed_year_sum

    str_cashflow_year = revenue_year_sum - opex_year_sum - (monthly_payment * 12)
    str_cashflow_mo = str_cashflow_year / 12.0

    summary = pd.DataFrame({
        "Scenario": ["Long-term let", "Short-term let"],
        "Monthly cashflow (£)": [lt_cashflow, str_cashflow_mo],
        "Annual cashflow (£)": [lt_cashflow*12, str_cashflow_year],
        "Cash-on-cash (%)": [
            (lt_cashflow*12 / upfront_cash * 100.0) if upfront_cash>0 else 0.0,
            (str_cashflow_year / upfront_cash * 100.0) if upfront_cash>0 else 0.0
        ]
    })
    st.dataframe(summary, use_container_width=True)

    # Comparison chart
    st.markdown("### Compare revenue, costs, and profit")
    freq = st.toggle("Show **annual** instead of monthly", value=False)
    metrics_to_plot = st.multiselect("Select series", ["Revenue", "Costs", "Profit"], default=["Revenue", "Costs", "Profit"])

    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    lt_rev_m = lt_revenue_mo
    lt_costs_m = (mgmt_mo + maint_mo + voids_mo + fixed_mo) + monthly_payment
    lt_profit_m = lt_cash_mo

    str_rev_m = str_revenue_mo
    str_costs_m = (str_opex_mo) + monthly_payment
    str_profit_m = str_cash_mo

    if not freq:
        df_m = pd.DataFrame({
            "Month": months * 2,
            "Scenario": ["Long-term"]*12 + ["Short-term"]*12,
            "Revenue": [lt_rev_m]*12 + [str_rev_m]*12,
            "Costs": [lt_costs_m]*12 + [str_costs_m]*12,
            "Profit": [lt_profit_m]*12 + [str_profit_m]*12
        })
        base_ch = alt.Chart(df_m).mark_line(point=True).encode(
            x=alt.X('Month:N', sort=months),
            y=alt.Y(alt.repeat('column'), type='quantitative', title='£ per month'),
            color='Scenario:N'
        ).repeat(column=metrics_to_plot).resolve_scale(y='independent')
        st.altair_chart(base_ch, use_container_width=True)
    else:
        df_a = pd.DataFrame({
            "Scenario": ["Long-term", "Short-term"],
            "Revenue": [lt_revenue_yr, str_revenue_yr],
            "Costs": [lt_opex_yr + lt_mort_yr, str_opex_yr + str_mort_yr],
            "Profit": [lt_cash_yr, str_cash_yr]
        })
        base_ch = alt.Chart(df_a).transform_fold(
            metrics_to_plot, as_=['Metric','Value']
        ).mark_line(point=True).encode(
            x='Scenario:N',
            y=alt.Y('Value:Q', title='£ per year'),
            color='Metric:N'
        )
        st.altair_chart(base_ch, use_container_width=True)

with tab4:
    st.subheader("ROI Metrics")
    annual_net_lt = lt_cash_mo * 12
    dscr_lt = ( (lt_noi_mo) / monthly_payment ) if monthly_payment > 0 else float('inf')
    payback_lt = (upfront_cash / annual_net_lt) if annual_net_lt > 0 else float('inf')

    occ_var_cost_per_night = nightly * (1 - (mgmt_pct_str/100.0) - (platform_pct/100.0)) - cleaning_per_night
    annual_fixed_and_mort = (utilities_mo*12 + linen_mo*12 + rates_annual) + (monthly_payment*12)
    breakeven_occ = 0.0
    if occ_var_cost_per_night > 0:
        breakeven_occ = min(max(annual_fixed_and_mort / (occ_var_cost_per_night * 365.0), 0.0), 1.0)

    annual_net_str = str_cash_mo * 12
    dscr_str = ( (str_noi_yr) / (monthly_payment*12) ) if monthly_payment>0 else float('inf')
    payback_str = (upfront_cash / annual_net_str) if annual_net_str > 0 else float('inf')

    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Long-term let**")
        st.metric("DSCR (NOI / Debt Service)", f"{dscr_lt:,.2f}")
        st.metric("Annual net cashflow", f"£{annual_net_lt:,.0f}")
        st.metric("Payback (years)", "∞" if payback_lt == float('inf') else f"{payback_lt:,.1f}")
    with colB:
        st.markdown("**Short-term let**")
        st.metric("Breakeven occupancy", f"{breakeven_occ*100:,.1f}%")
        st.metric("DSCR (NOI / Debt Service)", f"{dscr_str:,.2f}")
        st.metric("Annual net cashflow", f"£{annual_net_str:,.0f}")
        st.metric("Payback (years)", "∞" if payback_str == float('inf') else f"{payback_str:,.1f}")

with tab5:
    st.subheader("Best, Base, Worst Scenarios")
    st.caption("Scenarios are computed from your current inputs. Adjust deltas below.")

    col1, col2 = st.columns(2)
    with col1:
        occ_delta = st.slider("STR occupancy delta (± % points)", 0, 30, 10, 1)
        rate_delta = st.slider("STR nightly rate delta (± %)", 0, 30, 10, 1)
    with col2:
        rent_delta = st.slider("LTR monthly rent delta (± %)", 0, 30, 10, 1)
        cost_delta = st.slider("LTR variable costs delta (± %)", 0, 30, 10, 1)

    base_lt_monthly = lt_cash_mo
    base_str_monthly = str_cash_mo

    def ltr_cashflow_with(rent_mult, cost_mult):
        rent = monthly_rent * rent_mult
        mgmt = rent * mgmt_pct_lt/100.0 * cost_mult
        maint = rent * maint_pct_lt/100.0 * cost_mult
        voids = rent * voids_pct/100.0 * cost_mult
        fixed = other_mo + (service_chg + ground_rent + insurance + letting_fees)/12.0
        noi = rent - (mgmt + maint + voids + fixed)
        return noi - monthly_payment

    lt_worst = ltr_cashflow_with(1 - rent_delta/100.0, 1 + cost_delta/100.0)
    lt_best  = ltr_cashflow_with(1 + rent_delta/100.0, 1 - cost_delta/100.0)

    def str_monthly_with(occ_pp_delta, rate_pct_delta):
        occ = min(max(occupancy + occ_pp_delta, 0.0), 100.0)
        nights = 365 * (occ/100.0)
        rev = nightly * (1 + rate_pct_delta/100.0) * nights
        mgmt_s = rev * mgmt_pct_str/100.0
        plat_s = rev * platform_pct/100.0
        clean_s = cleaning_per_night * nights
        fixed_s = utilities_mo*12 + linen_mo*12 + rates_annual
        noi_s = rev - (mgmt_s + plat_s + clean_s + fixed_s)
        cf_year = noi_s - (monthly_payment*12)
        return cf_year / 12.0

    str_worst = str_monthly_with(-occ_delta, -rate_delta)
    str_best  = str_monthly_with(+occ_delta, +rate_delta)

    scen = pd.DataFrame({
        "Scenario": ["Worst", "Base", "Best"],
        "LTR cashflow (£/mo)": [lt_worst, base_lt_monthly, lt_best],
        "STR cashflow (£/mo)": [str_worst, base_str_monthly, str_best]
    })
    st.dataframe(scen, use_container_width=True)

st.markdown("---")
st.caption("Built for quick screening. Always verify SDLT, lender criteria, and local regulations.")


import math
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Property Deal Calculator", page_icon="🏠", layout="wide")

st.title("🏠 Property Deal Calculator")
st.caption("Quick, flexible modelling for long-term lets and short-term (Airbnb) lets — England & NI (SDLT)")

with st.expander("About & assumptions", expanded=False):
    st.markdown(
        """
- **SDLT**: Uses England & NI residential rates as of **1 April 2025**, with the **additional property surcharge at +5%** added to each band (buy-to-let/second home).
- **Mortgage**: You can switch between **Repayment** and **Interest-only**.
- **Short-term lets**: Cleaning cost is per **stay**. Stays/year = (Nights per year ÷ Average stay length).
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
        (125000, 0.05),   # 0% + 5%
        (250000, 0.07),   # 2% + 5%
        (925000, 0.10),   # 5% + 5%
        (1500000, 0.15),  # 10% + 5%
        (float('inf'), 0.17)  # 12% + 5%
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
    # Repayment formula
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

tab1, tab2, tab3 = st.tabs(["📄 Long-term let", "🛏️ Short-term (STR)", "📊 Summary"])

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

    # Yields
    annual_rent = monthly_rent * 12
    gross_yield = (annual_rent / price * 100.0) if price else 0.0
    annual_net = cashflow_mo_lt * 12
    coc_return = (annual_net / upfront_cash * 100.0) if upfront_cash > 0 else 0.0

    st.markdown("### Results (Long-term)")
    st.metric("Monthly mortgage", f"£{monthly_payment:,.0f}")
    st.metric("Monthly cashflow (after costs & mortgage)", f"£{cashflow_mo_lt:,.0f}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gross yield", f"{gross_yield:,.2f}%")
    with col2:
        st.metric("Annual net cashflow", f"£{annual_net:,.0f}")
    with col3:
        st.metric("Cash-on-cash return", f"{coc_return:,.2f}%")

    with st.expander("See monthly breakdown"):
        breakdown = pd.DataFrame({
            "Item": ["Rent", "Mgmt", "Maintenance", "Voids", "Fixed (svc+gr+ins+letting+other)", "Mortgage"],
            "Amount (£/mo)": [gross_month, -mgmt_mo, -maint_mo, -voids_mo, -fixed_mo, -monthly_payment]
        })
        st.dataframe(breakdown, use_container_width=True)

with tab2:
    st.subheader("Short-term rental inputs")
    colA, colB, colC = st.columns(3)
    with colA:
        nightly = st.number_input("Nightly rate (£)", min_value=0.0, value=100.0, step=5.0)
        occupancy = st.slider("Occupancy (% of nights)", 0.0, 100.0, 60.0, 1.0)
        avg_stay = st.number_input("Average stay (nights)", min_value=1.0, value=3.0, step=1.0)
    with colB:
        cleaning_per_stay = st.number_input("Cleaning cost per stay (£)", min_value=0.0, value=40.0, step=5.0)
        mgmt_pct_str = st.slider("Management (% of revenue)", 0.0, 50.0, 15.0, 0.5)
        platform_pct = st.slider("Platform/OTA fee (% of revenue)", 0.0, 20.0, 3.0, 0.5)
    with colC:
        utilities_mo = st.number_input("Utilities (monthly, £)", min_value=0.0, value=250.0, step=10.0)
        linen_mo = st.number_input("Linen/laundry (monthly, £)", min_value=0.0, value=60.0, step=5.0)
        rates_annual = st.number_input("Council tax / business rates (annual, £)", min_value=0.0, value=0.0, step=50.0)

    nights_year = 365 * (occupancy / 100.0)
    stays_year = max(nights_year / avg_stay, 0.0)
    revenue_year = nightly * nights_year
    mgmt_year = revenue_year * mgmt_pct_str / 100.0
    platform_year = revenue_year * platform_pct / 100.0
    cleaning_year = cleaning_per_stay * stays_year
    fixed_year = utilities_mo * 12 + linen_mo * 12 + rates_annual

    opex_year = mgmt_year + platform_year + cleaning_year + fixed_year
    noi_year = revenue_year - opex_year
    cashflow_year_str = noi_year - (monthly_payment * 12)
    cashflow_mo_str = cashflow_year_str / 12.0
    coc_return_str = (cashflow_year_str / upfront_cash * 100.0) if upfront_cash > 0 else 0.0

    st.markdown("### Results (Short-term)")
    st.metric("Monthly mortgage", f"£{monthly_payment:,.0f}")
    st.metric("Monthly cashflow (after costs & mortgage)", f"£{cashflow_mo_str:,.0f}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Revenue (annual)", f"£{revenue_year:,.0f}")
    with col2:
        st.metric("Operating costs (annual)", f"£{opex_year:,.0f}")
    with col3:
        st.metric("Cash-on-cash return", f"{coc_return_str:,.2f}%")

    with st.expander("See annual breakdown"):
        breakdown = pd.DataFrame({
            "Item": ["Revenue", "Mgmt", "Platform/OTA", "Cleaning", "Fixed (utils+linen+rates)", "Mortgage"],
            "Amount (£/yr)": [revenue_year, -mgmt_year, -platform_year, -cleaning_year, -fixed_year, -monthly_payment*12]
        })
        st.dataframe(breakdown, use_container_width=True)


with tab3:
    st.subheader("Deal summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Upfront cash required", f"£{upfront_cash:,.0f}")
    with col2:
        st.metric("Loan amount", f"£{loan:,.0f}")
    with col3:
        st.metric("Monthly mortgage", f"£{monthly_payment:,.0f}")

    # Recompute summary values explicitly
    # Long-term:
    monthly_rent_val = monthly_rent
    mgmt_mo_val = monthly_rent_val * mgmt_pct_lt / 100.0
    maint_mo_val = monthly_rent_val * maint_pct_lt / 100.0
    voids_mo_val = monthly_rent_val * voids_pct / 100.0
    fixed_mo_val = other_mo + (service_chg + ground_rent + insurance + letting_fees) / 12.0
    lt_cashflow = (monthly_rent_val - (mgmt_mo_val + maint_mo_val + voids_mo_val + fixed_mo_val)) - monthly_payment

    # Short-term:
    nights_year_sum = 365 * (occupancy / 100.0)
    stays_year_sum = max(nights_year_sum / avg_stay, 0.0)
    revenue_year_sum = nightly * nights_year_sum
    mgmt_year_sum = revenue_year_sum * mgmt_pct_str / 100.0
    platform_year_sum = revenue_year_sum * platform_pct / 100.0
    cleaning_year_sum = cleaning_per_stay * stays_year_sum
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

    st.download_button(
        "Download summary (CSV)",
        data=summary.to_csv(index=False).encode("utf-8"),
        file_name="deal_summary.csv",
        mime="text/csv",
    )


st.markdown("---")
st.caption("Built for quick screening. Always verify SDLT, lender criteria, and local regulations.")

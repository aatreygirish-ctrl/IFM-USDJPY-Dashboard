from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="IFM | USD/JPY Dashboard", page_icon="💱", layout="wide")
DATA_FILE = Path(__file__).with_name("USDJPY_IFM_compiled_dataset_2020_onwards.csv")
REQUIRED = ["date", "usd_jpy", "us_cpi", "jp_cpi", "us_rate", "jp_rate"]

@st.cache_data
def read_dataset(uploaded_bytes=None):
    if uploaded_bytes is not None:
        from io import BytesIO
        df = pd.read_csv(BytesIO(uploaded_bytes))
    elif DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
    else:
        raise FileNotFoundError("The compiled CSV is not beside app.py. Upload it in the sidebar.")
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError("Dataset is missing columns: " + ", ".join(missing))
    df = df[REQUIRED].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in REQUIRED[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()
    if df["date"].duplicated().any():
        raise ValueError("There is more than one row for a month. Please use the compiled monthly CSV.")
    # Keep the full monthly calendar. Missing source observations remain blank, not zero or interpolated.
    df = df.set_index("date").asfreq("MS").reset_index()
    return df

def build_metrics(df):
    d = df.copy().sort_values("date").reset_index(drop=True)
    d["us_inflation_yoy"] = (d["us_cpi"] / d["us_cpi"].shift(12) - 1) * 100
    d["jp_inflation_yoy"] = (d["jp_cpi"] / d["jp_cpi"].shift(12) - 1) * 100
    d["inflation_diff_us_minus_jp"] = d["us_inflation_yoy"] - d["jp_inflation_yoy"]
    d["rate_diff_us_minus_jp"] = d["us_rate"] - d["jp_rate"]
    base_rows = d.dropna(subset=["usd_jpy", "us_cpi", "jp_cpi"])
    if base_rows.empty:
        raise ValueError("No month has all three values needed to establish the PPP base.")
    b = base_rows.iloc[0]
    d["ppp_usdjpy"] = b.usd_jpy * (d["jp_cpi"] / b.jp_cpi) / (d["us_cpi"] / b.us_cpi)
    d["misalignment_pct"] = (d["usd_jpy"] / d["ppp_usdjpy"] - 1) * 100
    d["annual_spot_change_pct"] = (d["usd_jpy"] / d["usd_jpy"].shift(12) - 1) * 100
    # Start-month rates and exact t+12 monthly spot quote; no row-skipping across missing months.
    d["carry_gross_return_12m_pct"] = (((1 + d["us_rate"] / 100) * (d["usd_jpy"].shift(-12) / d["usd_jpy"]) / (1 + d["jp_rate"] / 100)) - 1) * 100
    d["carry_profitability_index"] = 100 * (1 + d["carry_gross_return_12m_pct"] / 100)
    return d

st.title("International Financial Management | USD/JPY")
st.caption("AI-assisted financial modelling · Relative PPP · Interest Rate Parity & Carry Trade · International Fisher Effect")
st.info("Exchange-rate convention: USD/JPY is JPY per USD. A rise means the US dollar appreciates against the Japanese yen.")
with st.sidebar:
    st.header("Dataset")
    upload = st.file_uploader("Optional: replace the included compiled CSV", type=["csv"])
    st.caption("Sample: January 2020 onward. Monthly observations. Source files are included in the project folder.")
try:
    raw = read_dataset(upload.getvalue() if upload else None)
    data = build_metrics(raw)
    usable = data.dropna(subset=["usd_jpy", "us_cpi", "jp_cpi", "us_rate", "jp_rate"])
    missing_counts = raw[REQUIRED[1:]].isna().sum()
    st.write(f"**Coverage:** {data.date.min():%B %Y} – {data.date.max():%B %Y} · {len(data)} calendar months")
    if missing_counts.sum():
        st.warning("Missing source observations have been retained as blanks; no values have been invented or filled. Missing counts: " + ", ".join(f"{k}: {v}" for k,v in missing_counts.items() if v))
    with st.expander("Dataset preview and data quality", expanded=False):
        st.dataframe(data, use_container_width=True)
        st.download_button("Download calculated dataset", data.to_csv(index=False).encode("utf-8"), "USDJPY_IFM_calculated_metrics.csv", "text/csv")
    tabs = st.tabs(["1 · PPP & Misalignment", "2 · IRP & Carry Trade", "3 · International Fisher Effect"])
    latest = data.dropna(subset=["usd_jpy", "ppp_usdjpy", "misalignment_pct"]).iloc[-1]
    with tabs[0]:
        st.subheader("Relative Purchasing Power Parity")
        a,b,c = st.columns(3)
        status = "USD relatively overvalued / JPY undervalued" if latest.misalignment_pct > 0 else "USD relatively undervalued / JPY overvalued" if latest.misalignment_pct < 0 else "At PPP benchmark"
        a.metric("Actual USD/JPY", f"{latest.usd_jpy:,.2f}")
        b.metric("PPP-implied USD/JPY", f"{latest.ppp_usdjpy:,.2f}")
        c.metric("Misalignment", f"{latest.misalignment_pct:+.2f}%")
        st.info(f"Latest available valuation: {status} ({latest.date:%B %Y}).")
        fig = px.line(data, x="date", y=["usd_jpy", "ppp_usdjpy"], labels={"value":"JPY per USD", "date":"Month", "variable":"Series"}, title="Actual spot rate vs relative-PPP implied rate")
        st.plotly_chart(fig, use_container_width=True)
        st.line_chart(data.set_index("date")[["misalignment_pct"]])
        with st.expander("Formula & calculation", expanded=False):
            st.markdown("**Relative Purchasing Power Parity (base-month method)**")
            st.latex(r"PPP_t = S_0 \times \frac{CPI_{JP,t}/CPI_{JP,0}}{CPI_{US,t}/CPI_{US,0}}")
            st.markdown("**Currency misalignment**")
            st.latex(r"Misalignment_t(\%) = \left(\frac{S_t}{PPP_t}-1\right)\times100")
            st.markdown(r"Here, \(S_t\) is the actual spot rate in JPY per USD. A positive result means the actual quote is above the PPP benchmark (relatively overvalued USD / undervalued JPY); a negative result means the reverse. The benchmark is anchored to the first month with valid spot and both CPI observations.")
        st.caption("PPP is a relative, long-run benchmark, not a short-term trading signal. Changing the sample's base month changes the benchmark.")
    with tabs[1]:
        st.subheader("Interest Rate Differential & Uncovered Carry Trade")
        rate_rows = data.dropna(subset=["rate_diff_us_minus_jp"]).iloc[-1]
        annual_rows = data.dropna(subset=["annual_spot_change_pct"])
        carry_rows = data.dropna(subset=["carry_gross_return_12m_pct"])
        a,b,c = st.columns(3)
        a.metric("Latest US − Japan rate differential", f"{rate_rows.rate_diff_us_minus_jp:+.2f} pp")
        b.metric("Latest 12-month spot change", "N/A" if annual_rows.empty else f"{annual_rows.iloc[-1].annual_spot_change_pct:+.2f}%")
        c.metric("Latest completed 12-month carry return", "N/A" if carry_rows.empty else f"{carry_rows.iloc[-1].carry_gross_return_12m_pct:+.2f}%")
        if not carry_rows.empty:
            st.metric("Carry profitability index (base 100)", f"{carry_rows.iloc[-1].carry_profitability_index:.2f}", "Above 100 = positive realised return; below 100 = loss")
        chart = data.dropna(subset=["rate_diff_us_minus_jp", "annual_spot_change_pct"])
        fig = px.line(chart, x="date", y=["rate_diff_us_minus_jp", "annual_spot_change_pct"], labels={"value":"Percent / percentage points", "date":"Month", "variable":"Measure"}, title="Nominal yield differential vs trailing 12-month USD/JPY change")
        st.plotly_chart(fig, use_container_width=True)
        st.line_chart(data.set_index("date")[["carry_profitability_index"]])
        st.markdown("**UIP sign convention:** With S quoted as JPY per USD, a positive US-minus-Japan interest differential implies expected USD depreciation (a fall in S) under UIP. The realised 12-month change is an ex-post outcome and need not match the expectation.")
        with st.expander("Formulas & calculation", expanded=False):
            st.markdown("**Nominal interest-rate differential**")
            st.latex(r"\Delta i_t = i_{US,t} - i_{JP,t}")
            st.markdown("**Trailing 12-month spot-rate change**")
            st.latex(r"SpotChange_t(\%) = \left(\frac{S_t}{S_{t-12}}-1\right)\times100")
            st.markdown("**Uncovered carry-trade return (JPY-funded, USD investment)**")
            st.latex(r"CarryReturn_t(\%) = \left[\frac{(1+i_{US,t}/100)(S_{t+12}/S_t)}{1+i_{JP,t}/100}-1\right]\times100")
            st.markdown("The interest rates are recorded as annual percentages and are divided by 100 inside the formula. For this simplified estimate, they are treated as effective annual rates. The trade borrows JPY, invests in USD for 12 months, then converts the USD proceeds back to JPY.")
            st.markdown("**Carry profitability index (base = 100)**")
            st.latex(r"Index_t = 100\times\left(1+\frac{CarryReturn_t}{100}\right)")
            st.markdown("An index above 100 indicates a positive realised return; below 100 indicates a loss. The t+12 exchange rate is matched by calendar month, not by skipping missing rows.")
        st.warning("Covered Interest Parity (CIP) is not tested: the dataset does not contain a matched-maturity forward exchange rate. This tab provides a spot-based UIP/carry diagnostic only.")
    with tabs[2]:
        st.subheader("International Fisher Effect Diagnostic")
        sample = data.dropna(subset=["inflation_diff_us_minus_jp", "rate_diff_us_minus_jp"])
        if len(sample) < 3:
            st.warning("Not enough overlapping observations to estimate a relationship.")
        else:
            corr = sample["inflation_diff_us_minus_jp"].corr(sample["rate_diff_us_minus_jp"])
            slope, intercept = np.polyfit(sample["inflation_diff_us_minus_jp"], sample["rate_diff_us_minus_jp"], 1)
            a,b,c = st.columns(3)
            a.metric("Pearson correlation", f"{corr:.3f}")
            b.metric("OLS slope", f"{slope:.3f}")
            c.metric("Observations", f"{len(sample):,}")
            fig = px.scatter(sample, x="inflation_diff_us_minus_jp", y="rate_diff_us_minus_jp", trendline="ols", labels={"inflation_diff_us_minus_jp":"US − Japan inflation differential (pp)", "rate_diff_us_minus_jp":"US − Japan nominal rate differential (pp)"}, title="Inflation differential vs nominal interest-rate differential")
            st.plotly_chart(fig, use_container_width=True)
            st.write(f"Estimated relationship: rate differential = {intercept:.3f} + {slope:.3f} × inflation differential.")
            with st.expander("Formulas & calculation", expanded=False):
                st.markdown("**Year-over-year inflation for each country**")
                st.latex(r"\pi_{c,t}(\%) = \left(\frac{CPI_{c,t}}{CPI_{c,t-12}}-1\right)\times100")
                st.markdown("**Inflation and nominal interest-rate differentials**")
                st.latex(r"\Delta\pi_t = \pi_{US,t}-\pi_{JP,t}")
                st.latex(r"\Delta i_t = i_{US,t}-i_{JP,t}")
                st.markdown("**Pearson correlation and OLS regression**")
                st.latex(r"r = \frac{Cov(\Delta\pi,\Delta i)}{\sigma_{\Delta\pi}\sigma_{\Delta i}}")
                st.latex(r"\Delta i_t = \alpha + \beta\Delta\pi_t + \varepsilon_t")
                st.markdown(f"For the available paired observations, the estimated intercept is **{intercept:.4f}** and slope is **{slope:.4f}**. The slope describes the sample association; it is not proof of causation.")
        st.caption("Inflation is realised year-over-year CPI inflation, used as a proxy rather than expected inflation. IFE is therefore assessed as a diagnostic, not a strict test. Differences in rate instruments, maturities, risk premia and policy regimes limit interpretation. Correlation does not prove causation.")
    st.divider()
    st.subheader("Data sources, definitions and limitations")
    st.markdown("""
- USD/JPY spot: FRED `DEXJPUS`, daily observations converted to monthly last available quote.
- US CPI: FRED `CPIAUCNS`, monthly, not seasonally adjusted.
- Japan CPI: Statistics Bureau of Japan / e-Stat, `All items`, 2020-base monthly index.
- US interest rate: FRED `FEDFUNDS`, monthly percent per annum.
- Japan interest rate: FRED `IRSTCI01JPM156N`, monthly percent per annum.

All series are aligned by calendar month. Missing observations remain blank; calculations requiring a missing observation are left unavailable. The selected interest-rate series are not perfectly identical instruments. Realised CPI inflation is not the same as expected inflation. The carry calculation is unhedged and simplified. CIP cannot be tested without forward rates.
""")
except Exception as e:
    st.error(f"Could not load the dataset: {e}")
    st.info("Place `USDJPY_IFM_compiled_dataset_2020_onwards.csv` in the same folder as app.py, or upload it in the sidebar.")

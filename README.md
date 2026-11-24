# International Financial Management — AI-Assisted Financial Modelling (USD/JPY)

## Current project version
- Currency pair: USD/JPY, quoted as Japanese yen per one US dollar (JPY per USD).
- Sample: January 2020 to October 2026 (82 calendar months).
- Frequency: monthly. Daily USD/JPY observations use the last available quote in each calendar month.
- Japan CPI source: Statistics Bureau of Japan / e-Stat, 2020-base monthly CPI, All Items.
- Missing source observations are retained as blanks. No values are invented, set to zero, or interpolated.

## Dashboard
`app.py` is a three-tab Streamlit dashboard:
1. Relative Purchasing Power Parity (PPP) and currency misalignment.
2. Interest-rate differential, UIP interpretation, and realised 12-month unhedged carry trade.
3. International Fisher Effect (IFE) diagnostic using inflation and nominal interest-rate differentials, Pearson correlation, and OLS regression.

Each tab includes an expandable formula and calculation explanation. The app also provides dataset coverage, missing-data notes, source mapping, and a downloadable calculated dataset.

## Data sources
| Variable | Source / series | Treatment |
|---|---|---|
| USD/JPY spot | FRED `DEXJPUS` | Daily; last available quote in each month |
| US CPI | FRED `CPIAUCNS` | Monthly, not seasonally adjusted |
| Japan CPI | Statistics Bureau of Japan / e-Stat, `zmi2020a.csv` | Monthly, 2020-base, All Items |
| US interest rate | FRED `FEDFUNDS` | Monthly, percent per annum |
| Japan interest rate | FRED `IRSTCI01JPM156N` | Monthly, percent per annum |

## Run locally
Install Python 3.10 or newer. In this folder run:
```bash
python -m pip install -r requirements.txt
streamlit run app.py
```
Or on Windows, double-click `START_HERE.bat`.

To rebuild the compiled monthly data from the five included source files:
```bash
python compile_dataset.py
```

## Deploy
The GitHub repository should contain at least:
- `app.py`
- `requirements.txt`
- `USDJPY_IFM_compiled_dataset_2020_onwards.csv`
- `README.md`

On Streamlit Community Cloud choose branch `main` and main file `app.py`.

## Model definitions and limitations
- Relative PPP is anchored to the first month with valid spot, US CPI and Japan CPI observations. The result depends on the base month.
- Misalignment is `(actual spot / PPP-implied spot - 1) * 100`. With JPY per USD quotation, positive values indicate relative USD overvaluation / JPY undervaluation.
- The nominal interest differential is US rate minus Japan rate. Under UIP, a positive US-minus-Japan differential implies expected USD depreciation (a fall in JPY per USD); the chart compares this with realised, not expected, spot changes.
- Carry return is a simplified, unhedged 12-month JPY-funded USD investment return. Annual rates are treated as effective annual rates. Transaction costs, taxes, credit/funding constraints and risk premia are not modelled.
- Covered Interest Parity (CIP) is not tested because matched-maturity forward exchange rates are not included.
- IFE uses realised year-over-year CPI inflation as a proxy, not expected inflation. The relationship is descriptive; correlation does not establish causation.
- The supplied US CPI file has one missing monthly observation (October 2025). It is retained as missing; affected calculations are unavailable where required.
- The two interest-rate series are not perfectly identical instruments or maturities.
- Data providers may revise historical observations. Record the download date when submitting.

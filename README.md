# IFM AI-Assisted Financial Modelling — USD/JPY

## Current project version
Sample: January 2020–October 2026 (82 calendar months). The dataset uses the supplied FRED files and Japan Statistics Bureau/e-Stat Japan CPI 2020-base All Items series.

## Files
- `app.py`: three-tab Streamlit dashboard.
- `USDJPY_IFM_compiled_dataset_2020_onwards.csv`: monthly source dataset.
- `USDJPY_IFM_calculated_metrics.csv`: dataset plus calculated model variables.
- `USDJPY_IFM_Data_Workbook.xlsx`: source data, metrics and data dictionary.
- `compile_dataset.py`: rebuilds the monthly dataset from the five raw source files.
- `methodology.docx`: two-page methodology and limitations.
- Five raw source files: DEXJPUS, CPIAUCNS, FEDFUNDS, IRSTCI01JPM156N and zmi2020a.

## Run locally (Windows)
1. Install Python 3.10 or newer.
2. Open Command Prompt in this folder.
3. Run `python -m pip install -r requirements.txt`.
4. Run `python compile_dataset.py` if you want to rebuild the dataset.
5. Run `streamlit run app.py`.
6. The dashboard opens in your browser. The compiled CSV is loaded automatically; you can also upload a replacement CSV in the sidebar.

## Calculations
PPP is relative PPP anchored to the first complete month. Spot changes and carry returns use exact calendar-month t+12/t-12 observations. Missing observations are retained as blanks and are not interpolated.

## Limitations
The supplied US CPI file contains one missing monthly observation. The dependent calculations are left unavailable rather than filled. Japan CPI is Statistics Bureau/e-Stat 2020-base All Items, while the US CPI is not seasonally adjusted. Interest-rate instruments are not perfectly identical. Realised CPI inflation is a proxy, not expected inflation. Carry is simplified and unhedged. CIP is not tested because no forward-rate series is included.

## Deployment
For Streamlit Community Cloud, upload `app.py`, `requirements.txt`, and `USDJPY_IFM_compiled_dataset_2020_onwards.csv` to a GitHub repository. Add the raw sources and compiler if you want reproducibility. Deploy `app.py` at https://share.streamlit.io/. Test all three tabs and submit the public app URL.

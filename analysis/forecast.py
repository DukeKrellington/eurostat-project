from typing import List
import numpy as np
import pandas as pd
import sqlite3
from config.settings import DB_PATH
from statsmodels.tsa.arima.model import ARIMA
import warnings
from numpy.linalg import LinAlgError
from statsmodels.tools.sm_exceptions import ConvergenceWarning, ValueWarning
import traceback

warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels.tsa")
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=FutureWarning, module="statsmodels")


def get_all_country_sector_combos() -> List[tuple[str, str]]:
    """ Get all unique (country_name, sector_name) pairs from emissions_data table. """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT DISTINCT country_name, sector_name
        FROM emissions_data
        ORDER BY country_name, sector_name;
    """

    combos = conn.execute(query).fetchall()
    conn.close()
    return combos


def get_emissions_data(country_name: str, sector_name: str) -> pd.DataFrame:
    """ Retrieve emissions data from emissions_data table. """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT year, emissions_ktco2, emissions_per_capita
        FROM emissions_data
        WHERE country_name = ? AND sector_name = ?
        ORDER BY year;
    """

    df = pd.read_sql_query(query, conn, params=[country_name, sector_name])
    conn.close()
    return df


# ---------- helper fallback ----------
def _linear_trend_forecast(series: pd.Series, steps: int) -> pd.Series:
    """Fit linear trend (year->value) and extrapolate. series.index should be numeric year or PeriodIndex."""
    # get numeric years
    try:
        years = np.array(series.index.year if isinstance(series.index, pd.PeriodIndex) else series.index.astype(int), dtype=float)
    except Exception:
        years = np.arange(len(series), dtype=float)
    values = np.array(series.values, dtype=float)

    if len(values) == 0:
        return pd.Series([np.nan] * steps, index=[None]*steps)
    if len(values) == 1:
        last = int(years[-1]) if len(years) else 0
        return pd.Series([float(values[-1])] * steps, index=[last + i for i in range(1, steps+1)])

    try:
        coeffs = np.polyfit(years, values, deg=1)
        poly = np.poly1d(coeffs)
        last_year = int(years[-1])
        future_years = np.arange(last_year + 1, last_year + 1 + steps)
        preds = poly(future_years)
        return pd.Series(preds, index=future_years.astype(int))
    except Exception:
        last = int(years[-1])
        return pd.Series([float(values[-1])] * steps, index=[last + i for i in range(1, steps+1)])

# ---------- ensure index ----------
def _ensure_year_period_index(s: pd.Series) -> pd.Series:
    # Convert numeric/integer index to PeriodIndex with yearly freq; if PeriodIndex/DatetimeIndex convert accordingly.
    if isinstance(s.index, pd.PeriodIndex):
        if s.index.freq is None:
            s.index = s.index.asfreq('Y')
        return s
    if isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.PeriodIndex(s.index.year, freq='Y')
        return s
    # else
    try:
        years = s.index.astype(int)
        s.index = pd.PeriodIndex(years, freq='Y')
        return s
    except Exception:
        s.index = pd.PeriodIndex(range(1, len(s) + 1), freq='Y')
        return s

# ---------- core forecasting function ----------
def forecast_series(series: pd.Series, forecast_years=10, order=(2, 1, 2)):
    """
    Forecast a numeric time series with ARIMA but robust to numerical failures.
    Returns pandas.Series indexed by integer years (future years).
    """
    # copy & drop na
    s = series.dropna().copy()
    if s.empty:
        # fallback: return NaNs (or you can choose repeated-last-value)
        return pd.Series([np.nan] * forecast_years, index=[None]*forecast_years)

    # Ensure PeriodIndex
    s = _ensure_year_period_index(s)

    # convert to numeric values and integer year index for final output
    last_year = int(s.index[-1].year)

    # try ARIMA (relaxed)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ConvergenceWarning)
            warnings.simplefilter("ignore", category=ValueWarning)
            warnings.simplefilter("ignore", category=UserWarning)
            model = ARIMA(s, order=order, enforce_stationarity=False, enforce_invertibility=False)
            model_fit = model.fit()
            pred = model_fit.get_forecast(steps=forecast_years)
            # predicted_mean has PeriodIndex; convert to integer years
            years_idx = [p.year for p in pred.predicted_mean.index]
            return pd.Series(pred.predicted_mean.values, index=years_idx)
    except (LinAlgError, np.linalg.LinAlgError) as lae:
        print(f"[forecast_series] LinAlgError during ARIMA fit: {lae}")
    except Exception as e:
        print(f"[forecast_series] ARIMA fit exception: {type(e).__name__}: {e}")
        # print stack for container logs
        traceback.print_exc()

    # try alternative optimizer (Nelder-Mead)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ConvergenceWarning)
            model = ARIMA(s, order=order, enforce_stationarity=False, enforce_invertibility=False)
            model_fit = model.fit(method='nm', disp=False, maxiter=500)
            pred = model_fit.get_forecast(steps=forecast_years)
            years_idx = [p.year for p in pred.predicted_mean.index]
            return pd.Series(pred.predicted_mean.values, index=years_idx)
    except Exception as e_nm:
        print(f"[forecast_series] ARIMA (nm) fit failed: {type(e_nm).__name__}: {e_nm}")
        traceback.print_exc()

    # fallback: linear trend
    try:
        fallback = _linear_trend_forecast(pd.Series(s.values, index=[p.year for p in s.index]), forecast_years)
        print("[forecast_series] Falling back to linear trend forecast.")
        return fallback
    except Exception as e_f:
        print(f"[forecast_series] Linear fallback failed: {type(e_f).__name__}: {e_f}")
        traceback.print_exc()
        # last-resort: repeat last value
        return pd.Series([float(s.values[-1])] * forecast_years, index=[last_year + i for i in range(1, forecast_years+1)])

# ---------- forecast_all with failure logging ----------
def forecast_all(forecast_years=10):
    """
    Forecast emissions and emissions_per_capita for all country/sector combinations.
    If a series fails, we log the failure to a DB table and continue.
    """
    combos = get_all_country_sector_combos()
    results = []
    failures = []

    for country, sector in combos:
        df = get_emissions_data(country, sector)
        if df.empty or len(df) < 3:
            # insufficient history; skip but record as failure with reason
            failures.append({'country_name': country, 'sector_name': sector, 'reason': 'insufficient_history'})
            continue

        df = df.set_index('year')

        # Forecast emissions_ktco2
        try:
            emissions_forecast = forecast_series(df['emissions_ktco2'], forecast_years)
        except Exception as e:
            failures.append({'country_name': country, 'sector_name': sector, 'reason': f'emissions_error: {e}'})
            emissions_forecast = pd.Series([np.nan]*forecast_years, index=list(range(df.index[-1]+1, df.index[-1]+1+forecast_years)))

        # Forecast emissions_per_capita
        try:
            per_capita_forecast = forecast_series(df['emissions_per_capita'], forecast_years)
        except Exception as e:
            failures.append({'country_name': country, 'sector_name': sector, 'reason': f'percapita_error: {e}'})
            per_capita_forecast = pd.Series([np.nan]*forecast_years, index=list(range(df.index[-1]+1, df.index[-1]+1+forecast_years)))

        # Align indices and append results
        forecast_years_idx = list(emissions_forecast.index)
        for year, e_val, p_val in zip(forecast_years_idx,
                                      emissions_forecast.values,
                                      per_capita_forecast.values):
            results.append({
                'year': int(year),
                'country_name': country,
                'sector_name': sector,
                'forecast_emissions_ktco2': float(e_val) if not np.isnan(e_val) else None,
                'forecast_emissions_per_capita': float(p_val) if not np.isnan(p_val) else None
            })

    # write failures to DB
    if failures:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS forecast_failures (
                    country_name TEXT,
                    sector_name TEXT,
                    reason TEXT
                );
            """)
            cur.executemany("INSERT INTO forecast_failures (country_name, sector_name, reason) VALUES (?,?,?)",
                            [(f['country_name'], f['sector_name'], f['reason']) for f in failures])
            conn.commit()
        finally:
            conn.close()

    return pd.DataFrame(results)


def load_forecasts_to_db(forecast_df: pd.DataFrame):
    """ Load forecast results into emissions_forecast table in SQLite. """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emissions_forecast (
            year INTEGER,
            country_name TEXT,
            sector_name TEXT,
            forecast_emissions_ktco2 REAL,
            forecast_emissions_per_capita REAL,
            PRIMARY KEY (year, country_name, sector_name)
        );
    """)

    forecast_df.to_sql('emissions_forecast', conn, if_exists='replace', index=False)
    conn.close()
    print(f'Successfully loaded forecasts for {len(forecast_df)} rows.')


if __name__ == "__main__":
    print("Generating ARIMA forecasts for all countries and sectors...")
    forecasts_df = forecast_all(forecast_years=10)
    load_forecasts_to_db(forecasts_df)
    print("Forecasting completed.")

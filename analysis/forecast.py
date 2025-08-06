import pandas as pd
import sqlite3
from config.settings import DB_PATH
from statsmodels.tsa.arima.model import ARIMA
import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning

warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels.tsa")
warnings.filterwarnings("ignore", category=ConvergenceWarning)


def get_all_country_sector_combos():
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


def get_emissions_data(country_name, sector_name):
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


def forecast_series(series, forecast_years=10, order=(2, 1, 2)):
    """
    Forecast a numeric time series with ARIMA.
    Returns a pandas Series of forecasts.
    """
    series.index = pd.PeriodIndex(series.index, freq='Y')
    model = ARIMA(series, order=order)
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=forecast_years)
    return forecast


def forecast_all(forecast_years=10):
    """
    Forecast emissions and emissions_per_capita for all country/sector combinations.
    Returns a DataFrame with forecasts for all.
    """
    combos = get_all_country_sector_combos()
    results = []

    for country, sector in combos:
        df = get_emissions_data(country, sector)
        if df.empty or len(df) < 5:  # Skip if insufficient history
            continue

        df = df.set_index('year')

        # Forecast emissions_ktco2
        emissions_forecast = forecast_series(df['emissions_ktco2'], forecast_years)
        # Forecast emissions_per_capita
        per_capita_forecast = forecast_series(df['emissions_per_capita'], forecast_years)

        forecast_years_idx = range(df.index[-1] + 1, df.index[-1] + forecast_years + 1)

        for year, e_val, p_val in zip(forecast_years_idx, emissions_forecast, per_capita_forecast):
            results.append({
                'year': year,
                'country_name': country,
                'sector_name': sector,
                'forecast_emissions_ktco2': e_val,
                'forecast_emissions_per_capita': p_val
            })

    return pd.DataFrame(results)


def load_forecasts_to_db(forecast_df):
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

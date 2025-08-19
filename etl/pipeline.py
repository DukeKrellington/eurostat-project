from etl.extract import fetch_emissions_data
from etl.transform import transform_emissions_data
from etl.load import create_connection, create_table, load_transformed_data
from analysis.forecast import forecast_all, load_forecasts_to_db


def run_pipeline(start_year: int=1990, end_year: int=2023):
    """
    Full ETL + Forecast pipeline:
      1. Extract emissions data
      2. Transform emissions data
      3. Load historical data into SQLite
      4. Forecast emissions & emissions_per_capita for all countries/sectors
      5. Load forecasts into SQLite
    """
    print("Extracting emissions data...")
    emissions_raw_data = fetch_emissions_data(start_year, end_year)

    print("Transforming emissions data...")
    transformed_data = transform_emissions_data(emissions_raw_data)

    print("Creating table...")
    conn = create_connection()
    create_table(conn)

    print("Loading transformed data...")
    load_transformed_data(transformed_data, conn)
    conn.close()

    print("Running ARIMA forecasts...")
    forecasts_df = forecast_all(forecast_years=10)
    load_forecasts_to_db(forecasts_df)

    print("Pipeline complete (Historical + Forecast data updated).")


if __name__ == "__main__":
    run_pipeline()

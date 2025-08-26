import sqlite3
import pandas as pd
from config.settings import DB_PATH


def get_top_emitters(year: int, top_n: int=10) -> pd.DataFrame:
    """
    Return top N emitters by total emissions for a given year.
    """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT country_name, sector_name, emissions_ktco2
        FROM emissions_data
        WHERE year = ?
        AND country_name NOT LIKE 'EU %'
        ORDER BY emissions_ktco2 DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=[year, top_n])
    conn.close()
    return df


def get_biggest_decreases(start_year: int, end_year: int, top_n: int=10) -> pd.DataFrame:
    """
    Return top N countries with the largest percentage decrease between two years.
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT 
            e1.country_name,
            e1.emissions_ktco2 AS start_emissions,
            e2.emissions_ktco2 AS end_emissions,
            ROUND(((e1.emissions_ktco2 - e2.emissions_ktco2) / e1.emissions_ktco2) * 100, 2) AS pct_change
        FROM emissions_data e1
        JOIN emissions_data e2
            ON e1.country_name = e2.country_name
            AND e1.sector_name = e2.sector_name
        WHERE e1.year = ? AND e2.year = ?
        AND e1.sector_name LIKE 'Total%'
        ORDER BY pct_change DESC
        LIMIT ?
        """, conn, params=[start_year, end_year, top_n]
    )
    conn.close()
    return df


def get_worst_forecast_increases(top_n: int=10) -> pd.DataFrame:
    """
    Return top N country-sector pairs with the largest forecasted %
    increase comparing the last historical year to the last forecast year.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        # Get last historical year
        hist_df = pd.read_sql_query("SELECT MAX(year) AS year FROM emissions_data", conn)
        fore_df = pd.read_sql_query("SELECT MAX(year) AS year FROM emissions_forecast", conn)

        if hist_df.empty or fore_df.empty:
            # missing tables or no rows
            return pd.DataFrame()

        hist_year = hist_df.iloc[0]['year']
        fore_year = fore_df.iloc[0]['year']

        # Validate years
        if pd.isna(hist_year) or pd.isna(fore_year):
            return pd.DataFrame()

        hist_year = int(hist_year)
        fore_year = int(fore_year)

        query = """
            SELECT
                h.country_name,
                h.sector_name,
                h.emissions_ktco2 AS hist_emissions,
                f.forecast_emissions_ktco2 AS forecast_emissions,
                ((f.forecast_emissions_ktco2 - h.emissions_ktco2) / h.emissions_ktco2) * 100 AS pct_change
            FROM emissions_data h
            JOIN emissions_forecast f
              ON TRIM(h.country_name) = TRIM(f.country_name)
             AND TRIM(h.sector_name) = TRIM(f.sector_name)
            WHERE h.year = ? AND f.year = ?
            ORDER BY pct_change DESC
            LIMIT ?
        """

        df = pd.read_sql_query(query, conn, params=[hist_year, fore_year, top_n])
        return df

    finally:
        conn.close()


if __name__ == "__main__":
    print("Top 10 emitters in 2023:")
    print(get_top_emitters(2023))

    print("\nBiggest decreases from 2010 to 2023:")
    print(get_biggest_decreases(2010, 2023))

    print("\nWorst forecast increases over next period:")
    print(get_worst_forecast_increases())

import pandas as pd

from eurostatapiclient import EurostatAPIClient


def fetch_emissions_data(start_year=1990, end_year=2023, geo_filter=None):
    """
    Fetch GHG emissions data from Eurostat API using the 'env_air_gge' dataset.

    Parameters:
        start_year (int): First year of data to retrieve.
        end_year (int): Last year of data to retrieve.
        geo_filter (list): List of ISO country codes (e.g., ['DE', 'FR', 'EU27_2020'])

    Returns:
        pd.DataFrame: Emissions data
    """
    client = EurostatAPIClient(language='en', response_type='json', version='1.0')
    dataset_code = 'env_air_gge'

    params = {
        'unit': 'THS_T',       # thousand tonnes CO2 equivalent
        'airpol': 'GHG',       # Greenhouse gases total
        'src_crf': ['TOTXMEMO', 'CRF1', 'CRF2', 'CRF3', 'CRF4', 'CRF5', 'CRF6']  # Major industries
    }
    if geo_filter:
        params['geo'] = geo_filter

    dataset = client.get_dataset(dataset_code, params=params)

    df = dataset.to_dataframe()
    df = df[(df['time'].astype(int) >= start_year) & (df['time'].astype(int) <= end_year)]

    return df


def fetch_population_data(start_year=1990, end_year=2023, geo_filter=None):
    """
    Fetch total population by country and year using EurostatAPIClient.

    Parameters:
        start_year (int): Earliest year to include.
        end_year (int): Latest year to include.
        geo_filter (list[str]): ISO country codes (e.g. ['FR', 'DE'])

    Returns:
        pd.DataFrame: DataFrame with [country_code, year, population]
    """
    dataset_code = 'demo_pjan'
    client = EurostatAPIClient(language='en', response_type='json', version='1.0')

    # Eurostat uses these params for total population
    params = {
        'age': 'TOTAL',
        'sex': 'T',
        'unit': 'NR'
    }

    if geo_filter:
        params['geo'] = geo_filter

    dataset = client.get_dataset(dataset_code, params=params)
    df = dataset.to_dataframe()

    # Clean and format
    df = df.rename(columns={
        'geo': 'country_code',
        'time': 'year',
        'values': 'population'
    })
    df['year'] = df['year'].astype(int)
    df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    df = df.dropna(subset=['population'])

    df = df[['country_code', 'year', 'population']]
    return df


if __name__ == '__main__':
    print(fetch_emissions_data().head())
    print(fetch_population_data().head())

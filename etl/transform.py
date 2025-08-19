# etl/transform.py

import pandas as pd
from etl.extract import fetch_population_data, fetch_emissions_data

from config.settings import COUNTRY_MAP, SECTOR_MAP


def transform_emissions_data(emissions_df: pd.DataFrame, start_year: int=1990, end_year: int=2023):
    """
    Cleans and transforms raw emissions data:
      - Filters for relevant years
      - Renames key columns
      - Merges in population data
      - Computes per capita emissions

    Parameters:
        emissions_df (pd.DataFrame): Raw emissions data
        start_year (int): Earliest year to keep
        end_year (int): Latest year to keep

    Returns:
        pd.DataFrame: Transformed data with per capita emissions
    """

    # --- Step 1: Filter by year ---
    emissions_df['year'] = emissions_df['time'].astype(int)
    emissions_df = emissions_df[(emissions_df['year'] >= start_year) & (emissions_df['year'] <= end_year)]

    # --- Step 2: Rename & clean ---
    emissions_df = emissions_df.rename(columns={
        'geo': 'country_code',
        'src_crf': 'sector_code',
        'values': 'emissions_ktco2',
        'value': 'emissions_ktco2'
    })

    emissions_df = emissions_df[['country_code', 'sector_code', 'year', 'emissions_ktco2']]
    emissions_df.dropna(subset=['emissions_ktco2'], inplace=True)
    emissions_df = emissions_df[emissions_df['emissions_ktco2'] > 0]
    emissions_df['emissions_ktco2'] = emissions_df['emissions_ktco2'].astype(float)

    # --- Step 3: Fetch population data ---
    unique_countries = emissions_df['country_code'].unique().tolist()
    population_df = fetch_population_data(start_year=start_year, end_year=end_year, geo_filter=unique_countries)

    # --- Step 4: Merge population ---
    merged_df = pd.merge(
        emissions_df,
        population_df,
        how='left',
        on=['country_code', 'year']
    )

    # --- Step 5: enrich sector and country names ---
    merged_df['sector_name'] = merged_df['sector_code'].map(SECTOR_MAP)
    merged_df['country_name'] = merged_df['country_code'].map(COUNTRY_MAP)
    merged_df = merged_df[['year', 'sector_name', 'country_name', 'population', 'emissions_ktco2']]

    # --- Step 6: Compute per capita emissions (kt CO2 per person) ---
    merged_df.dropna(subset=['population', 'country_name'], inplace=True)
    merged_df['population'] = merged_df['population'].astype(int)

    merged_df['emissions_per_capita'] = round(merged_df['emissions_ktco2'] * 1_000_000 / merged_df['population'], 2)  # Convert kt to kg CO2

    return merged_df


if __name__ == "__main__":
    print(transform_emissions_data(fetch_emissions_data()))

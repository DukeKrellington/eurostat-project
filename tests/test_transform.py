import pandas as pd
import etl.transform as transform_module

def test_transform_emissions_data_basic(monkeypatch):
    # Prepare a minimal raw emissions dataframe
    raw = pd.DataFrame([
        {'time': '2020', 'geo': 'DE', 'src_crf': '1A1', 'values': 1000.0, 'unit': 'THS_T', 'airpol': 'GHG'},
        {'time': '2020', 'geo': 'FR', 'src_crf': '1A1', 'values': 800.0, 'unit': 'THS_T', 'airpol': 'GHG'}
    ])

    # Prepare a population dataframe to be returned by fetch_population_data
    pop = pd.DataFrame([
        {'country_code': 'DE', 'year': 2020, 'population': 83000000},
        {'country_code': 'FR', 'year': 2020, 'population': 67000000}
    ])

    # Monkeypatch the fetch_population_data function used inside transform module
    monkeypatch.setattr(transform_module, 'fetch_population_data', lambda start_year, end_year, geo_filter=None: pop)

    # Ensure COUNTRY_MAP and SECTOR_MAP contain entries used in test
    transform_module.COUNTRY_MAP['DE'] = 'Germany'
    transform_module.COUNTRY_MAP['FR'] = 'France'
    transform_module.SECTOR_MAP['1A1'] = 'Energy industries'

    out = transform_module.transform_emissions_data(raw, start_year=2020, end_year=2020)

    # Check columns
    assert set(['year','sector_name','country_name','population','emissions_ktco2','emissions_per_capita']).issubset(out.columns)

    # Check values for Germany
    de = out[out['country_name']=='Germany'].iloc[0]
    assert de['year'] == 2020
    assert de['sector_name'] == 'Energy industries'
    assert de['emissions_ktco2'] == 1000.0
    expected_per_capita = round(1000.0 * 1_000_000 / 83000000, 2)
    assert abs(de['emissions_per_capita'] - expected_per_capita) < 1e-6

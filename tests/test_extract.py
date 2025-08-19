import pandas as pd
import etl.extract as extract_module

class DummyDataset:
    def __init__(self, df):
        self._df = df
    def to_dataframe(self):
        return self._df

class DummyClient:
    def __init__(self, *args, **kwargs):
        pass
    def get_dataset(self, dataset_code, params=None):
        # return different sample data depending on dataset_code
        if dataset_code == 'env_air_gge':
            df = pd.DataFrame([
                {'time': '2005', 'geo': 'DE', 'src_crf': 'TOTAL', 'values': 100.0},
                {'time': '2010', 'geo': 'DE', 'src_crf': 'TOTAL', 'values': 200.0},
                {'time': '2020', 'geo': 'FR', 'src_crf': 'TOTAL', 'values': 300.0},
            ])
            return DummyDataset(df)
        elif dataset_code == 'demo_pjan':
            df = pd.DataFrame([
                {'time': '2010', 'geo': 'DE', 'values': 80000000},
                {'time': '2020', 'geo': 'DE', 'values': 83000000},
                {'time': '2020', 'geo': 'FR', 'values': 67000000},
            ])
            return DummyDataset(df)
        else:
            return DummyDataset(pd.DataFrame())

def test_fetch_emissions_data_monkeypatch(monkeypatch):
    # Monkeypatch the EurostatAPIClient in the extract module
    monkeypatch.setattr(extract_module, 'EurostatAPIClient', DummyClient)

    df = extract_module.fetch_emissions_data(start_year=2008, end_year=2021)
    years = sorted(df['time'].astype(int).unique().tolist())
    assert years == [2010, 2020]
    assert 'geo' in df.columns

def test_fetch_population_data_monkeypatch(monkeypatch):
    monkeypatch.setattr(extract_module, 'EurostatAPIClient', DummyClient)
    df = extract_module.fetch_population_data(start_year=2010, end_year=2020)
    assert set(['country_code', 'year', 'population']).issubset(df.columns)
    row = df[(df['country_code']=='DE') & (df['year']==2020)]
    assert not row.empty
    assert int(row.iloc[0]['population']) == 83000000
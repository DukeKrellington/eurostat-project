import sqlite3
from fastapi.testclient import TestClient
import fastapi_app.main as api_module
from fastapi_app.main import app

def setup_temp_db(tmp_path):
    db_path = tmp_path / "api_test.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # create tables with required columns
    cur.execute('''
        CREATE TABLE emissions_data (
            year INTEGER,
            sector_name TEXT,
            country_name TEXT,
            population INTEGER,
            emissions_ktco2 REAL,
            emissions_per_capita REAL
        )
    ''')
    cur.execute('''
        CREATE TABLE emissions_forecast (
            year INTEGER,
            country_name TEXT,
            sector_name TEXT,
            forecast_emissions_ktco2 REAL,
            forecast_emissions_per_capita REAL
        )
    ''')
    # Insert sample historical rows
    rows = [
        (2020, 'Total', 'Germany', 83000000, 1000.0, 12.05),
        (2020, 'Total', 'France', 67000000, 800.0, 11.94),
        (2021, 'Total', 'Germany', 83100000, 950.0, 11.43)
    ]
    cur.executemany('INSERT INTO emissions_data (year, sector_name, country_name, population, emissions_ktco2, emissions_per_capita) VALUES (?,?,?,?,?,?)', rows)
    # Insert forecast rows (e.g., 2030)
    forecast_rows = [
        (2030, 'Germany', 'Total', 500.0, 6.0),
        (2030, 'France', 'Total', 400.0, 5.9)
    ]
    cur.executemany('INSERT INTO emissions_forecast (year, country_name, sector_name, forecast_emissions_ktco2, forecast_emissions_per_capita) VALUES (?,?,?,?,?)', forecast_rows)
    conn.commit()
    conn.close()
    return db_path

def test_historical_endpoint(tmp_path, monkeypatch):
    db_path = setup_temp_db(tmp_path)
    # Monkeypatch DB_PATH in API module
    monkeypatch.setattr(api_module, 'DB_PATH', str(db_path))

    client = TestClient(app)
    res = client.get('/historical', params={'country':'Germany', 'sector':'Total'})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(d['year']==2020 for d in data)

def test_top_emitters_endpoint(tmp_path, monkeypatch):
    db_path = setup_temp_db(tmp_path)
    monkeypatch.setattr(api_module, 'DB_PATH', str(db_path))

    client = TestClient(app)
    res = client.get('/trends/top_emitters', params={'year':2020, 'top_n':2})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert any(d['country_name']=='Germany' for d in data)

def test_forecast_endpoint(tmp_path, monkeypatch):
    db_path = setup_temp_db(tmp_path)
    monkeypatch.setattr(api_module, 'DB_PATH', str(db_path))

    client = TestClient(app)
    res = client.get('/forecast', params={'country':'Germany', 'sector':'Total'})
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]['year'] == 2030
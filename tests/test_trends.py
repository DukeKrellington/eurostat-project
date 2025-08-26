import sqlite3
import analysis.trends as trends

def setup_temp_db(tmp_path):
    db_path = tmp_path / "temp.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # create emissions_data table
    cur.execute('''
        CREATE TABLE emissions_data (
            country_name TEXT,
            sector_name TEXT,
            year INTEGER,
            emissions_ktco2 REAL
        )
    ''')
    rows = [
        ('Germany','Total',2010, 1000.0),
        ('Germany','Total',2023, 600.0),
        ('France','Total',2010, 800.0),
        ('France','Total',2023, 500.0),
        ('Spain','Total',2010, 300.0),
        ('Spain','Total',2023, 450.0),
    ]
    cur.executemany('INSERT INTO emissions_data (country_name, sector_name, year, emissions_ktco2) VALUES (?,?,?,?)', rows)
    conn.commit()
    conn.close()
    return db_path

def test_trends_functions(tmp_path, monkeypatch):
    db_path = setup_temp_db(tmp_path)
    monkeypatch.setattr(trends, 'DB_PATH', str(db_path))
    top = trends.get_top_emitters(2023, top_n=2)
    assert len(top) == 2
    dec = trends.get_biggest_decreases(2010, 2023, top_n=5)
    assert 'Germany' in dec['country_name'].values

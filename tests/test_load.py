import pandas as pd
from etl import load

def test_load_transformed_data(tmp_path):
    # Create a temp sqlite db path
    db_path = tmp_path / "test.db"
    conn = load.create_connection(str(db_path))
    load.create_table(conn)

    # Create a small dataframe with expected columns
    df = pd.DataFrame([{
        'year': 2020,
        'sector_name': 'Energy industries',
        'country_name': 'Germany',
        'population': 83000000,
        'emissions_ktco2': 1000.0,
        'emissions_per_capita': 12.04
    }])

    # Load into DB
    load.load_transformed_data(df, conn, table_name='emissions_data', if_exists='replace')

    # Query back and assert
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM emissions_data')
    count = cur.fetchone()[0]
    assert count == 1
    conn.close()

import sqlite3

import pandas as pd

from config.settings import DB_PATH


def create_connection(db_path: str=DB_PATH) -> sqlite3.Connection:
    """ Create a database connection to a SQLite database """
    conn = sqlite3.connect(db_path)
    return conn


def create_table(conn: sqlite3.Connection):
    """ Create the merged emissions table if it does not exist. """
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emissions_data
    (
        year                 INTEGER,
        sector_name          TEXT,
        country_name         TEXT,
        population           INTEGER,
        emissions_ktco2      REAL,
        emissions_per_capita REAL,
        PRIMARY KEY (year, sector_name, country_name)
    );
    ''')

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_year ON emissions_data(year);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_country ON emissions_data(country_name);")

    conn.commit()


def load_transformed_data(
        df: pd.DataFrame,
        conn: sqlite3.Connection,
        table_name: str='emissions_data',
        if_exists: str='replace'):
    """
    Load transformed data into SQLite table
    :param df: Transformed data frame
    :param conn: Database connection
    :param table_name: Name of table to load into
    :param if_exists: replace or append to existing table if exists
    :return:
    """

    expected_columns = ['year', 'sector_name', 'country_name', 'population', 'emissions_ktco2', 'emissions_per_capita']
    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        raise ValueError('Missing columns in DataFrame: {}'.format(missing))

    df[expected_columns].to_sql(table_name, conn, if_exists=if_exists, index=False)
    print(f'Loaded {len(df)} rows into {table_name} table')


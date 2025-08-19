from fastapi import FastAPI, HTTPException, Query
import uvicorn
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import pandas as pd
from config.settings import DB_PATH

app = FastAPI(
    title="EU Emissions API",
    description="API for historical and forecasted greenhouse gas emissions data",
    version="1.0.0"
)

# Pydantic models
class EmissionRecord(BaseModel):
    year: int
    sector_name: str
    country_name: str
    emissions_ktco2: float
    emissions_per_capita: float

class ForecastRecord(BaseModel):
    year: int
    sector_name: str
    country_name: str
    forecast_emissions_ktco2: float
    forecast_emissions_per_capita: float

class TopEmitter(BaseModel):
    country_name: str
    sector_name: str
    emissions_ktco2: float

class ChangeRecord(BaseModel):
    country_name: str
    sector_name: str
    start_emissions: float
    end_emissions: float
    pct_change: float

# Utility function to query DB
def query_db(query: str, params: tuple = ()) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()
    return df

# Endpoints
@app.get("/historical", response_model=List[EmissionRecord])
def get_historical(
    country: str = Query(..., description="Country name, e.g., Germany"),
    sector: str = Query(..., description="Sector name, e.g., Energy industries"),
    start_year: Optional[int] = Query(None),
    end_year: Optional[int] = Query(None)
):
    """Retrieve historical emissions data for a country and sector."""
    query = """
        SELECT year, sector_name, country_name, emissions_ktco2, emissions_per_capita
        FROM emissions_data
        WHERE country_name = ? AND sector_name = ?
    """
    params = [country, sector]
    if start_year is not None:
        query += " AND year >= ?"
        params.append(start_year)
    if end_year is not None:
        query += " AND year <= ?"
        params.append(end_year)
    query += " ORDER BY year"
    df = query_db(query, tuple(params))
    if df.empty:
        raise HTTPException(status_code=404, detail="No historical data found.")
    return df.to_dict(orient="records")

@app.get("/forecast", response_model=List[ForecastRecord])
def get_forecast(
    country: str = Query(...),
    sector: str = Query(...),
    start_year: Optional[int] = Query(None),
    end_year: Optional[int] = Query(None)
):
    """Retrieve forecasted emissions data for a country and sector."""
    query = """
        SELECT year, sector_name, country_name, forecast_emissions_ktco2, forecast_emissions_per_capita
        FROM emissions_forecast
        WHERE country_name = ? AND sector_name = ?
    """
    params = [country, sector]
    if start_year is not None:
        query += " AND year >= ?"
        params.append(start_year)
    if end_year is not None:
        query += " AND year <= ?"
        params.append(end_year)
    query += " ORDER BY year"
    df = query_db(query, tuple(params))
    if df.empty:
        raise HTTPException(status_code=404, detail="No forecast data found.")
    return df.to_dict(orient="records")

@app.get("/trends/top_emitters", response_model=List[TopEmitter])
def top_emitters(year: int = Query(..., description="Year to query"), top_n: int = Query(10)):
    """Return top N emitters by total emissions for a year."""
    query = """
        SELECT country_name, sector_name, emissions_ktco2
        FROM emissions_data
        WHERE year = ?
        ORDER BY emissions_ktco2 DESC
        LIMIT ?
    """
    df = query_db(query, (year, top_n))
    if df.empty:
        raise HTTPException(status_code=404, detail="No data for given year.")
    return df.to_dict(orient="records")

@app.get("/trends/decreases", response_model=List[ChangeRecord])
def biggest_decreases(
    start_year: int = Query(...),
    end_year: int = Query(...),
    top_n: int = Query(10)
):
    """Return top N largest % decreases between two years."""
    query = """
        SELECT e1.country_name, e1.sector_name,
               e1.emissions_ktco2 AS start_emissions,
               e2.emissions_ktco2 AS end_emissions,
               ((e1.emissions_ktco2 - e2.emissions_ktco2) / e1.emissions_ktco2) * 100 AS pct_change
        FROM emissions_data e1
        JOIN emissions_data e2
          ON e1.country_name = e2.country_name
         AND e1.sector_name = e2.sector_name
        WHERE e1.year = ? AND e2.year = ?
        ORDER BY pct_change DESC
        LIMIT ?
    """
    df = query_db(query, (start_year, end_year, top_n))
    if df.empty:
        raise HTTPException(status_code=404, detail="No data for given years.")
    return df.to_dict(orient="records")

@app.get("/trends/forecast_increases", response_model=List[ChangeRecord])
def worst_forecast_increases(top_n: int = Query(10)):
    """Return top N forecasted % increases comparing last hist vs last forecast."""
    # Determine years
    conn = sqlite3.connect(DB_PATH)
    hist_year = pd.read_sql_query("SELECT MAX(year) AS year FROM emissions_data", conn).iloc[0]['year']
    fore_year = pd.read_sql_query("SELECT MAX(year) AS year FROM emissions_forecast", conn).iloc[0]['year']
    conn.close()

    query = """
        SELECT h.country_name, h.sector_name,
               h.emissions_ktco2 AS start_emissions,
               f.forecast_emissions_ktco2 AS end_emissions,
               ((f.forecast_emissions_ktco2 - h.emissions_ktco2) / h.emissions_ktco2) * 100 AS pct_change
        FROM emissions_data h
        JOIN emissions_forecast f
          ON h.country_name = f.country_name
         AND h.sector_name = f.sector_name
        WHERE h.year = ? AND f.year = ?
        ORDER BY pct_change DESC
        LIMIT ?
    """
    df = query_db(query, (hist_year, fore_year, top_n))
    if df.empty:
        raise HTTPException(status_code=404, detail="No forecast data available.")
    return df.to_dict(orient="records")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

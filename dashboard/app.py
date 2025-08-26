import sys
from pathlib import Path

from config.settings import DB_PATH

import dash
from dash import dcc, html, Input, Output
import pandas as pd
import sqlite3
import plotly.graph_objs as go

# Add the project root to sys.path for imports
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # for deployment

# Global font settings
FONT_FAMILY = 'Helvetica, Arial, sans-serif'
TITLE_FONT_SIZE = 24
AXIS_TITLE_FONT_SIZE = 14
TEXT_FONT_SIZE = 16

# Queries


def query_historical(country: str, sector: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT year, emissions_ktco2, emissions_per_capita
        FROM emissions_data
        WHERE country_name = ? AND sector_name = ?
        ORDER BY year
    """
    df = pd.read_sql_query(query, conn, params=(country, sector))
    conn.close()
    return df


def query_forecast(country: str, sector: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT year, forecast_emissions_ktco2, forecast_emissions_per_capita
        FROM emissions_forecast
        WHERE country_name = ? AND sector_name = ?
        ORDER BY year
    """
    df = pd.read_sql_query(query, conn, params=(country, sector))
    conn.close()
    return df


def get_country_sector_options():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT DISTINCT country_name, sector_name FROM emissions_data ORDER BY country_name, sector_name"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [{'label': f"{c} - {s}", 'value': f"{c}|||{s}"} for c, s in rows]

# App layout
app.layout = html.Div(
    style={'fontFamily': FONT_FAMILY, 'margin': '40px'},
    children=[
        html.H1("EU Emissions Dashboard", style={'fontSize': TITLE_FONT_SIZE}),
        html.P(
            "Use this dashboard to explore historical and forecasted greenhouse gas emissions. "
            "Select a country and sector below to view two separate charts: one for total emissions and another for emissions per capita.",
            style={'fontSize': TEXT_FONT_SIZE}
        ),
        html.Div([
            html.Label("Select Country and Sector:", style={'fontSize': TEXT_FONT_SIZE}),
            dcc.Dropdown(
                id="country-sector-dropdown",
                options=get_country_sector_options(),
                value=None,
                placeholder="Select a country and sector",
                clearable=True,
                searchable=True,
                style={
                    'width': '400px',
                    'fontSize': TEXT_FONT_SIZE
                }
            ),
        ], style={'marginBottom': '30px'}),

        html.Div([
            dcc.Graph(id="total-emissions-chart"),
            dcc.Graph(id="per-capita-chart")
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}),

        html.Div(id="no-data-message", style={'color': 'red', 'fontSize': TEXT_FONT_SIZE, 'marginTop': '20px'})
    ]
)

# Callbacks
@app.callback(
    [Output("total-emissions-chart", "figure"),
     Output("per-capita-chart", "figure"),
     Output("no-data-message", "children")],
    [Input("country-sector-dropdown", "value")]
)
def update_charts(selected_value):
    # Default empty
    empty_fig = go.Figure()
    empty_fig.update_layout(
        template='plotly_white',
        font=dict(family=FONT_FAMILY)
    )
    if not selected_value:
        return empty_fig, empty_fig, ""

    country, sector = selected_value.split("|||")
    hist_df = query_historical(country, sector)
    forecast_df = query_forecast(country, sector)

    if hist_df.empty:
        return empty_fig, empty_fig, f"No data found for {country} - {sector}."

    # Total emissions chart
    total_fig = go.Figure()
    total_fig.add_trace(go.Scatter(
        x=hist_df['year'], y=hist_df['emissions_ktco2'],
        mode='lines+markers', name='Historical',
    ))
    if not forecast_df.empty:
        total_fig.add_trace(go.Scatter(
            x=forecast_df['year'], y=forecast_df['forecast_emissions_ktco2'],
            mode='lines+markers', name='Forecast', line=dict(dash='dash')
        ))
    total_fig.update_layout(
        title=f"Total Emissions for {country} - {sector}",
        xaxis_title="Year",
        yaxis_title="Emissions (kt CO₂)",
        font=dict(family=FONT_FAMILY)
    )

    # Per capita emissions chart
    percap_fig = go.Figure()
    percap_fig.add_trace(go.Scatter(
        x=hist_df['year'], y=hist_df['emissions_per_capita'],
        mode='lines+markers', name='Historical',
    ))
    if not forecast_df.empty:
        percap_fig.add_trace(go.Scatter(
            x=forecast_df['year'], y=forecast_df['forecast_emissions_per_capita'],
            mode='lines+markers', name='Forecast', line=dict(dash='dash')
        ))
    percap_fig.update_layout(
        title=f"Emissions Per Capita for {country} - {sector}",
        xaxis_title="Year",
        yaxis_title="Emissions per Person (kg)",
        font=dict(family=FONT_FAMILY)
    )

    # Clear message
    return total_fig, percap_fig, ""


if __name__ == "__main__":
    app.run(debug=True)

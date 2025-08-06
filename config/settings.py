from pathlib import Path
"""
Configuration and lookup tables for the EU Emissions Tracker project.
Includes mappings for sectors (src_crf), countries, and optional population data.
"""

# Mapping from Eurostat `src_crf` sector code to human-readable sector names
SECTOR_MAP = {
    "TOTXMEMO": "Total (excluding memo items)",
    "CRF1": "Energy",
    "CRF2": "Industrial processes and product use",
    "CRF3": "Agriculture",
    "CRF4": "Land use, land use change  and forestry (LULUCF)",
    "CRF5": "Waste management",
    "CRF6": "Other sectors",
}

# Country code to name mapping
COUNTRY_MAP = {
    "BE": "Belgium", "BG": "Bulgaria", "CZ": "Czechia",
    "DK": "Denmark", "DE": "Germany", "EE": "Estonia",
    "IE": "Ireland", "EL": "Greece", "ES": "Spain",
    "FR": "France", "HR": "Croatia", "IT": "Italy",
    "CY": "Cyprus", "LV": "Latvia", "LT": "Lithuania",
    "LU": "Luxembourg", "HU": "Hungary", "MT": "Malta",
    "NL": "Netherlands", "AT": "Austria", "PL": "Poland",
    "PT": "Portugal", "RO": "Romania", "SI": "Slovenia",
    "SK": "Slovakia", "FI": "Finland", "SE": "Sweden",
    "NO": "Norway", "IS": "Iceland",
    "EU27_2020": "EU (27 countries, from 2020)",
}

# Root project path (adjust if needed)
PROJECT_ROOT = Path(__file__).parent.parent

# Data directory
DATA_DIR = PROJECT_ROOT / "data"

# SQLite database path
DB_PATH = DATA_DIR / "emissions.db"

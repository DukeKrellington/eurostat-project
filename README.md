# Eurostat Emissions ETL, Forecasting, and Dashboard

This project ingests greenhouse gas emissions data from **Eurostat**, processes and stores it in an SQLite database, applies time-series forecasting models, and exposes the results via both a **FastAPI backend** and an interactive **Dash dashboard**.

The system is fully containerized with **Docker Compose**.

---

## Features

- **ETL Pipeline**  
  - Extracts emissions data from Eurostat APIs  
  - Transforms and stores it in a PostgreSQL database  
  - Runs forecasting models to project future emissions  

- **Forecasting**  
  - Uses `statsmodels` ARIMA for time-series analysis  
  - Handles initialization and edge cases to avoid solver errors  

- **FastAPI Service**  
  - Provides programmatic access to stored emissions and forecasts  
  - Useful for integration with external applications  

- **Dash Dashboard**  
  - Visualizes emissions and forecasts in a clean web UI  
  - Runs inside Docker and can be accessed via browser  

---

## Project Structure
```
eurostat-project/
│── analysis/ # Forecasting models and analysis scripts
│── dashboard/ # Dash web application
│── etl/ # Extract, Transform, Load pipeline
│── api/ # FastAPI backend
│── requirements.txt # Python dependencies
│── docker-compose.yml # Multi-service Docker configuration
│── Dockerfile # Base Docker image
```

---

## Running the Project

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/eurostat-project.git
cd eurostat-project
```

### 2. Build and start containers
```
docker-compose up --build
```
This will start:

- ETL pipeline (runs and exits after loading data + forecasts)
- FastAPI backend (default port: 8000)
- Dash dashboard (default port: 8050)

### 3. Access the services

- Dashboard → http://localhost:8050
- API docs (Swagger UI) → http://localhost:8000/docs

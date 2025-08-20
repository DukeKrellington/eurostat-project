# Use an official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app
ENV OPENBLAS_NUM_THREADS=1
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

# Install system dependencies (for numpy/pandas/statsmodels)
RUN apt-get update && apt-get install -y \
    build-essential \
    libopenblas-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Confirm that DB path is present
RUN mkdir -p /app/data
# Copy project files
COPY . .
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Expose ports for FastAPI (8000) and Dashboard (8050)
EXPOSE 8000 8050

# Default command - runs uvicorn (API) and dash in parallel via a script
CMD ["bash", "start.sh"]
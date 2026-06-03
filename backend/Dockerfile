# =====================================================================
# Dockerfile for Plum OPD Adjudication FastAPI Backend
# =====================================================================

# Use an official lightweight Python runtime as a parent image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container to /app
WORKDIR /app

# Copy only requirements first to leverage Docker cache for pip layers
COPY requirements.txt /app/requirements.txt

# Install all backend Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire backend directory contents into the container
COPY . /app/

# Expose port 8000 for FastAPI / Uvicorn traffic
EXPOSE 8000

# By default, run uvicorn to host our backend api service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

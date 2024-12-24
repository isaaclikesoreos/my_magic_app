# Use Python 3.13 base image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=a_core.settings

# Set the working directory inside the container
WORKDIR /app

# Copy application code into the container
COPY . /app

# Install system dependencies and MariaDB
RUN apt-get update && apt-get install -y --no-install-recommends \
    mariadb-server \
    mariadb-client \
    libmariadb-dev \
    pkg-config \
    build-essential \
    gcc \
    dos2unix \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install --upgrade pip && pip install pipenv

# Convert Pipfile and Pipfile.lock to Unix format in case of encoding issues
RUN dos2unix Pipfile Pipfile.lock || true

# Install Python dependencies using pipenv
RUN pipenv install --system --deploy

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose MariaDB and Django ports
EXPOSE 3306 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

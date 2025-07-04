# Use official Python image as base image
FROM python:3.11-slim-bullseye as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH=/app/server

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY server/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Development stage
FROM base as development

# Set environment variables for development
ENV DJANGO_SETTINGS_MODULE=server.settings \
    DEBUG=True

# Expose the port the app runs on
EXPOSE 8000

# Change to server directory for running commands
WORKDIR /app/server

# Run the development server with auto-reload
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Production stage (LAST so it's used by default on Render)
FROM base as production

# Set environment variables for production
ENV DJANGO_SETTINGS_MODULE=server.settings \
    PORT=8000 \
    WEB_CONCURRENCY=4 \
    DEBUG=False \
    PYTHONUNBUFFERED=1

# Create and switch to a non-root user
RUN useradd -m myuser && chown -R myuser:myuser /app

# Change to server directory for running commands
WORKDIR /app/server

# Create static and media directories with proper permissions
RUN mkdir -p /app/server/staticfiles /app/server/media \
    && chown -R myuser:myuser /app/server/staticfiles /app/server/media

# Switch to non-root user
USER myuser

# Requirements are already installed in the base image.

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Run database migrations (only if needed, might want to run this separately in production)
# RUN python manage.py migrate --noinput

# Use gunicorn as the production server
CMD gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers $WEB_CONCURRENCY \
    --worker-tmp-dir /dev/shm \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level=info \
    server.wsgi:application

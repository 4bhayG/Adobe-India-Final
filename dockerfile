# Multi-stage Dockerfile for React (Frontend) + Django (Backend)

# 1. Build React Frontend
FROM node:20 AS frontend-build
WORKDIR /app/frontend
COPY react-frontend/ ./
RUN npm install && npm run build

# 2. Backend: Django
FROM python:3.12-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    nginx \
    curl \
    procps \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY django-backend/ ./Back/
COPY --from=frontend-build /app/frontend/dist/ /app/Back/static/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r Back/requirements.txt

# Collect Django static files
RUN python Back/manage.py collectstatic --noinput

# Ensure media directory exists
RUN mkdir -p /app/Back/media/PDFsUploaded

# Copy Nginx config
COPY docker_nginx.conf /etc/nginx/conf.d/default.conf

# Entrypoint script
COPY docker_entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port 8080
EXPOSE 8080

# Start Nginx and Gunicorn
CMD ["/entrypoint.sh"]

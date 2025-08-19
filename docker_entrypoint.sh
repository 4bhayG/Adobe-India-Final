#!/bin/bash
set -e

echo "Starting Docker entrypoint script..."

# Ensure media directory exists and is writable
echo "Creating media directories..."
mkdir -p /app/Back/media/PDFsUploaded
chmod -R 777 /app/Back/media/PDFsUploaded

# Change to Django directory
cd /app/Back

# Wait for any potential database setup (if needed)
echo "Testing Django setup..."
python manage.py check --deploy || echo "Django check failed, continuing anyway..."

# Start Gunicorn with better configuration
echo "Starting Gunicorn..."
gunicorn Adobe.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class sync \
    --worker-connections 1000 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --daemon

# Wait a moment for Gunicorn to start
echo "Waiting for Gunicorn to start..."
sleep 3

# Verify Gunicorn is running
if ! pgrep -f gunicorn > /dev/null; then
    echo "ERROR: Gunicorn failed to start!"
    exit 1
fi

# Test if Gunicorn is responding
echo "Testing Gunicorn connection..."
if curl -f http://127.0.0.1:8000/ > /dev/null 2>&1; then
    echo "✓ Gunicorn is responding"
else
    echo "⚠ Gunicorn is running but not responding to HTTP requests"
fi

# Start Nginx in foreground
echo "Starting Nginx..."
nginx -t && echo "✓ Nginx configuration is valid" || echo "✗ Nginx configuration has errors"
exec nginx -g 'daemon off;'

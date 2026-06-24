# Use a lightweight official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV DB_NAME=/data/spendly.db

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create the data directory for the SQLite volume and set permissions
RUN mkdir -p /data

# Expose port
EXPOSE 8080

# Command to run the application using gunicorn
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app"]

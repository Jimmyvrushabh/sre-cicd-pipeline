FROM python:3.12-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Prevent stdout/stderr buffering
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better caching)
COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ .

# Create non-root user
RUN useradd -m appuser

# Switch to non-root user
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

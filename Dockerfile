FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run with gunicorn
CMD ["gunicorn", "app:create_app()", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120"]

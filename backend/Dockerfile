FROM python:3.12-slim

WORKDIR /app

# Install git (required for pip to install GitHub dependencies)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create an unprivileged user
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app

# Run the app as that user
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

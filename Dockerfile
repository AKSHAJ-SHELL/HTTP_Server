FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Create directories for images, metadata, and logs
RUN mkdir -p images metadata logs

# Expose port
EXPOSE 8000

# Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]


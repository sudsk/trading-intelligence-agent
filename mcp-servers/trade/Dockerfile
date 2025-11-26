FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Create data directory
RUN mkdir -p /app/data

# Copy mock data if exists
COPY data/ /app/data/ 2>/dev/null || true

# Expose port
EXPOSE 8080

# Run server
CMD ["python", "server.py"]

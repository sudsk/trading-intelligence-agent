FROM python:3.11-slim

WORKDIR /app

# Copy shared directory from context root
COPY shared/ /app/shared/

# Copy agents-service files
COPY agents-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents-service/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

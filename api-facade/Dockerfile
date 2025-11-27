FROM python:3.11-slim

WORKDIR /app

# Copy shared directory from context root
COPY shared/ /app/shared/

# Copy api-facade files
COPY api-facade/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api-facade/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

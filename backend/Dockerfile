FROM python:3.11-slim

WORKDIR /app

# System packages for OCR and PDF processing.
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from the backend package.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and shared config from the repository root.
COPY backend/app/ ./app/
COPY config/ ./config/

RUN mkdir -p /app/data/uploads /app/data/chroma_db /app/data/logs

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

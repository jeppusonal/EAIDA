FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY app/ app/
COPY data/analytics/ data/analytics/
COPY data/features/ data/features/
COPY data/predictions/ data/predictions/

EXPOSE 8000 8501

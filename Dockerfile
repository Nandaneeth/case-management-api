FROM python:3.11.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt pyarrow==25.0.1

COPY . .

VOLUME ["/app/data"]

CMD ["python", "-m", "etl.pipeline"]

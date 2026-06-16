FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api api
COPY core core

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "python -m uvicorn api.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

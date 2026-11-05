FROM python:3.12-slim-bookworm

ARG APP_VERSION=local

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION} \
    APP_PORT=8000 \
    GUNICORN_WORKERS=2

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends procps iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser \
       --create-home --shell /usr/sbin/nologin appuser

COPY requirements.lock ./

RUN python -m pip install --no-cache-dir -r requirements.lock

COPY app.py gunicorn.conf.py ./

ENV FAIL_HEALTH=1

USER appuser

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:create_app()"]
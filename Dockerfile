FROM python:3.12-alpine

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv && \
    uv venv /opt/venv

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN uv pip install -r /requirements.txt && \
    rm -rf /root/.cache

COPY app /app
WORKDIR /app

RUN python manage.py collectstatic --noinput

CMD daphne -b 0.0.0.0 -p 8080 app.asgi:application --http-timeout 30 --verbosity 0

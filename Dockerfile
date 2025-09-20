FROM python:3.12-alpine

COPY requirements.txt /requirements.txt

RUN apk add --update --no-cache build-base

RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir wheel && \
    pip3 install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

COPY app /app

WORKDIR /app

RUN python3 manage.py collectstatic

CMD daphne -b 0.0.0.0 -p 8080 app.asgi:application --http-timeout 30 --verbosity 0

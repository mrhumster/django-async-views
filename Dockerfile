# syntax=docker/dockerfile:1
FROM python:3.10.4-slim-buster
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN mkdir build
WORKDIR /build
COPY . .
RUN pip install --no-cache-dir  -r requirements.txt
EXPOSE 80
WORKDIR /build/hello_async
CMD python -m uvicorn hello_async.asgi:application --host 0.0.0.0 --port 80
FROM python:3.13.1-alpine
COPY --from=ghcr.io/astral-sh/uv:0.5.30 /uv /uvx /bin/

WORKDIR /app
COPY . .

RUN apk update && apk add --no-cache \
    musl-dev \
    libc-dev \
    python3-dev \
    libffi-dev \
    gcc \
    g++

ENV CASS_DRIVER_NO_EXTENSIONS=1

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ENV EXCHANGE_NAME=rabbitmq-exchange
ENV QUEUE_NAME=rabbitmq-queue
ENV ROUTING=rabbitmq-routing-key
ENV KEYSPACE=example-keyspace

CMD ["uv", "run", "main.py"]


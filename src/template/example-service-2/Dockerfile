FROM python:3.13.1-alpine
COPY --from=ghcr.io/astral-sh/uv:0.5.30 /uv /uvx /bin/

WORKDIR /app
COPY . .

ENV CASS_DRIVER_NO_EXTENSIONS=1

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

RUN uv pip install -e shared/

RUN addgroup -S group1 && adduser -S user1 -G group1 -u 1000
RUN chown -R user1:group1 /app
USER user1:group1

CMD ["uv", "run", "main.py"]

FROM dhi.io/python:3.13-sfw-dev AS builder
COPY --from=dhi.io/uv:0.10-dev /usr/local/bin/uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . /app

FROM dhi.io/python:3.13 AS runtime
WORKDIR /app

# Copy the whole prepared app tree including its permsissions from the builder stage
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["gunicorn"]
CMD ["--chdir", "/app", "-b", "0.0.0.0:8080", "--workers=10", "--preload", "app:server"]

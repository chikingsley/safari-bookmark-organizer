FROM python:3.12-slim AS builder

# Pin uv to a specific version for reproducibility.
COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /bin/

ENV UV_LINK_MODE=copy
WORKDIR /app

COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM python:3.12-slim

COPY --from=builder /bin/uv /bin/uv
COPY --from=builder /bin/uvx /bin/uvx

WORKDIR /app
COPY --from=builder /app /app

# Ensure OpenCode installer paths are discoverable.
ENV PATH=/root/.opencode/bin:/root/.local/bin:$PATH \
    UV_LINK_MODE=copy

# Install OpenCode CLI in the image
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://opencode.ai/install | bash

EXPOSE 8000

CMD ["uv", "run", "safari-organizer", "preview", "/data/bookmarks.plist", "--host", "0.0.0.0", "--port", "8000", "--no-open"]

FROM python:3.12-alpine

WORKDIR /app/

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY ./pyproject.toml ./uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

COPY ./scripts /app/scripts
COPY ./auction /app/auction

RUN python --version

CMD ["sh", "/app/scripts/run.sh"]

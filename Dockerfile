# Copied from: 
#   https://docs.astral.sh/uv/guides/integration/aws-lambda/#deploying-a-docker-image
FROM ghcr.io/astral-sh/uv:0.6.8 AS uv
FROM public.ecr.aws/lambda/python:3.13 AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_INSTALLER_METADATA=1
ENV UV_LINK_MODE=copy

# Omit any local packages (`--no-emit-workspace`) and development dependencies (`--no-dev`).
# This ensures that the Docker layer cache is only invalidated when the `pyproject.toml` or `uv.lock`
# files change, but remains robust to changes in the application code.
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv export \
        --frozen \
        --no-emit-workspace \
        --no-dev \
        --no-editable \
        -o requirements.txt \
    && uv pip install \
        -r requirements.txt \
        --target "${LAMBDA_TASK_ROOT}"

FROM public.ecr.aws/lambda/python:3.13

COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}
COPY ./wa ${LAMBDA_TASK_ROOT}/wa
COPY ./handler.py ${LAMBDA_TASK_ROOT}/handler.py

CMD ["handler.handler"]
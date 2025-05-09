FROM python:3.8-slim AS builder
RUN apt-get update \
    && pip3 install --upgrade pip

ENV PYTHONUNBUFFERED 1

# Install uv
RUN pip install uv --no-cache-dir

# Copy dependency files
RUN mkdir /code
WORKDIR /code
COPY pyproject.toml uv.lock .

# Create venv and install dependencies
ENV UV_COMPILE_BYTECODE=1
RUN uv venv /code/.venv
RUN uv sync --locked
RUN uv sync --locked --group controller


FROM python:3.8-slim AS runtime

RUN apt-get update \
    && apt-get install -y git \
    && git clone https://github.com/networktocode/ntc-templates.git \
    && mv ntc-templates ntc_templates \
    && pip3 install --upgrade pip

ENV PYTHONUNBUFFERED 1

RUN addgroup --system app \
    && adduser --system --ingroup app app

RUN mkdir /code
WORKDIR /code

COPY --chown=app:app . /code

RUN chown -R app:app /code
RUN mkdir /code/.venv

COPY --from=builder /code/.venv/ /code/.venv/
ENV PATH=/code/.venv/bin:$PATH

USER app
CMD gunicorn -p controller.pid -c gunicorn.conf.py netpalm.netpalm_controller:app

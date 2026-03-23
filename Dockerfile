FROM python:3.12-slim AS base

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

# Install ntc-templates
WORKDIR /usr/local/lib/python3.12/site-packages
RUN git clone --depth 1 https://github.com/networktocode/ntc-templates.git \
    && mv ntc-templates ntc_templates

# Install poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /code

# Install dependencies first for better layer caching
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --no-directory && pip install --no-cache-dir setuptools

# Copy application code
COPY . .
RUN poetry install --only-root

STOPSIGNAL SIGINT

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
# Default to controller; override in docker-compose for workers
CMD ["gunicorn", "-c", "gunicorn.conf.py", "netpalm.netpalm_controller:app"]

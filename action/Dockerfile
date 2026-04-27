FROM python:3.12-slim

WORKDIR /forgebench

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git gh \
    && rm -rf /var/lib/apt/lists/*

COPY . /forgebench

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

ENTRYPOINT ["/forgebench/action/entrypoint.sh"]

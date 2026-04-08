FROM phpdockerio/php:8.3-fpm
WORKDIR "/application"

RUN apt-get update \
    && apt-get -y --no-install-recommends install \
        php8.3-mysql php8.3-gd \
        python3 python3-pip python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# vytvoř venv
RUN python3 -m venv /opt/bp-venv \
    && /opt/bp-venv/bin/pip install --no-cache-dir -U pip setuptools wheel

COPY checker/requirements.txt /tmp/checker-requirements.txt
RUN /opt/bp-venv/bin/pip install --no-cache-dir -r /tmp/checker-requirements.txt
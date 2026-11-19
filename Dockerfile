# Python 3.14 is the runtime target.
FROM python:3.14-slim-bookworm

ENV PYTHONUNBUFFERED=1

USER root


RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    poppler-utils \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    gettext \
 && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir /matchco
RUN mkdir /matchco/config
RUN mkdir /entrypoint
RUN mkdir /migrate

# Copy files to directories
COPY matchco/  matchco/
COPY config/  matchco/config/
COPY migrate/migrate.sh migrate/
COPY entrypoint/entrypoint.sh /entrypoint

# Install the project requirements.
RUN pip3 install --upgrade pip --no-cache
RUN pip3 install -r /matchco/config/requirements.txt

# Add permission to entrypoint file
RUN chmod +x /entrypoint/entrypoint.sh

ENTRYPOINT ["/entrypoint/entrypoint.sh"]

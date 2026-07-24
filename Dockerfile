# Python 3.12 is the runtime target after the Wagtail removal.
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1

USER root


RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    gettext \
 && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir /talk
RUN mkdir /talk/config
RUN mkdir /entrypoint
RUN mkdir /migrate

# Copy files to directories
COPY talk/  talk/
COPY config/  talk/config/
COPY migrate/migrate.sh migrate/
COPY entrypoint/entrypoint.sh /entrypoint

# Install the project requirements.
RUN pip3 install --upgrade pip --no-cache
RUN pip3 install -r /talk/config/requirements.txt

# Add permission to entrypoint file
RUN chmod +x /entrypoint/entrypoint.sh

ENTRYPOINT ["/entrypoint/entrypoint.sh"]

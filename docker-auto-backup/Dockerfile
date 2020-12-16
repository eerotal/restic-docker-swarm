FROM debian:buster-slim

LABEL description="A Docker image for automatically backing up Docker volumes."
LABEL maintainer="Eero Talus"
LABEL license="BSD 3-clause license"
LABEL copyright="Copyright 2020 Eero Talus"

ENV CRON_EXPR="0 4 * * *"
ENV ENABLE_RSYNC="n"
ENV RSYNC_DEST=""
ENV SSH_HOST=""
ENV ROTATE_AFTER="5"

USER root
WORKDIR /root

RUN DEBIAN_FRONTEND=noninteractive; \
    apt-get update&& \
    apt-get install -y --no-install-recommends rsync gpg ssh cron

COPY docker-config.sh .
RUN sed -i "1s:^:WORKDIR=\"$(pwd)\"\n:" docker-config.sh

COPY docker-entrypoint.sh .
COPY docker-backup.sh .
COPY docker-healthcheck.sh .
COPY docker-rotate-backups.sh .
COPY docker-rotate-local.sh .
COPY docker-rotate-remote.sh .

CMD ["sh", "docker-entrypoint.sh"]

HEALTHCHECK \
    --interval=60s \
    --timeout=5s \
    --start-period=1ms \
    --retries=2 \
    CMD sh docker-healthcheck.sh 120

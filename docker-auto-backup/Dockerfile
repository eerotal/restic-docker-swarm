FROM alpine:3

LABEL description="A Docker image for automatically backing up Docker volumes."
LABEL maintainer="Eero Talus"
LABEL license="BSD 3-clause license"
LABEL copyright="Copyright 2020 Eero Talus"

ENV CRON_EXPR="0 4 * * *"
ENV ENABLE_RSYNC="n"
ENV RSYNC_DEST=""
ENV SSH_HOST=""
ENV ROTATE_AFTER="5"
ENV CONTAINERS=""

USER root
WORKDIR /root

RUN apk update && \
    apk add --no-cache \
        docker-cli \
        rsync \
        gnupg \
        openssh-client \
        python3 && \
    rm -rf /var/cache/apk

COPY docker-entrypoint.sh .
COPY docker-healthcheck.sh .
COPY src/ .
RUN sed -i "1s:^:WORKDIR=\"$(pwd)\"\n:" config.sh

CMD ["sh", "docker-entrypoint.sh"]

HEALTHCHECK \
    --interval=86400s \
    --timeout=5s \
    --start-period=1ms \
    --retries=2 \
    CMD sh docker-healthcheck.sh 86400

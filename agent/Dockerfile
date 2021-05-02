FROM alpine:3

LABEL description="An image for running a restic agent in a Docker Swarm."
LABEL maintainer="Eero Talus"
LABEL license="BSD 3-clause license"
LABEL copyright="Copyright 2020 Eero Talus"

ENV SSH_HOST=""
ENV SSH_PORT="2222"
ENV SSH_PRIVKEY_FILE="/run/secrets/restic-ssh-privkey"
ENV SSH_KNOWN_HOSTS_FILE="/run/secrets/restic-ssh-known-hosts"
ENV RESTIC_REPO_PASSWORD_FILE="/run/secrets/restic-repo-password"
ENV BACKUP_FORGET_POLICY="1 1 1 1 1 0y0m0d0h 0 false"

# Not intended to be changed by users.
ENV BACKUP_BASE="/backup"
ENV TARGET_USER="restic"
ENV TARGET_USER_UID="1000"
ENV SSH_ID_FILE="/home/${TARGET_USER}/.ssh/id"

USER root
RUN apk add --no-cache restic python3 py3-pip openssh && \
    apk add --no-cache --virtual py3-build-deps py3-setuptools

RUN adduser -D -u $TARGET_USER_UID $TARGET_USER
WORKDIR /home/$TARGET_USER

COPY docker-entrypoint.sh .
COPY docker-healthcheck.py .

COPY restic_docker_swarm_agent/ restic_docker_swarm_agent/
RUN cd restic_docker_swarm_agent/ && \
    python3 setup.py install && \
    cd .. && \
    rm -rf restic_docker_swarm_agent/

RUN apk del --no-cache py3-build-deps

# Add a custom shell profile script.
COPY config/ash/ashrc "$HOME_DIR/.ashrc"
ENV ENV="$HOME_DIR/.ashrc"

CMD ["sh", "docker-entrypoint.sh"]

HEALTHCHECK \
    --interval=10s \
    --timeout=10s \
    --start-period=20s \
    --retries=5 \
    CMD python3 docker-healthcheck.py

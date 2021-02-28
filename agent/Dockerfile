FROM alpine:3

LABEL description="An image for running a restic agent in a Docker Swarm."
LABEL maintainer="Eero Talus"
LABEL license="BSD 3-clause license"
LABEL copyright="Copyright 2020 Eero Talus"

ENV SSH_HOST=""
ENV SSH_PORT="2222"
ENV BACKUP_PATH="/backup"
ENV REPO_PATH=""

ENV SERVICE_NAME=""
ENV PRE_HOOK=""
ENV POST_HOOK=""
ENV RUN_AT=""

ENV SSH_PRIVKEY_FILE="/run/secrets/restic-ssh-privkey"
ENV SSH_KNOWN_HOSTS_FILE="/run/secrets/restic-ssh-known-hosts"
ENV RESTIC_REPO_PASSWORD_FILE="/run/secrets/restic-repo-password"

ENV USER="restic"
ENV USER_UID="1000"

USER root
RUN apk add --no-cache restic python3 docker-py openssh

RUN adduser -D -u $USER_UID $USER
WORKDIR /home/$USER

COPY docker-entrypoint.sh .
COPY src/ rds/

CMD ["sh", "docker-entrypoint.sh"]

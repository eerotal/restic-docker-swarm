FROM alpine:3

LABEL description="An image for running a restic SFTP repo in a Docker Swarm."
LABEL mainatiner="Eero Talus"
LABEL license="BSD 3-clause license"
LABEL copyright="Copyright 2020 Eero Talus"

ARG HOME_DIR="/restic"

ENV REPO_DIR="$HOME_DIR/repositories"
ENV SSHD_PORT="2222"
ENV USER="restic"
ENV USER_UID="1000"

USER root
WORKDIR /root

RUN apk add --no-cache openssh restic gettext
RUN rm -f /etc/ssh/ssh_host_*

COPY config/openssh/sshd_config /tmp/sshd_config
RUN envsubst < /tmp/sshd_config >> /etc/ssh/sshd_config && \
    rm -f /tmp/sshd_config

COPY docker-entrypoint.sh .

# Create the main user for the image. The user is created here
# without a password but one is set in docker-entrypoint.sh
# because otherwise you can't SSH to the container.
RUN adduser -D -u $USER_UID -h "$HOME_DIR" $USER

# Add a custom shell profile script.
COPY config/ash/ashrc "$HOME_DIR/.ashrc"
ENV ENV="$HOME_DIR/.ashrc"

WORKDIR "$HOME_DIR"

CMD ["sh", "/root/docker-entrypoint.sh"]

#!/bin/sh

set -e

printf "secret" | docker secret create restic-repo-password_v0 -
docker secret create restic-ssh-privkey_v0 assets/id_rsa
docker secret create restic-ssh-pubkey_v0 assets/id_rsa.pub

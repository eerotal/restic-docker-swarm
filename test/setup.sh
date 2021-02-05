#!/bin/sh

set -e

docker secret create restic-ssh-privkey_v1 assets/id_rsa
docker secret create restic-ssh-pubkey_v1 assets/id_rsa.pub

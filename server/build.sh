#!/bin/sh

printf "[INFO] Building restic-docker-swarm-server.\n"
docker build -t eerotal/restic-docker-swarm-server:latest .

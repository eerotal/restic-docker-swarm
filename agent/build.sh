#!/bin/sh

printf "[INFO] Building restic-docker-swarm-agent.\n"
docker build -t eerotal/restic-docker-swarm-agent:latest .

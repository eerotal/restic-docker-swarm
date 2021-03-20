REGISTRY ?= eerotal
TAG ?= $(shell git describe --tags --always --long --dirty)
IMAGES := agent server
IMAGE_TARGETS := $(addsuffix -image,$(IMAGES))

.PHONY: $(IMAGE_TARGETS) deploy-test rm-test logs-agent logs-server

all: $(IMAGE_TARGETS)

#
# Build targets.
#

$(IMAGE_TARGETS): %-image:
	docker build -t "$(REGISTRY)/restic-docker-swarm-$(*):$(TAG)" $(*)/

#
# Test targets.
#

deploy-test:
	docker stack deploy -c test/stack.yml restic

rm-test:
	docker stack rm restic

logs-agent:
	docker service logs restic_rds-agent

logs-server:
	docker service logs restic_rds-server

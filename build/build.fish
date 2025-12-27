#!/usr/bin/env fish
podman-compose -f build/compose.yaml build
podman-compose -f podman/compose.yaml down
podman-compose -f podman/compose.yaml up -d

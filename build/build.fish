#!/usr/bin/env fish

# Build ARM (local)
# podman build -t docker.io/sumarokovvp/simplelogic:royal_estate_arm -f build/Dockerfile .

# Build AMD64 (server) - cross-compile
podman build --no-cache --platform linux/amd64 -t docker.io/sumarokovvp/simplelogic:royal_estate_amd64 -f build/Dockerfile .

# Push AMD64 to registry
podman push docker.io/sumarokovvp/simplelogic:royal_estate_amd64

# Restart local
# podman-compose -f podman/compose.yaml down
# podman-compose -f podman/compose.yaml up -d

# Deploy to server
ssh royal_estate_odoo 'cd /opt/odoo/ && docker compose pull && docker compose down && docker compose up -d'

#!/usr/bin/env fish

# Определяем корень проекта (скрипт в build/, проект на уровень выше)
set PROJECT_ROOT (dirname (status filename))/..
set SSH_KEY $PROJECT_ROOT/.ssh/deploy_key
set SSH_OPTS -i $SSH_KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=no
set SERVER root@46.101.177.22

# Build ARM (local)
# podman build -t docker.io/sumarokovvp/simplelogic:estate_kit_arm -f build/Dockerfile .

# Build AMD64 (server) - cross-compile
podman build --no-cache --platform linux/amd64 -t docker.io/sumarokovvp/simplelogic:estate_kit_amd64 -f build/Dockerfile .

# Push AMD64 to registry
podman push docker.io/sumarokovvp/simplelogic:estate_kit_amd64

# Restart local
# podman-compose -f podman/compose.yaml down
# podman-compose -f podman/compose.yaml up -d

# Deploy to server
ssh $SSH_OPTS $SERVER 'cd /opt/odoo/ && docker compose pull && docker compose down && docker compose up -d'

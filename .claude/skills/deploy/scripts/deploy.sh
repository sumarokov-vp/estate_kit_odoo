#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd "$(git rev-parse --show-toplevel)"

# --- Загрузка .env ---
if [[ ! -f .env ]]; then
    echo -e "${RED}ERROR: .env not found. Copy .env.example to .env and fill in values.${NC}"
    exit 1
fi

set -a
source .env
set +a

# --- Проверка обязательных переменных ---
missing=()
[[ -z "${DEPLOY_SSH_KEY:-}" ]] && missing+=("DEPLOY_SSH_KEY")
[[ -z "${DEPLOY_USER:-}" ]] && missing+=("DEPLOY_USER")
[[ -z "${DEPLOY_HOST:-}" ]] && missing+=("DEPLOY_HOST")
[[ -z "${DEPLOY_IMAGE:-}" ]] && missing+=("DEPLOY_IMAGE")
[[ -z "${DEPLOY_SERVER_PATH:-}" ]] && missing+=("DEPLOY_SERVER_PATH")
[[ -z "${DEPLOY_CONTAINER:-}" ]] && missing+=("DEPLOY_CONTAINER")
[[ -z "${DEPLOY_DB_NAME:-}" ]] && missing+=("DEPLOY_DB_NAME")

if [[ ${#missing[@]} -gt 0 ]]; then
    echo -e "${RED}Missing required env variables in .env:${NC}"
    for var in "${missing[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

if [[ ! -f "$DEPLOY_SSH_KEY" ]]; then
    echo -e "${RED}ERROR: SSH key not found: $DEPLOY_SSH_KEY${NC}"
    exit 1
fi

SSH_OPTS=(-i "$DEPLOY_SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=no)
SSH_TARGET="$DEPLOY_USER@$DEPLOY_HOST"

# --- Получаем параметры БД с сервера ---
echo -e "${YELLOW}Fetching DB credentials from server...${NC}"
DB_PASSWORD=$(ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "grep '^DB_PASSWORD=' $DEPLOY_SERVER_PATH/.env" | cut -d= -f2-)
if [[ -z "$DB_PASSWORD" ]]; then
    echo -e "${RED}ERROR: Could not fetch DB_PASSWORD from server${NC}"
    exit 1
fi

DB_HOST=$(ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "grep '^DB_HOST=' $DEPLOY_SERVER_PATH/.env" | cut -d= -f2-)
DB_PORT=$(ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "grep '^DB_PORT=' $DEPLOY_SERVER_PATH/.env" | cut -d= -f2-)
DB_USER=$(ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "grep '^DB_USER=' $DEPLOY_SERVER_PATH/.env" | cut -d= -f2-)

echo -e "${GREEN}DB connection: $DB_USER@$DB_HOST:$DB_PORT/$DEPLOY_DB_NAME${NC}"

# --- 1. Сборка образа ---
echo -e "${YELLOW}Building Docker image (AMD64)...${NC}"
docker build --no-cache --platform linux/amd64 \
    -t "$DEPLOY_IMAGE" \
    -f build/Dockerfile .

# --- 2. Push в registry ---
echo -e "${YELLOW}Pushing image to registry...${NC}"
docker push "$DEPLOY_IMAGE"

# --- 3. Деплой на сервер ---
echo -e "${YELLOW}Deploying on server...${NC}"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
    "cd $DEPLOY_SERVER_PATH && docker compose pull && docker compose down && docker compose up -d"

# --- 4. Обновление модуля ---
echo -e "${YELLOW}Updating estate_kit module...${NC}"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
    "docker exec $DEPLOY_CONTAINER odoo \
        --db_host=$DB_HOST --db_port=$DB_PORT \
        --db_user=$DB_USER --db_password=$DB_PASSWORD \
        -d $DEPLOY_DB_NAME -u estate_kit --stop-after-init"

# --- 5. Перезапуск Odoo ---
echo -e "${YELLOW}Restarting Odoo...${NC}"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
    "cd $DEPLOY_SERVER_PATH && docker compose restart odoo"

# --- 6. Проверка логов ---
echo -e "${YELLOW}Checking logs...${NC}"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
    "docker logs --tail 20 $DEPLOY_CONTAINER"

echo ""
echo -e "${GREEN}Deploy complete! Site: https://royalestate.smartist.dev/${NC}"

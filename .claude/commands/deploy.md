Выполни деплой Estate Kit на продакшн сервер.

## Шаги

### 1. Сборка образа
```bash
docker build --no-cache --platform linux/amd64 \
  -t docker.io/sumarokovvp/simplelogic:estate_kit_amd64 \
  -f build/Dockerfile .
```

### 2. Push в registry
```bash
docker push docker.io/sumarokovvp/simplelogic:estate_kit_amd64
```

Если ошибка авторизации — попроси пользователя выполнить `docker login -u sumarokovvp`.

### 3. Деплой на сервер
```bash
ssh -i .ssh/deploy_key -o IdentitiesOnly=yes -o StrictHostKeyChecking=no \
  root@46.101.177.22 \
  'cd /opt/odoo/ && docker compose pull && docker compose down && docker compose up -d'
```

### 4. Обновление модуля estate_kit
```bash
ssh -i .ssh/deploy_key -o IdentitiesOnly=yes root@46.101.177.22 \
  "docker exec odoo-odoo-1 odoo \
    --db_host=10.114.0.2 --db_port=5432 \
    --db_user=odoo --db_password=AV0P2q4nFh0mUZ05XQ41f \
    -d royal_estate -u estate_kit --stop-after-init"
```

### 5. Перезапуск Odoo
```bash
ssh -i .ssh/deploy_key -o IdentitiesOnly=yes root@46.101.177.22 \
  'cd /opt/odoo && docker compose restart odoo'
```

### 6. Проверка
Проверь логи:
```bash
ssh -i .ssh/deploy_key -o IdentitiesOnly=yes root@46.101.177.22 \
  'docker logs --tail 20 odoo-odoo-1'
```

Сайт: https://royalestate.smartist.dev/

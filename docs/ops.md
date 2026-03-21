# Ops guide: API/бот

## Логирование (единый формат)

Приложение пишет логи в формате:

`timestamp level module request_id=<id> ip=<ip> message`

Пример:

`2026-03-21T12:34:56+0000 INFO app.api.http_handlers request_id=abc ip=127.0.0.1 Feed API server started`

### Переменные окружения для логов

- `LOG_LEVEL` — уровень логирования (по умолчанию `INFO`).
- `LOG_FILE` — путь к файлу логов. Если не задано, логирование только в stdout/stderr.
- `LOG_MAX_BYTES` — размер файла до ротации (по умолчанию `10485760`, 10 MB).
- `LOG_BACKUP_COUNT` — количество ротационных файлов (по умолчанию `5`).

## Health-check

Endpoint API:

- `GET /health`

Возвращает:

- `200` и `{"status":"ok","process":"ok","database":"ok"}` если процесс жив и БД доступна.
- `503` и `{"status":"degraded","process":"ok","database":"unavailable"}` если БД недоступна.

## Запуск через systemd

Пример unit-файла для API (`/etc/systemd/system/bazardrive-api.service`):

```ini
[Unit]
Description=BazarDrive Feed API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/bazardrive
Environment=BAZAR_DB_PATH=/var/lib/bazardrive/bot.db
Environment=LOG_LEVEL=INFO
Environment=LOG_FILE=/var/log/bazardrive/api.log
Environment=LOG_MAX_BYTES=10485760
Environment=LOG_BACKUP_COUNT=5
ExecStart=/opt/bazardrive/.venv/bin/python run_api.py
Restart=always
RestartSec=3
User=bazardrive
Group=bazardrive

[Install]
WantedBy=multi-user.target
```

Пример unit-файла для бота (`/etc/systemd/system/bazardrive-bot.service`):

```ini
[Unit]
Description=BazarDrive Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/bazardrive
Environment=BAZAR_DB_PATH=/var/lib/bazardrive/bot.db
Environment=LOG_LEVEL=INFO
Environment=LOG_FILE=/var/log/bazardrive/bot.log
Environment=LOG_MAX_BYTES=10485760
Environment=LOG_BACKUP_COUNT=5
ExecStart=/opt/bazardrive/.venv/bin/python run_bot.py
Restart=always
RestartSec=3
User=bazardrive
Group=bazardrive

[Install]
WantedBy=multi-user.target
```

Команды управления:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bazardrive-api bazardrive-bot
sudo systemctl status bazardrive-api
sudo systemctl status bazardrive-bot
```

# Contributing to BazarDrive

Спасибо за вклад в BazarDrive. Этот документ описывает **общие правила участия в проекте**, а не только отдельный Epic или UI-срез.

Используйте его как базовый guide для:
- локального запуска,
- изменения frontend / backend / bot / docs,
- оформления issues и pull requests,
- работы с миграциями и тестами,
- соблюдения scope и обратной совместимости.

---

## 1. Что входит в проект

BazarDrive состоит из нескольких связанных частей:

- **Web UI**: публичная лента, профиль, правила, документы;
- **HTTP API**: backend-обработчики и бизнес-логика;
- **Telegram bot**: пользовательские сценарии, модерация, статусы;
- **SQLite data layer**: repository + migrations;
- **Docs / QA / схемы**: спецификации, регрессии, FigJam/архитектура.

Каноничные entrypoints:
- `run_api.py`
- `run_bot.py`

Legacy aliases поддерживаются для совместимости, но новые изменения нужно ориентировать на каноничные точки входа.

---

## 2. Базовые принципы contribution

1. **Держите изменения в scope.**
   - Не смешивайте в одном PR unrelated refactor, UI polishing, API changes и docs cleanup без необходимости.
   - Если задача расползается, разбейте её на отдельные issues/PRs.

2. **Сохраняйте обратную совместимость**, если специально не согласовано обратное.
   - Не ломайте существующие entrypoints.
   - Не переименовывайте уже применённые миграции.
   - Не переносите frontend-файлы и test paths без отдельного scope.

3. **Сначала минимально рабочее решение, потом polish.**
   - Сначала correctness и интеграция.
   - Потом UX, naming cleanup, visual refinement.

4. **Документируйте архитектурно значимые изменения.**
   - Если меняется поток ролей, API-контракт, схема данных, moderation flow или compliance logic, обновите docs.

---

## 3. Настройка локальной среды

### Требования
- Python 3.x
- Git
- SQLite
- Telegram bot token для bot-части

### Переменные окружения

Создайте `.env` в корне проекта. Базовый пример:

```env
BOT_TOKEN=123456:your_real_token
ADMIN_CHAT_ID=-1001234567890
GROUP_CHAT_ID=-1009876543210
ADMIN_IDS=123456789,987654321

FEED_API_HOST=0.0.0.0
FEED_API_PORT=8001
BAZAR_DB_PATH=bot.db
FEED_UPLOAD_DIR=storage/feed_images

APP_ENV=dev
```

Если вы работаете только с frontend/API без Telegram, `BOT_TOKEN` можно временно не использовать, но для полного сценария bot он обязателен.

## 4. Локальный запуск

### Запуск API

`python3 -c "from app.db.migrator import apply_migrations; apply_migrations('bot.db')"`
`FEED_API_HOST=0.0.0.0 FEED_API_PORT=8001 python3 run_api.py`

### Запуск статического frontend

`python3 -m http.server 8000 --bind 0.0.0.0`

После этого откройте:
`http://localhost:8000/public/guest_feed.html`

### Запуск Telegram bot

`python3 run_bot.py`

## 5. Работа с базой данных и миграциями

### Применение миграций

`python3 -c "from app.db.migrator import apply_migrations; apply_migrations('bot.db')"`

### Правила миграций

- Не переименовывайте уже применённые migration files.
- Не меняйте исторические имена миграций задним числом.
- Новые миграции должны иметь новый уникальный префикс.
- Перед PR убедитесь, что миграции применяются на чистой БД.

### Чего нельзя делать

- Ломать `schema_migrations.version` логикой rename-переезда.
- Подменять applied migration другим файлом с тем же именем.

## 6. Работа с frontend

Основной frontend-файл проекта сейчас:
- `public/guest_feed.html`

Связанные пути:
- `web/js/**`
- `web/css/**`
- `public/web/**` (если используется текущим scope/test-слоем)

### Правила для frontend PR

- Не переносите frontend-файлы между директориями без отдельного scope.
- Не ломайте существующие test assumptions по путям.
- Если меняете навигацию, вкладки, публикацию, документы, роль-экран или mobile UX:
  - проверьте desktop/mobile сценарии,
  - проверьте отсутствие поломки доступности базового уровня,
  - обновите docs, если flow реально изменился.

Для UI-изменений особенно важно:
- состояние `default / hover / active / disabled / loading`,
- читаемость контраста,
- сохранение понятных ошибок и inline validation,
- отсутствие магических визуальных изменений вне scope задачи.

## 7. Работа с backend / API

Основная transport layer логика находится в:
- `app/api/http_handlers.py`

Бизнес-логика распределена по services:
- `app/services/**`

Data access layer:
- `app/db/repository.py`

### Правила для backend PR

- Не тащите бизнес-логику в transport layer, если её можно вынести в service.
- Не дублируйте guard/compliance/summary логику между API и Telegram bot.
- Все новые endpoint-ы должны иметь:
  - понятную валидацию,
  - предсказуемые коды ответа,
  - совместимый payload,
  - тест или хотя бы smoke-проверку.

Для API-изменений желательно:
- обновить docs/openapi или смежную документацию,
- проверить backward compatibility,
- зафиксировать новые поля/статусы в docs.

## 8. Работа с Telegram bot

Основной bot flow:
- `app/bot/handlers.py`

Дополнительные bot-модули:
- `app/bot/**`

### Правила для bot PR

- Не дублируйте routing и callback handlers.
- Не раздувайте `handlers.py`, если функциональность можно вынести в отдельный модуль.
- Если меняется UX статусов или moderation flow:
  - проверьте, что сообщения не спамят чат без необходимости,
  - предпочитайте обновление/refresh сообщения, если это подходит сценарию,
  - следите за совместимостью callback data.

## 9. Работа с docs, схемами и архитектурой

В BazarDrive документация является частью разработки, а не постфактум приложением.

Обновляйте docs, если меняются:
- роли и permission model,
- driver compliance flow,
- documents / waybill / summary / reminders,
- navigation / profile tabs / publish flow,
- moderation architecture,
- Users API / RBAC / security boundaries.

Если вы сделали новую архитектурную схему, желательно:
- положить рядом markdown summary,
- связать схему с issue/epic,
- избегать расхождения между схемой и реальным кодом.

## 10. Тесты и проверка изменений

### Полный прогон тестов

`python -m unittest discover -s tests -p "test_*.py" -v`

### Примеры точечного запуска

`BAZAR_DB_PATH=/tmp/bazardrive-test.db python -m unittest tests.test_db_guest_feed -v`
`python3 -m pytest tests/test_driver_reminder_service.py -v`
`python3 -m pytest tests/test_driver_scoring_service.py -v`

### Минимум перед PR

- проект запускается локально,
- миграции применяются,
- изменённый сценарий проходит smoke-проверку,
- relevant tests обновлены или добавлены,
- если тестов нет, это явно указано в PR.

## 11. Git / branch / PR conventions

### Branch naming

Рекомендуемый стиль:
- `feature/<short-name>`
- `fix/<short-name>`
- `docs/<short-name>`
- `refactor/<short-name>`
- `chore/<short-name>`

Примеры:
- `feature/driver-summary-card`
- `fix/waybill-close-validation`
- `docs/permissions-matrix`

### Commit messages

Предпочтительно коротко и по делу:
- `Add driver reminders service`
- `Fix order journal filtering`
- `Update contributing guide`

### PR expectations

В описании PR желательно указать:
- что именно изменено,
- зачем это нужно,
- какие файлы/слои затронуты,
- как это проверялось,
- какие риски/ограничения остались.

## 12. Работа с issues / epics

### Для обычных задач

- Держите связь между issue и PR.
- Если PR закрывает issue полностью, используйте `Closes #<id>`.
- Если это промежуточный кусок, лучше использовать `Part of #<id>`.

### Для Epic-ов

- Не закрывайте Epic первым же промежуточным PR.
- Старайтесь держать product-task и tech-task связь прозрачной.
- При больших изменениях полезно оставлять status comment:
  - что реализовано,
  - что ещё осталось,
  - какие зависимости появились.

## 13. Scope guardrails

Следующие типы изменений лучше не смешивать в одном PR без явной причины:
- redesign UI,
- перенос frontend-структуры,
- migration strategy changes,
- refactor repository/API/bot одновременно,
- массовая rename/cleanup без функциональной задачи,
- unrelated docs rewrite.

Если это всё-таки нужно, опишите это явно в PR и в issue.

## 14. Security и права доступа

Для изменений, затрагивающих users/roles/moderation/compliance:
- придерживайтесь явной RBAC-модели;
- не давайте moderator-права admin-уровня по умолчанию;
- критичные действия должны быть audit-friendly;
- guard/compliance ограничения должны применяться консистентно между web, API и bot.

Если вы меняете permission model, обновите:
- docs по ролям,
- permissions matrix,
- соответствующие схемы.

## 15. Когда нужно обновлять этот файл

Обновляйте `docs/contributing.md`, если меняется:
- способ локального запуска,
- каноничная структура проекта,
- политика PR/issue linkage,
- правила миграций,
- contribution protocol для основных слоёв проекта.

## 16. Полезные связанные файлы

- `README.md`
- `docs/security/permissions_matrix.md`
- `docs/driver_profile_wireframe_spec.md`
- `docs/feed_navigation_publish_flow.md`
- `docs/openapi.yaml`
- `docs/issues/**`
- `tests/**`

## 17. Краткий checklist перед merge

- [ ] Изменение находится в scope задачи
- [ ] Локальный запуск не сломан
- [ ] Миграции применяются корректно
- [ ] Тесты / smoke-check выполнены
- [ ] Docs обновлены при необходимости
- [ ] PR описывает что сделано и как проверено

BazarDrive развивается как связанная система из web + bot + API + data + docs. Хороший вклад сюда — это не только рабочий код, но и сохранённая целостность потока между этими слоями.

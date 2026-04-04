# BazarDrive

## Configuration

Создайте файл `.env` в корне проекта (можно взять за основу `.env.example`).
Загрузка env-переменных централизована в `app/config.py` и используется как API, так и Telegram-ботом.

| Переменная | Обязательно | Значение по умолчанию | Описание |
| --- | --- | --- | --- |
| `BOT_TOKEN` | Да | — | Токен Telegram-бота (BotFather). |
| `ADMIN_CHAT_ID` | Да | — | ID админ-чата для модерации (целое число). |
| `GROUP_CHAT_ID` | Да | — | ID группы/канала для публикации одобренного контента (целое число). |
| `ADMIN_IDS` | Нет | пусто | Список Telegram user id через запятую с правом модерации. |
| `FEED_API_HOST` | Нет | `0.0.0.0` | Хост для запуска Feed API. |
| `FEED_API_PORT` | Нет | `8001` | Порт для запуска Feed API (целое число). |
| `BAZAR_DB_PATH` | Нет | `bot.db` | Путь до SQLite-файла базы данных. |
| `FEED_UPLOAD_DIR` | Нет | `storage/feed_images` | Директория для сохранения изображений гостевой ленты. |
| `APP_ENV` | Нет | `dev` | Режим API: `dev` или `prod`. В `prod` включаются строгие CORS/auth-правила для write-методов. |
| `CORS_ALLOWED_ORIGINS` | Нет | пусто | Список origin через запятую для `prod` (например, `https://app.example.com,https://admin.example.com`). `*` в `prod` запрещён. |
| `API_AUTH_KEYS` | Нет | пусто | Список валидных API-ключей для write-endpoints в `prod` (`X-API-Key`). |
| `API_AUTH_BEARER_TOKENS` | Нет | пусто | Список bearer-токенов для write-endpoints в `prod` (`Authorization: Bearer <token>`). |
| `MODERATOR_API_KEYS` | Нет | пусто | Список API-ключей модераторов в `prod`: дают write-auth и право изменять/удалять любые посты/комментарии. |
| `MODERATOR_BEARER_TOKENS` | Нет | пусто | Список bearer-токенов модераторов в `prod` с теми же правами override. |

## Хранение изображений в гостевой ленте

Выбрана модель **файл на диске + ссылка в БД** (вариант 1).

### Ограничения и правила
- **Максимальный размер файла:** `3 MB` (`3 * 1024 * 1024` байт).
- **Допустимые форматы:** `image/jpeg`, `image/png`, `image/webp`.
- **Место хранения файлов:** директория `storage/feed_images` (можно переопределить через переменную окружения `FEED_UPLOAD_DIR`).
- **Что хранится в БД:** поле `image_url` с относительной ссылкой вида `/uploads/feed/<uuid>.<ext>`.
- **BLOB в SQLite:** не используется (допускается только для малых нагрузок, но в этом проекте отключён как основной способ).

### Безопасность хранения
- Файлы сохраняются только в выделенную директорию с правами `0700`.
- Имена файлов генерируются сервером (`UUID` + расширение по MIME-типу), оригинальные имена клиента не используются.
- Реализована защита от path traversal при чтении файлов: путь нормализуется и проверяется, что он остаётся внутри `FEED_UPLOAD_DIR`.

## APP_ENV режимы для CORS и write-auth

Ниже — явное разделение поведения для локальной разработки и production.
Источник фактического runtime-поведения: `FeedAPIHandler._with_error_handling` и `FeedAPIHandler._resolve_write_auth_context` в `app/api/http_handlers.py`.

### `APP_ENV=dev` (по умолчанию)

- Режим для локальной разработки и быстрого smoke-тестирования.
- CORS permissive: API отвечает с `Access-Control-Allow-Origin: *`.
- Write-endpoints (`POST/PATCH/DELETE`) проходят без обязательных API-ключей/токенов transport-уровня.

### `APP_ENV=prod`

- CORS работает через allowlist `CORS_ALLOWED_ORIGINS`.
  - Любой `Origin`, которого нет в allowlist, блокируется с `403 forbidden_origin`.
  - `*` в `CORS_ALLOWED_ORIGINS` запрещён.
- Для write-endpoints (`POST/PATCH/DELETE`) обязательны валидные credentials:
  - `X-API-Key` из `API_AUTH_KEYS`, или
  - `Authorization: Bearer <token>` из `API_AUTH_BEARER_TOKENS`, или
  - moderator-варианты из `MODERATOR_API_KEYS` / `MODERATOR_BEARER_TOKENS` (если нужны права модератора).
- При отсутствии настроенных write-кредов в окружении **или** при невалидных входящих кредах write-запрос блокируется с `401 unauthorized`.
- Дополнительно для PATCH/DELETE постов и комментариев действует object-level авторизация:
  - автор может изменять/удалять только свои сущности;
  - модераторские ключи/токены могут делать override.
- Ошибки содержат `request_id` для трассировки.

### Минимум для `prod` (чеклист)

- [ ] Установить `APP_ENV=prod`.
- [ ] Заполнить `CORS_ALLOWED_ORIGINS` реальными origin frontend/admin.
- [ ] Задать минимум один write credential:
  - [ ] `API_AUTH_KEYS` и/или `API_AUTH_BEARER_TOKENS`.
- [ ] Если нужен moderator override — заполнить `MODERATOR_API_KEYS` и/или `MODERATOR_BEARER_TOKENS`.
- [ ] Проверить, что write без валидных кредов возвращает `401`, а запрещённый origin — `403`.

Пример минимального `.env` для `prod`:

```env
APP_ENV=prod
CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
API_AUTH_KEYS=prod-write-key-1,prod-write-key-2
API_AUTH_BEARER_TOKENS=prod-write-token-1
MODERATOR_API_KEYS=prod-moderator-key-1
MODERATOR_BEARER_TOKENS=prod-moderator-token-1
```

### Бэкап и очистка
- **Бэкап:** включайте директорию `storage/feed_images` в регулярные бэкапы вместе с `bot.db`, иначе ссылки в БД станут «битые».
- **Очистка:** периодически удаляйте неиспользуемые файлы (без ссылок в `guest_feed_posts.image_url`) отдельным maintenance-скриптом/cron-задачей.

## Гостевая HTML-лента

В репозиторий добавлена отдельная страница `public/guest_feed.html`.

### Что умеет
- Добавлять посты гостей через backend API (`POST /api/feed/posts`).
- Прикреплять к посту одно изображение (JPEG/PNG/WEBP, до 3 МБ) через JSON-поля `image_base64` + `image_mime_type`.
- Сохранять профиль гостя с ролью `guest_author` через backend API (`POST /api/feed/profiles`).
- Загружать посты через backend API (`GET /api/feed/posts`).
- Редактировать посты через модальное окно и backend API (`PATCH /api/feed/posts/{id}`).
- Получать общую модерируемую ленту одобренных постов/объявлений (`GET /api/feed/approved`).
- Получать структурированные правила публикации для UI (`GET /api/feed/publication-rules`).
- Хранить в `localStorage` только UI-настройки (поиск/сортировка/фильтры/page size) и профиль.
- Искать по имени и тексту.
- Фильтровать "только с лайками".
- Сортировать (новые/старые).
- Разбивать список на страницы (5/10/20 постов).
- Показывать отметку времени последнего редактирования поста (`updated_at`), если пост изменён.
- Переключаться между основными разделами через нижнее меню: Лента / Профиль / Правила.
- Редактировать профиль пользователя (имя/email/аватар/о себе) с локальным сохранением.
- Валидировать гостевой профиль перед публикацией (обязательны имя и один контакт: email или телефон).
- Если профиль невалиден при попытке публикации, автоматически перенаправлять пользователя в «Профиль» → «Документы» и сохранять черновик поста.
- После успешного сохранения профиля автоматически возвращать пользователя в «Ленту» и продолжать отложенную публикацию.
- При ответе API `429 Too Many Requests` показывать пользователю время ожидания (`retry_after` / `Retry-After`) без потери черновика.
- При нарушении контент-правил (запрещённые темы, спам или избыток ссылок) показывать понятную ошибку API рядом с формой публикации.
- Показывать единые in-app уведомления (toast) для успешных действий и ошибок вместо системных `alert`.
- Автоматически проверять профиль при переходе в пункт меню "Профиль".
- Использовать вкладки профиля по спецификации docs: **Обзор, Такси / ИП, Документы, Выплаты, Безопасность** (всего 5 вкладок).
- На вкладке «Документы» показывать кнопку **«Добавить документ»** с формой создания и валидацией полей.
- После успешного добавления документа обновлять список документов без перезагрузки страницы.
- В блоке статуса профиля показывать trust-сигналы (`profileVerificationBadge`, `profileTrustBadge`) на базе `verification_state`/`is_verified` для будущего расширения trust badges.
- Структура и порядок вкладок в интерфейсе должны совпадать с `docs/driver_profile_wireframe_spec.md`.
- Основной источник UI-решений по профилю/меню: секция [«Источник дизайна (Figma)»](docs/driver_profile_wireframe_spec.md#2-источник-дизайна-figma) в `docs/driver_profile_wireframe_spec.md`.
- Применять горизонтальную прокрутку вкладок профиля на мобильных экранах без перезагрузки страницы.
- Показывать пошаговые правила публикации рядом с формой создания поста.
- Использовать объединённый раздел «Правила и документы» в отдельной вкладке (правила платформы, публикации и шаблоны документов).

### Правила и документы
- Вкладка «Правила» объединяет правила платформы, краткие правила публикации и список шаблонов документов.
- На вкладке «Лента» дублируется подробный пошаговый блок «Как публиковать посты (пошагово)» для быстрого доступа перед отправкой поста.
- Для ручной мобильной проверки UX + accessibility используйте чеклист `docs/qa/rules_mobile_a11y_checklist.md`.
- Карта навигации для сценария `Лента → Профиль → Одобренное`: `docs/feed_navigation_flow.md`.
- Карта переходов между «Лента/Правила/Профиль» и тест-кейсы публикации описаны в `docs/feed_navigation_publish_flow.md`.
- OpenAPI-контракт по ленте: `docs/openapi.yaml`.
- QA-набор (smoke + регрессия): `docs/qa/feed_qa_regression.md`.
- CSV для импорта QA-кейсов в тест-менеджер: `docs/qa/feed_qa_cases.csv`.
- План автоматизации и декомпозиции по эпику #172: `docs/issues/172-documents-trust-automation-plan.md`.
- Архив постановки по загрузке фото в ленту: `docs/issues/upload_photo_issue.md`.


### Миграции базы данных

Перед запуском API/бота можно явно применить миграции:

```bash
python3 -c "from app.db.migrator import apply_migrations; apply_migrations('bot.db')"
```

В CI/деплое добавьте отдельный шаг перед запуском приложения:

```bash
# пример для CI/CD pipeline
python3 -c "from app.db.migrator import apply_migrations; apply_migrations('bot.db')"
python3 run_api.py
```

Правила нумерации миграций:
- не переименовывайте уже применённые миграции;
- если есть исторические совпадения по префиксу (в проекте уже есть две миграции `006_*.sql`), оставляйте их как есть;
- для новых миграций используйте следующий свободный уникальный префикс (`010_*`, `011_*`, ...).

Почему это важно:
- мигратор применяет файлы в порядке сортировки имён (`sorted(...)`);
- в `schema_migrations.version` сохраняется имя файла миграции;
- переименование уже применённого файла на «живой» БД может привести к повторному применению SQL.

### Как запустить локально
1. Запустите API-сервер:

```bash
FEED_API_HOST=0.0.0.0 FEED_API_PORT=8001 python3 run_api.py
```

2. В отдельном терминале запустите статический сервер (с привязкой ко всем интерфейсам):

```bash
python3 -m http.server 8000 --bind 0.0.0.0
```

3. На текущем устройстве откройте `http://localhost:8000/public/guest_feed.html`.

4. Для запуска с другого устройства в той же сети откройте:

```text
http://<LAN-IP-ВАШЕГО-ПК>:8000/public/guest_feed.html
```

Если API находится на другом хосте/порту, можно передать его напрямую: `?apiBase=http://<host>:<port>`.
Пример: `http://192.168.1.50:8000/public/guest_feed.html?apiBase=http://192.168.1.50:8001`.

#### CSP для `guest_feed.html` (dev/prod)

- В `public/guest_feed.html` оставлен базовый безопасный CSP через `<meta>` с локальными dev-origin (`localhost/127.0.0.1:8001`) для сценария запуска через `python3 -m http.server`.
- Для запуска через API-сервер (`run_api.py`) заголовок `Content-Security-Policy` для `/public/guest_feed.html` формируется из env:
  - `GUEST_FEED_CSP_CONNECT_SRC_DEV`, `GUEST_FEED_CSP_IMG_SRC_DEV`
  - `GUEST_FEED_CSP_CONNECT_SRC_PROD`, `GUEST_FEED_CSP_IMG_SRC_PROD`
- Пример для локального `apiBase`:

```bash
APP_ENV=dev \
GUEST_FEED_CSP_CONNECT_SRC_DEV="'self' http://127.0.0.1:8001" \
GUEST_FEED_CSP_IMG_SRC_DEV="'self' data: https: http://127.0.0.1:8001" \
python3 run_api.py
```

### Этап 0: безопасные границы «быстрой чистки»

Чтобы упростить навигацию по проекту и не сломать текущий runtime/CI:
- каноничные точки запуска: `run_api.py` и `run_bot.py`;
- legacy-алиасы для обратной совместимости: `feed_api.py`, `bot.py`, `db.py`;
- пока сохраняем `public/guest_feed.html` и `public/web/**` в текущем месте, чтобы локальный запуск оставался прежним;
- тесты читают фронтенд-файлы по путям из корня (например, `tests/test_driver_tab_content_regression.py`, `tests/test_guest_feed_theme_contrast_guardrails.py`), поэтому перенос делать только отдельным PR с массовым обновлением тестов;
- скрипт доказательной съёмки `scripts/capture_guest_feed_evidence.py` также ожидает путь `/public/guest_feed.html`, поэтому перенос фронтенда в рамках «быстрой чистки" запрещён;
- применённые SQL-миграции не переименовываем: `schema_migrations.version` хранит имя файла миграции.

### Этап 0: безопасные границы «быстрой чистки»

Чтобы упростить навигацию по проекту и не сломать текущий runtime/CI:
- каноничные точки запуска: `run_api.py` и `run_bot.py`;
- legacy-алиасы для обратной совместимости: `feed_api.py`, `bot.py`, `db.py`;
- пока сохраняем `guest_feed.html` в корне и `web/**` в текущем месте, чтобы локальный запуск оставался прежним;
- тесты читают фронтенд-файлы по путям из корня (например, `tests/test_driver_tab_content_regression.py`, `tests/test_guest_feed_theme_contrast_guardrails.py`), поэтому перенос делать только отдельным PR с массовым обновлением тестов;
- скрипт доказательной съёмки `scripts/capture_guest_feed_evidence.py` также ожидает путь `/guest_feed.html`, поэтому перенос фронтенда в рамках «быстрой чистки" запрещён;
- применённые SQL-миграции не переименовываем: `schema_migrations.version` хранит имя файла миграции.

### Как добавить в ваш репозиторий (шаги)
Если вы переносите файл в другой проект:

```bash
cp public/guest_feed.html /path/to/your-repo/
cd /path/to/your-repo
git add public/guest_feed.html
git commit -m "Add guest feed HTML page with search, filters and pagination"
git push
```

Если нужно встроить страницу в существующий backend, можно отдавать этот файл как статический ресурс.


### Telegram bot
- Команда `/feed` отправляет последние одобренные публикации (посты + объявления) из таблиц модерации.
- В ленту попадают только записи со статусом `approved`.

#### Запуск Telegram-бота через `.env`
1. Создайте файл `.env` в корне проекта:

```env
BOT_TOKEN=123456:your_real_token
ADMIN_CHAT_ID=-1001234567890
GROUP_CHAT_ID=-1009876543210
ADMIN_IDS=123456789,987654321
```

2. Запустите бота:

```bash
python3 run_bot.py
```

`run_bot.py` и `run_api.py` автоматически подхватывают `.env`, поэтому дополнительно делать `export` не нужно.


## Новая структура проекта

```text
app/
  api/http_handlers.py        # HTTP-роутинг + сериализация ответов
  bot/handlers.py             # Telegram conversation/callback handlers
  db/repository.py            # SQL-операции и доступ к данным
  db/migrator.py              # запуск SQL-миграций и schema_migrations
  services/feed_service.py    # валидация и бизнес-логика API ленты
  services/moderation_service.py # бизнес-правила модерации
  models/                     # доменные константы и настройки
run_api.py                    # запуск API: python run_api.py
run_bot.py                    # запуск бота: python run_bot.py
migrations/                   # SQL-миграции (001_init.sql, 002_...sql, ...)
```

Совместимость со старыми точками входа (`feed_api.py`, `bot.py`, `db.py`) сохранена через прокси-импорты в новые модули.

### Точки входа: каноничные и legacy
- **Каноничные entrypoints:** `run_api.py`, `run_bot.py`.
- **Legacy aliases (backward compatibility):** `feed_api.py`, `bot.py`, `db.py`.
- Для новой документации, скриптов и инструкций используйте каноничные entrypoints.

## Спецификация профиля водителя такси (ИП, УСН «Доходы»)

Для frontend-проработки добавлены материалы по wireframe, компонентной схеме и сценарию входа водителя:

- `docs/driver_profile_wireframe_spec.md` — текстовая спецификация layout, состояний, событий и адаптива.
- `docs/driver_onboarding_flow.md` — пошаговый сценарий входа и онбординга водителя: первый вход, выбор роли, профиль, документы, верификация и блокеры выхода на линию.
- `docs/schemas/driver-profile/driver_profile_screen.schema.json` — JSON-схема экрана для проектирования компонентной архитектуры.
- `docs/schemas/driver-profile/driver_profile.types.ts` — TypeScript-интерфейсы и union-типы для типизации payload экрана.

### Driver UX docs

Для driver UX в репозитории выделен отдельный набор документов:

- `docs/driver_master_ux_map.md` — единая master-карта UX водителя.
- `docs/driver_order_flow.md` — сценарий заказа глазами водителя.
- `docs/driver_shift_flow.md` — жизненный цикл смены водителя.
- `docs/driver_menu_map.md` — карта меню Telegram / Web.
- `docs/driver_figjam_links.md` — индекс актуальных FigJam-ссылок.
- `docs/driver_ui_assets_index.md` — единый индекс экранных карт, wireframes, mobile low-fi и UI copy assets.
- `docs/driver_profile_components_board.md` — board ключевых driver-компонентов: обязательные поля, документы, путевой лист, допуск, смена и активный заказ.
- `docs/driver_ui_kit.md` — compact skeleton UI-kit для driver domain: tokens, buttons, chips, banners, cards, domain components и responsive rules.

Рекомендуемый порядок чтения:
1. `docs/driver_master_ux_map.md`
2. `docs/driver_onboarding_flow.md`
3. `docs/driver_order_flow.md`
4. `docs/driver_shift_flow.md`
5. `docs/driver_menu_map.md`
6. `docs/driver_ui_assets_index.md`
7. `docs/driver_profile_components_board.md`
8. `docs/driver_ui_kit.md`


## Тесты

Для изоляции тестов используется отдельный временный SQLite-файл через переменную окружения `BAZAR_DB_PATH`.
В самих тестах файл создаётся автоматически, но при ручном запуске можно указать путь явно.

### Запуск всех тестов

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Пример ручного запуска с отдельной БД

```bash
BAZAR_DB_PATH=/tmp/bazardrive-test.db python -m unittest tests.test_db_guest_feed -v
```


### API документов водителя

Новые endpoint'ы для сценария add/list/update/delete документов профиля водителя:

- `GET /api/driver/documents?profile_id=driver-main` — список документов.
- `POST /api/driver/documents` — создать документ.
- `PATCH /api/driver/documents/{id}` — заменить/обновить документ.
- `DELETE /api/driver/documents/{id}` — удалить документ.

#### Кнопка «Добавить документ»: расположение и пользовательский сценарий

- **Где находится в интерфейсе:** вкладка профиля **«Документы»** (3-я вкладка из 5: Обзор → Такси / ИП → Документы → Выплаты → Безопасность), верхняя часть секции документов рядом с заголовком списка.
- **Что делает:** открывает форму добавления документа, отправляет `POST /api/driver/documents`, а после успешного ответа закрывает форму и обновляет список документов **без перезагрузки страницы**.
- **Краткий сценарий:**
  1. Пользователь открывает вкладку **«Документы»** и нажимает **«Добавить документ»**.
  2. Заполняет обязательные поля и нажимает «Сохранить» (форма уходит в состояние `loading`).
  3. При `201 Created` новый документ отображается в текущем списке без смены вкладки и без `reload`.
  4. При ошибке (`400/409/5xx/timeout`) форма остаётся открытой, inline-ошибки показываются у полей, пользователь может исправить данные и отправить повторно.

Пример payload для создания:

```json
{
  "profile_id": "driver-main",
  "type": "passport",
  "number": "4010 123456",
  "valid_until": "2030-12-31",
  "status": "uploaded"
}
```

Допустимые значения `status` в payload: `uploaded`, `open`, `closed`, `checking`, `approved`, `rejected`, `expired`.

Пример успешного ответа (`201 Created`) при создании:

```json
{
  "id": 15,
  "profile_id": "driver-main",
  "type": "passport",
  "number": "4010 123456",
  "valid_until": "2030-12-31",
  "file_url": null,
  "status": "uploaded",
  "created_at": "2026-03-22T10:15:30Z",
  "updated_at": "2026-03-22T10:15:30Z"
}
```

Пример ответа ошибки валидации:

```json
{
  "error": "validation_error",
  "fields": {
    "type": "Некорректный тип документа",
    "number": "Номер документа должен содержать минимум 3 символа"
  }
}
```

При попытке добавить дубликат документа (`profile_id + type + number`) API возвращает `409`:

```json
{
  "error": "duplicate_document",
  "message": "Документ с таким типом и номером уже существует",
  "fields": {
    "number": "Документ с таким номером уже добавлен"
  }
}
```

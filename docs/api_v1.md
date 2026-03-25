# BazarDrive Feed API v1

Этот документ фиксирует стабильный контракт между `guest_feed.html` и API v1.

- Base URL: `http://<host>:8001`
- Формат данных: `application/json; charset=utf-8` (если не указано иначе)
- Все timestamp-поля возвращаются в ISO 8601 UTC (например, `2026-03-21T11:45:00Z`)

## 1) `GET /api/feed/posts`

Возвращает список постов гостевой ленты.

### Query params
- `limit` (optional, integer): от `1` до `100`, по умолчанию `20`
- `offset` (optional, integer): `>= 0`, по умолчанию `0`

### Response `200`
```json
{
  "items": [
    {
      "id": 101,
      "author": "Алексей Петров",
      "text": "Ищу попутчиков на утро",
      "guest_profile_id": "guest-0f7d7b8a",
      "likes": 0,
      "image_url": "/uploads/feed/0f4c2e8a9f0a4e34b3f8d20f4e4ec42e.jpg",
      "created_at": "2026-03-21T11:45:00Z",
      "updated_at": "2026-03-21T11:45:00Z"
    }
  ],
  "limit": 20,
  "offset": 0,
  "total": 1
}
```

---

## 2) `POST /api/feed/posts`

Создаёт пост в гостевой ленте. Поддерживаются JSON и `multipart/form-data`.

### JSON payload (схема)
```json
{
  "author": "string, required, 2..40",
  "text": "string, required, 5..500",
  "image_url": "string, optional, http/https или /uploads/feed/*",
  "image_base64": "string, optional, base64 или data URL",
  "image_mime_type": "string, required только для image_base64 без data URL",
  "guest_profile": {
    "id": "string, required if object present, min length 8",
    "role": "guest_author | guest_reader",
    "display_name": "string, required, 2..60",
    "email": "string, optional, max 254",
    "phone": "string, optional, max 32",
    "about": "string, optional, max 400",
    "status": "active | blocked | pending_moderation",
    "is_verified": "boolean"
  }
}
```

### Пример JSON payload
```json
{
  "author": "Алексей Петров",
  "text": "Освободилось место в машине на 18:30",
  "guest_profile": {
    "id": "guest-0f7d7b8a",
    "role": "guest_author",
    "display_name": "Алексей Петров",
    "email": "alex@example.com",
    "phone": "+79990000000",
    "about": "Езжу по будням",
    "status": "active",
    "is_verified": false
  }
}
```

### Успешный ответ `201`
Возвращает созданный пост в том же формате, что элемент `items` из `GET /api/feed/posts`.

### Возможные ошибки
- `400 Bad Request` — ошибка валидации payload
- `413 Payload Too Large` — размер загружаемого изображения или всего payload превышает лимиты сервера
- `429 Too Many Requests` — превышен rate limit (возвращаются `retry_after` и заголовок `Retry-After`)
- `500 Internal Server Error`

### Примечание для `guest_feed.html` (текущий publish flow)
- В первом инкременте фронтенд отправляет изображение только через JSON-поля `image_base64` + `image_mime_type`.
- Поля `image_base64` и `image_mime_type` добавляются в payload только если выбран и прошёл локальную валидацию один файл изображения.
- Если файл не выбран, отправляется прежний text-only payload без image-полей.

#### Контент-ограничения и антиспам (дополнительно к схеме полей)
- Запрещён контент с упоминанием наркотиков, ставок/казино и `18+`.
- В одном посте допускается не более `2` URL (`http://`/`https://`).
- Публикации с чрезмерным повторением одинаковых слов отклоняются как спам.
- Для нарушений API возвращает `400` и человеко-понятный `error`.

---

## 3) `PATCH /api/feed/posts/{post_id}`

Обновляет существующий пост.

### Path param
- `post_id` — положительный integer

### JSON payload (схема)
```json
{
  "author": "string, required, 2..40",
  "text": "string, required, 5..500",
  "image_url": "string|null, optional",
  "image_base64": "string, optional",
  "image_mime_type": "string, optional",
  "guest_profile_id": "string, optional"
}
```

### Пример payload
```json
{
  "author": "Алексей Петров",
  "text": "Освободилось 2 места на 18:30",
  "image_url": "/uploads/feed/0f4c2e8a9f0a4e34b3f8d20f4e4ec42e.jpg",
  "guest_profile_id": "guest-0f7d7b8a"
}
```

### Успешный ответ `200`
Возвращает обновлённый пост (та же структура, что для `GET /api/feed/posts`).

### Возможные ошибки
- `400 Bad Request` — некорректный `post_id` или ошибка валидации payload
- `404 Not Found` — пост не найден
- `500 Internal Server Error`

---

## 4) `POST /api/feed/profiles`

Создаёт/обновляет гостевой профиль (upsert по `id`).

### JSON payload (схема)
```json
{
  "id": "string, required, min length 8",
  "role": "guest_author | guest_reader",
  "display_name": "string, required, 2..60",
  "email": "string, optional, max 254",
  "phone": "string, optional, max 32",
  "about": "string, optional, max 400",
  "status": "active | blocked | pending_moderation",
  "is_verified": "boolean"
}
```

### Пример payload
```json
{
  "id": "guest-0f7d7b8a",
  "role": "guest_author",
  "display_name": "Алексей Петров",
  "email": "alex@example.com",
  "phone": "+79990000000",
  "about": "Езжу по будням",
  "status": "active",
  "is_verified": false
}
```

### Успешный ответ `201`
```json
{
  "id": "guest-0f7d7b8a",
  "role": "guest_author",
  "display_name": "Алексей Петров",
  "email": "alex@example.com",
  "phone": "+79990000000",
  "about": "Езжу по будням",
  "is_verified": false,
  "status": "active",
  "created_at": "2026-03-21T11:40:00Z",
  "updated_at": "2026-03-21T11:40:00Z",
  "last_seen_at": "2026-03-21T11:40:00Z"
}
```

### Возможные ошибки
- `400 Bad Request` — ошибка валидации полей
- `500 Internal Server Error`

---

## 5) `GET /api/feed/approved`

Возвращает объединённую ленту одобренного контента (`post` + `ad`).

### Response `200`
```json
{
  "items": [
    {
      "kind": "post",
      "id": 77,
      "user_tg_id": 123456,
      "title": "",
      "text": "Подтверждённый пост",
      "status": "approved",
      "created_at": "2026-03-21T10:00:00Z"
    },
    {
      "kind": "ad",
      "id": 12,
      "user_tg_id": 789012,
      "title": "Скидка на мойку",
      "text": "-20% до конца недели",
      "status": "approved",
      "created_at": "2026-03-21T09:00:00Z"
    }
  ]
}
```

### Возможные ошибки
- `500 Internal Server Error`

---

## 6) `GET /uploads/feed/*`

Раздача загруженных изображений ленты.

- Поддерживаемые форматы: `jpg/jpeg`, `png`, `webp`
- Cache-Control: `public, max-age=86400`
- Пример: `GET /uploads/feed/0f4c2e8a9f0a4e34b3f8d20f4e4ec42e.jpg`

### Возможные ошибки
- `404 Not Found` — файл не найден

---

## 8) `GET /api/feed/publication-rules`

Возвращает структурированный список правил публикации для отображения в UI.

### Response `200`
```json
{
  "title": "Правила публикации в гостевой ленте",
  "version": 1,
  "rules": [
    {"id": "no-spam", "text": "Не публикуйте однотипные повторяющиеся сообщения и флуд."},
    {"id": "no-prohibited", "text": "Запрещены наркотики, ставки/казино и контент 18+."},
    {"id": "links-limit", "text": "Допускается не более 2 ссылок в одном посте."}
  ]
}
```

---

## 7) Единый формат ошибок

Текущая v1 возвращает ошибки в одном из двух форматов (историческое поведение):

### Вариант A
```json
{
  "error": "Текст ошибки"
}
```

### Вариант B (внутренние ошибки)
```json
{
  "error": {
    "code": "internal_error",
    "message": "Internal server error",
    "request_id": "..."
  }
}
```

Клиентам v1 рекомендуется поддерживать оба варианта.

---

## 8) Breaking changes policy (API v1)

Для v1 действует политика стабильности:

1. **Без ломки контракта в рамках v1**:
   - нельзя удалять существующие endpoints;
   - нельзя переименовывать существующие поля ответа;
   - нельзя сужать допустимые значения/ограничения так, чтобы валидные v1-запросы перестали работать.
2. **Разрешены только backward-compatible изменения**:
   - добавление новых optional-полей в ответы;
   - добавление новых endpoints;
   - расширение допустимых значений enum, если старые значения остаются валидными.
3. **Любые несовместимые изменения** только через новую версию API (например, v2).
4. **Депрекация**:
   - перед удалением функциональности в новой мажорной версии должно быть предупреждение в changelog и документации.

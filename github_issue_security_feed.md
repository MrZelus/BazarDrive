Title: [Security/Feed] Публикация постов: XSS в UI + усиление валидации и защиты API (CORS/auth/rate-limit)

Description:
В текущем контуре «гостевой ленты» пользовательский текст поста/автора отображается через `innerHTML` в `renderFeed()`, что делает возможной XSS-инъекцию (stored/DOM XSS). Дополнительно API принимает публикации без аутентификации и отдаёт CORS `*`, что делает write-эндпоинты доступными любому origin при сетевой доступности API.

Технические ссылки на код:
- Рендер постов/ментов: `web/js/feed.js`
- Серверный CORS и endpoints: `app/api/http_handlers.py`
- Правила публикации и rate limit: `app/services/feed_service.py`
- Publish-flow тест: `tests/test_feed_publish_profile_navigation_flow.py`

## Scope / Problem Statement
- **XSS:** `renderFeed()` и рендер документов/driver documents используют `innerHTML` и вставляют пользовательские поля без экранирования.
- **API security:** `Access-Control-Allow-Origin: *`, методы `POST/PATCH/DELETE` разрешены, auth отсутствует.
- **Rate limit:** есть `429 + Retry-After`, но нужно усилить защиту от слишком больших payload (DoS через `Content-Length`) и обеспечить стабильный UX для повторов.
- **Validation:** серверные правила публикации ориентированы на спам/слова/ссылки, но не предотвращают HTML-инъекции.

## Steps to Reproduce
1. Опубликовать пост с payload, содержащим HTML/JS (например, `<img src=x onerror=alert(1)>`).
2. Перезагрузить ленту.
3. Убедиться, что вредоносный код исполняется/HTML интерпретируется (в зависимости от браузера).

## Expected Behavior
- Пользовательский контент отображается как текст, не как HTML (никакой XSS).
- В `PROD`-режиме write-эндпоинты защищены (API key/токен), CORS ограничен whitelist.
- Сервер отсекает большие запросы ранним `413 Payload Too Large`.
- Rate limit остаётся понятным для пользователя (сообщение + `Retry-After`) и не теряет черновик.

## Actual Behavior
- Возможна интерпретация пользовательского контента как HTML (XSS).
- API открыт для вызовов из любого origin (CORS `*`), auth отсутствует.

## Suggested Fix
### Frontend
- Переписать рендер постов/документов на DOM-узлы с `textContent`; запретить `innerHTML` для пользовательских строк.
- Добавить CSP (минимум: запрет `inline-script`, запрет `data:`/`javascript:` где применимо).

### Backend
- Добавить `MAX_REQUEST_BYTES` (например, 5–8 MB) и отвечать `413` при превышении.
- Ввести `APP_ENV=dev|prod`:
  - `dev`: CORS `*` допустим;
  - `prod`: CORS whitelist и обязательный `X-API-Key` (или Bearer) на write-эндпоинты.

### Docs / Contract
- Привести `docs/openapi.yaml` к фактическим полям.

## Tests to Add / Update
- Новый тест: публикация поста с HTML payload не приводит к появлению HTML в DOM (регрессия XSS).
- Добавить в CI workflow:
  - `tests/test_feed_publish_profile_navigation_flow.py`
  - `tests/test_main_tabs_a11y.py`
  - `tests/test_feed_api_smoke_publish.py`
- Интеграционный тест на `413` при слишком большом `Content-Length`.

## Labels
`security`, `feed`, `frontend`, `backend`, `bug`, `priority:P0`

## Estimated effort
Medium (основной объём на безопасный рендер UI и режимы доступа API).

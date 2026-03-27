# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

BazarDrive is a Russian-language taxi/ride-sharing community platform with a Telegram bot, REST API backend (Python stdlib `http.server`), and a mobile-first HTML frontend (`guest_feed.html`). Uses SQLite for storage — no external database services needed.

### Running services for development

Two processes must be running:

1. **Feed API** (port 8001): `python3 run_api.py` (env vars `FEED_API_HOST=0.0.0.0 FEED_API_PORT=8001`)
2. **Static file server** (port 8000): `python3 -m http.server 8000 --bind 0.0.0.0`

Open the app at `http://localhost:8000/guest_feed.html?apiBase=http://localhost:8001`.

The API health check is at `GET /health` on port 8001.

### Database

SQLite file `bot.db` in project root. Migrations are in `migrations/` and auto-applied on API startup. To apply manually: `python3 -c "from app.db.migrator import apply_migrations; apply_migrations('bot.db')"`.

### Tests

Run all tests: `python3 -m pytest tests/ -v`

The CI workflow (`.github/workflows/ci-driver-tab.yml`) runs a subset of tests with pytest. All 85 tests pass as of initial setup.

### Linting

No dedicated linter config (no flake8/ruff/mypy config files). The codebase is pure Python + vanilla HTML/JS/CSS.

### Telegram bot

The bot (`run_bot.py`) requires `BOT_TOKEN`, `ADMIN_CHAT_ID`, and `GROUP_CHAT_ID` env vars. Without valid Telegram credentials it will not start — this is expected for local dev unless you have a test bot token.

### Gotchas

- Use `python3` not `python` — the VM may not have `python` aliased.
- The `.env` file is auto-loaded by both `run_api.py` and `run_bot.py` via `app/config.py` (no `python-dotenv` needed).
- `APP_ENV=dev` (default) allows all CORS origins and skips auth on write endpoints. Set `APP_ENV=prod` to test auth/CORS rules.
- The guest feed UI requires a valid guest profile (name + email or phone) before allowing post creation — publishing redirects to profile completion if missing.
- Canonical entrypoints for docs/scripts are `run_api.py` and `run_bot.py`; `feed_api.py`, `bot.py`, and `db.py` are legacy aliases kept for backward compatibility.
- Keep `guest_feed.html` in repository root and `web/**` paths stable unless you also update all path-sensitive tests/scripts in the same PR.
- Never rename already-applied SQL migration files; if historical duplicate prefixes exist (for example `006_*`), keep them unchanged and create new migrations with the next unique prefix.

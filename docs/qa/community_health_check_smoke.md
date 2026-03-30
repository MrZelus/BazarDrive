# Community Health Check Smoke Runbook

Этот runbook описывает, как вручную проверить workflow `Community Health Check` на успешный и негативный сценарий.

## Цель

Проверить, что автоматизация:
- проходит на валидном PR;
- падает на ожидаемом нарушении;
- показывает понятную ошибку в GitHub Checks.

## Что проверяет workflow

Workflow `community-health-check.yml` валидирует:
- наличие `CONTRIBUTING.md`;
- наличие `CODE_OF_CONDUCT.md`;
- наличие `.github/pull_request_template.md`;
- наличие директории `.github/ISSUE_TEMPLATE`;
- наличие `docs/contributing.md`;
- ссылку из `CONTRIBUTING.md` на `docs/contributing.md`.

## Сценарий A: успешный smoke test

1. Создайте временную ветку.
2. Внесите безопасное изменение в `CONTRIBUTING.md` без удаления ссылки на `docs/contributing.md`.
3. Откройте PR в `main`.
4. Убедитесь, что check `Community Health Check` прошёл успешно.

Пример:

```bash
git checkout -b test/community-health-pass
printf "\n" >> CONTRIBUTING.md
git add CONTRIBUTING.md
git commit -m "test: trigger community health check"
git push origin test/community-health-pass
```

Ожидаемый результат:
- workflow запускается;
- job завершается успешно;
- PR остаётся mergeable.

## Сценарий B: негативный smoke test

1. Создайте временную ветку.
2. Удалите ссылку на `docs/contributing.md` из `CONTRIBUTING.md`.
3. Откройте PR в `main`.
4. Убедитесь, что check падает на шаге consistency.

Пример:

```bash
git checkout -b test/community-health-fail
python3 - <<'PY'
from pathlib import Path
p = Path("CONTRIBUTING.md")
text = p.read_text(encoding="utf-8")
text = text.replace("- [docs/contributing.md](docs/contributing.md)\n", "")
p.write_text(text, encoding="utf-8")
PY
git add CONTRIBUTING.md
git commit -m "test: break contributing reference"
git push origin test/community-health-fail
```

Ожидаемый результат:
- workflow падает;
- ошибка содержит сообщение:

```text
CONTRIBUTING.md must reference docs/contributing.md
```

## Сценарий C: отсутствие обязательного файла

1. Создайте временную ветку.
2. Временно переименуйте `CODE_OF_CONDUCT.md`.
3. Откройте PR в `main`.
4. Убедитесь, что workflow падает на required files check.

Пример:

```bash
git checkout -b test/community-health-missing-file
git mv CODE_OF_CONDUCT.md CODE_OF_CONDUCT.tmp
git add CODE_OF_CONDUCT.md CODE_OF_CONDUCT.tmp
git commit -m "test: break required community file check"
git push origin test/community-health-missing-file
```

Ожидаемый результат:
- workflow падает;
- ошибка содержит сообщение:

```text
Missing CODE_OF_CONDUCT.md
```

## Где смотреть результат

В GitHub PR:
- вкладка **Checks**;
- job `Community Health Check`;
- шаги `Check required files` и `Check contributing consistency`.

## Что считать успешной проверкой

Автоматизация считается проверенной, если:
- валидный PR даёт зелёный check;
- намеренно сломанный PR даёт красный check по ожидаемой причине.

## После теста

Тестовые PR не нужно merge'ить.

Рекомендуется:
- закрыть тестовый PR;
- удалить тестовую ветку;
- не оставлять намеренно сломанные файлы в активных ветках.

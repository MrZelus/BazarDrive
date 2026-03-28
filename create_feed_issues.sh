#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# === Fixed for your repo ===
OWNER="MrZelus"
REPO="BazarDrive"
ASSIGNEE="MrZelus"
MILESTONE="Feed MVP"

# Optional: set project number if you use GitHub Project (v2)
PROJECT_NUM="1"

command -v gh >/dev/null || { echo "gh CLI not found"; exit 1; }
command -v jq >/dev/null || { echo "jq not found (pkg install jq)"; exit 1; }

gh repo set-default "$OWNER/$REPO" >/dev/null
gh repo view "$OWNER/$REPO" >/dev/null

ensure_label() {
  local name="$1" color="$2" desc="$3"
  if gh label list --repo "$OWNER/$REPO" --search "$name" --json name -q '.[].name' | grep -Fxq "$name"; then
    return 0
  fi
  gh label create "$name" --repo "$OWNER/$REPO" --color "$color" --description "$desc" >/dev/null || true
}

ensure_milestone() {
  if gh api "repos/$OWNER/$REPO/milestones" --paginate | jq -e --arg t "$MILESTONE" '.[] | select(.title==$t)' >/dev/null; then
    echo "Milestone exists: $MILESTONE"
  else
    gh api "repos/$OWNER/$REPO/milestones" \
      -f title="$MILESTONE" \
      -f description="MVP расширения гостевой ленты" \
      -f state="open" >/dev/null
    echo "Milestone created: $MILESTONE"
  fi
}

create_issue() {
  local title="$1"
  local labels_csv="$2"
  local body="$3"

  IFS=',' read -r -a labels_arr <<< "$labels_csv"
  local cmd=(gh issue create
    --repo "$OWNER/$REPO"
    --title "$title"
    --assignee "$ASSIGNEE"
    --milestone "$MILESTONE"
    --body "$body"
    --json url,number
    -q '{url:.url,number:.number}'
  )
  for lb in "${labels_arr[@]}"; do cmd+=(--label "$lb"); done
  "${cmd[@]}"
}

project_id() {
  gh api graphql -f query='
query($owner:String!, $num:Int!){
  user(login:$owner){ projectV2(number:$num){ id } }
  organization(login:$owner){ projectV2(number:$num){ id } }
}' -F owner="$OWNER" -F num="$PROJECT_NUM" \
  | jq -r '.data.user.projectV2.id // .data.organization.projectV2.id // empty'
}

issue_node_id() {
  local url="$1"
  gh api graphql -f query='
query($url:URI!){
  resource(url:$url){
    ... on Issue { id }
  }
}' -F url="$url" | jq -r '.data.resource.id'
}

add_to_project() {
  local pid="$1" iid="$2"
  gh api graphql -f query='
mutation($project:ID!, $content:ID!){
  addProjectV2ItemById(input:{projectId:$project, contentId:$content}) {
    item { id }
  }
}' -F project="$pid" -F content="$iid" >/dev/null
}

echo "Ensuring labels..."
ensure_label "enhancement" "a2eeef" "New feature or request"
ensure_label "backend" "5319e7" "Backend changes"
ensure_label "frontend" "1d76db" "Frontend/UI changes"
ensure_label "api" "0e8a16" "API contract/handlers"
ensure_label "security" "d73a4a" "Security related"
ensure_label "performance" "fbca04" "Performance related"

ensure_milestone

echo "Creating EPIC..."
EPIC=$(create_issue \
  "Epic: Расширение гостевой ленты публикаций" \
  "enhancement,backend,frontend,api" \
  "Цель: довести гостевую ленту до уровня соцфидов (комментарии, реакции, репосты, мультимедиа, производительность, безопасность).")
EPIC_URL=$(echo "$EPIC" | jq -r '.url')
EPIC_NUM=$(echo "$EPIC" | jq -r '.number')
echo "EPIC #$EPIC_NUM -> $EPIC_URL"

declare -a URLS
declare -a NUMS

mk() {
  local title="$1" labels="$2" text="$3"
  local out
  out=$(create_issue "$title" "$labels" "Связано с Epic: $EPIC_URL

$text")
  URLS+=("$(echo "$out" | jq -r '.url')")
  NUMS+=("$(echo "$out" | jq -r '.number')")
  echo "Issue #${NUMS[-1]} -> ${URLS[-1]}"
}

echo "Creating child issues..."
mk "Feed: CRUD комментариев к постам" \
   "enhancement,backend,frontend,api" \
   "Добавить таблицу guest_feed_comments, endpoint'ы GET/POST/PATCH/DELETE /api/feed/posts/{id}/comments, UI-блок комментариев, тесты и OpenAPI."

mk "Feed: серверные реакции (лайк/дизлайк/эмодзи)" \
   "enhancement,backend,frontend,api" \
   "Добавить хранение реакций в БД, endpoint'ы POST/DELETE react, агрегаты в выдаче постов, синхронизацию UI-кнопок, тесты."

mk "Feed: DELETE /api/feed/posts/{id} + проверка прав" \
   "enhancement,backend,api,security" \
   "Реализовать удаление поста, вернуть 404/403 по ситуации, добавить проверку автор/модератор, обновить OpenAPI и тесты."

mk "Feed: поддержка нескольких медиа-вложений (карусель)" \
   "enhancement,backend,frontend,api" \
   "Добавить модель вложений post_media (несколько изображений/видео), обновить create/update post, UI-карусель, валидацию форматов/размера, тесты."

mk "Feed: cursor pagination и infinite scroll" \
   "enhancement,backend,frontend,performance,api" \
   "Заменить offset-пагинацию на курсорную, добавить next_cursor в API, реализовать догрузку при скролле и skeleton UI."

mk "Feed: объектная авторизация (author/moderator)" \
   "security,backend,api" \
   "Для PATCH/DELETE постов и комментариев добавить проверку прав на уровне объекта: автор может свои записи, модератор — любые."

# Optional: add all to Project v2
PID=$(project_id || true)
if [[ -n "${PID:-}" ]]; then
  echo "Adding issues to Project v2 #$PROJECT_NUM..."
  add_to_project "$PID" "$(issue_node_id "$EPIC_URL")"
  for u in "${URLS[@]}"; do
    add_to_project "$PID" "$(issue_node_id "$u")"
  done
  echo "Added to project."
else
  echo "Project v2 #$PROJECT_NUM not found. Skipping project linking."
fi

echo
echo "DONE"
echo "EPIC: #$EPIC_NUM $EPIC_URL"
for i in "${!URLS[@]}"; do
  echo " - #${NUMS[$i]} ${URLS[$i]}"
done

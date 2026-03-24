import unittest
from pathlib import Path


class FeedActionButtonsA11yStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = Path("web/js/feed.js").read_text(encoding="utf-8")

    def test_busy_state_helper_is_used_for_long_running_actions(self) -> None:
        self.assertIn("function setButtonBusyState(button, isBusy, busyText = '', idleText = '') {", self.script)
        self.assertIn("button.setAttribute('aria-disabled', String(busy));", self.script)
        self.assertIn("button.setAttribute('aria-busy', String(busy));", self.script)
        self.assertIn("setButtonBusyState(publishBtn, true, 'Публикация...');", self.script)
        self.assertIn("setButtonBusyState(saveProfileBtn, true, 'Сохранение...');", self.script)
        self.assertIn("setButtonBusyState(submitDocumentBtn, isSubmittingDocument, 'Сохранение...', 'Сохранить');", self.script)

    def test_contextual_aria_labels_for_delete_and_comment_actions(self) -> None:
        self.assertIn("deleteButton.setAttribute('aria-label', `Удалить документ: ${String(item.title || 'Документ')}`);", self.script)
        self.assertIn("deletePostBtn.setAttribute('aria-label', `Удалить пост автора ${String(post.author || 'Гость')}`);", self.script)
        self.assertIn("editBtn.setAttribute('aria-label', `Редактировать комментарий от ${String(comment.author || 'автора')}`);", self.script)
        self.assertIn("deleteBtn.setAttribute('aria-label', `Удалить комментарий от ${String(comment.author || 'автора')}`);", self.script)
        self.assertIn("submit.setAttribute('aria-label', `Отправить комментарий к посту автора ${String(post.author || 'Гость')}`);", self.script)


if __name__ == "__main__":
    unittest.main()

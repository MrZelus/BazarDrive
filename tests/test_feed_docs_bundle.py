import unittest
from pathlib import Path


class FeedDocsBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.readme = Path('README.md').read_text(encoding='utf-8')
        self.openapi = Path('docs/openapi.yaml').read_text(encoding='utf-8')
        self.flow = Path('docs/feed_navigation_publish_flow.md').read_text(encoding='utf-8')
        self.navigation_flow = Path('docs/feed_navigation_flow.md').read_text(encoding='utf-8')
        self.qa = Path('docs/qa/feed_qa_regression.md').read_text(encoding='utf-8')
        self.qa_csv = Path('docs/qa/feed_qa_cases.csv').read_text(encoding='utf-8')

    def test_readme_contains_links_to_feed_docs_bundle(self) -> None:
        self.assertIn('docs/openapi.yaml', self.readme)
        self.assertIn('docs/feed_navigation_flow.md', self.readme)
        self.assertIn('docs/feed_navigation_publish_flow.md', self.readme)
        self.assertIn('docs/qa/feed_qa_regression.md', self.readme)
        self.assertIn('docs/qa/feed_qa_cases.csv', self.readme)

    def test_openapi_covers_core_feed_endpoints(self) -> None:
        self.assertIn('/api/feed/posts:', self.openapi)
        self.assertIn('/api/feed/profiles:', self.openapi)
        self.assertIn('/api/feed/posts/{id}/react:', self.openapi)
        self.assertIn('deprecated: true', self.openapi)
        self.assertIn('/api/feed/posts/{id}/reactions:', self.openapi)
        self.assertIn('summary: Поставить или заменить реакцию на пост', self.openapi)
        self.assertIn('name: q', self.openapi)
        self.assertIn('/api/feed/approved:', self.openapi)
        self.assertIn('/api/feed/publication-rules:', self.openapi)
        self.assertIn('/api/driver/documents:', self.openapi)

    def test_qa_doc_contains_smoke_and_regression_sections(self) -> None:
        self.assertIn('## 1) Smoke (быстрый прогон)', self.qa)
        self.assertIn('## 2) Регрессия (обязательный набор)', self.qa)
        self.assertIn('### Взаимодействия в ленте (реакции, комментарии, поиск)', self.qa)
        self.assertIn('publish -> moderation -> approved', self.qa)
        self.assertIn('## 3) Автотесты (локальный минимум)', self.qa)
        self.assertIn('## 5) BAZ-51 — процент прогресса и следующий шаг', self.qa)
        self.assertIn('**7/7 = 100%**', self.qa)

    def test_flow_doc_has_navigation_map_section(self) -> None:
        self.assertIn('## 1) Карта переходов между разделами', self.flow)
        self.assertIn('## 1) Карта навигации (основной сценарий)', self.navigation_flow)
        self.assertIn('flow_id,title,priority,component,preconditions,steps,expected_result', self.qa_csv)
        self.assertIn('FLW-007,Серверные реакции восстанавливаются после reload', self.qa_csv)
        self.assertIn('FLW-009,CRUD комментариев только для автора', self.qa_csv)
        self.assertIn('FLW-012,Infinite scroll/pagination без пропусков', self.qa_csv)


if __name__ == '__main__':
    unittest.main()

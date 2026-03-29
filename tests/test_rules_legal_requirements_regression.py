import re
import unittest
from pathlib import Path


class RulesLegalRequirementsRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = Path("public/web/js/feed.js").read_text(encoding="utf-8")

    def test_rules_docs_include_taxi_legal_requirements_card(self) -> None:
        self.assertIn("id: 'taxi-legal-requirements'", self.script)
        self.assertIn("title: 'Обязательные требования к водителю такси'", self.script)
        self.assertIn("description: 'Перечень данных и документов для законной работы по 580-ФЗ, подзаконным актам и правилам сервиса.'", self.script)
        self.assertIn("type: 'Регламент'", self.script)
        self.assertIn("'Личные данные и квалификация'", self.script)
        self.assertIn("'Сведения о предпринимателе (для ИП)'", self.script)
        self.assertIn("'Сведения об автомобиле'", self.script)
        self.assertIn("'Документы для поездок'", self.script)
        self.assertIn("'Журнал регистрации заказов'", self.script)
        self.assertIn("'Дополнительные данные'", self.script)
        self.assertIn("'ОСГОП — обязательное страхование ответственности перевозчика.'", self.script)
        self.assertIn("'Путевой лист с предсменным и послесменным медосмотром водителя (подпись медработника или ЭП).'", self.script)

    def test_rules_search_and_render_support_deep_legal_sections(self) -> None:
        self.assertIn("tokens.push(...doc.tags);", self.script)
        self.assertIn("tokens.push(...section.items);", self.script)
        self.assertIn("tokens.push(...section.orderedItems);", self.script)
        self.assertIn("const haystack = tokens", self.script)
        self.assertIn("detailsSummary.textContent = 'Показать перечень обязательных сведений';", self.script)
        self.assertRegex(
            self.script,
            re.compile(
                r"const filteredDocs = docs\.filter\(\(doc\) => \{[\s\S]+const haystack = tokens[\s\S]+if \(Array\.isArray\(doc\.sections\) && doc\.sections\.length\)\s*\{[\s\S]+const details = document\.createElement\('details'\);",
                re.MULTILINE,
            ),
        )

    def test_platform_rules_include_passenger_taxi_and_delivery_policy(self) -> None:
        self.assertIn("id: 'platform-rules'", self.script)
        self.assertIn("title: 'Правила заказа такси и доставки пассажиром'", self.script)
        self.assertIn("type: 'Регламент'", self.script)
        self.assertIn("'Создавая заказ в BazarDrive, пассажир подтверждает согласие с правилами платформы, условиями выполнения заказа и требованиями безопасности.'", self.script)
        self.assertIn("'Запрещено передавать предметы, запрещённые законом, включая оружие, наркотические средства, токсичные и взрывоопасные материалы.'", self.script)
        self.assertIn("'Частые отмены могут приводить к ограничениям, снижению приоритета и системным уведомлениям.'", self.script)
        self.assertIn("'Водитель может отказаться от заказа при ложных данных, отсутствии пассажира, угрозе безопасности или нарушении правил.'", self.script)
        self.assertIn("'🚕 BazarDrive — правила пассажира: указывайте точные адреса, выходите вовремя и заранее сообщайте о багаже, животных или особых условиях.'", self.script)
        self.assertIn("'Будьте вовремя, указывайте точные данные и не нарушайте правила — это влияет на доступ к заказам.'", self.script)


if __name__ == "__main__":
    unittest.main()

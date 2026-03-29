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

    def test_rules_docs_include_passenger_safe_order_tips_card(self) -> None:
        self.assertIn("id: 'passenger-safe-ordering-rules'", self.script)
        self.assertIn("title: 'Что пассажиру важно по закону при заказе такси (РФ)'", self.script)
        self.assertIn("type: 'Памятка'", self.script)
        self.assertIn("'пассажир'", self.script)
        self.assertIn("РФ", self.script)
        self.assertIn("'фз-580'", self.script)
        self.assertIn("'пдд'", self.script)
        self.assertIn("'Подавайте жалобы по цепочке: сначала в поддержку агрегатора или перевозчика, затем в уполномоченный орган по такси субъекта РФ, по потребительским нарушениям — в Роспотребнадзор, при угрозе безопасности — 112/полиция.',", self.script)


if __name__ == "__main__":
    unittest.main()

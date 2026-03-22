import json
import re
import unittest
from pathlib import Path


class DriverDocumentsContractSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.schema_path = self.repo_root / "docs" / "driver_profile_screen.schema.json"
        self.types_path = self.repo_root / "docs" / "driver_profile.types.ts"
        self.html_path = self.repo_root / "guest_feed.html"

    def _load_schema(self) -> dict:
        return json.loads(self.schema_path.read_text(encoding="utf-8"))

    def _parse_document_type_union(self) -> set[str]:
        source = self.types_path.read_text(encoding="utf-8")
        match = re.search(r"export type DocumentType\s*=\s*(.+?);", source, re.S)
        self.assertIsNotNone(match, "DocumentType union was not found in driver_profile.types.ts")
        values = set(re.findall(r"'([^']+)'", match.group(1)))
        self.assertGreater(len(values), 0, "DocumentType union should not be empty")
        return values

    def _parse_html_document_type_options(self) -> set[str]:
        html = self.html_path.read_text(encoding="utf-8")
        select_match = re.search(r'<select id="documentType"[^>]*>(.+?)</select>', html, re.S)
        self.assertIsNotNone(select_match, "documentType select was not found in guest_feed.html")
        options_block = select_match.group(1)
        values = {
            value
            for value in re.findall(r'<option value="([^"]*)">', options_block)
            if value
        }
        self.assertGreater(len(values), 0, "documentType select should include non-empty values")
        return values

    def test_schema_includes_add_document_action_and_events(self) -> None:
        schema = self._load_schema()
        tab_content = next(
            (section for section in schema["sections"] if section.get("id") == "tab_content"),
            None,
        )
        self.assertIsNotNone(tab_content, "Schema must include tab_content section")
        documents_actions = tab_content["tabSchemas"]["documents"]["actions"]
        add_document_action = next((action for action in documents_actions if action.get("id") == "add_document"), None)
        self.assertIsNotNone(add_document_action, "Schema documents.actions must include add_document")
        self.assertEqual(add_document_action.get("states"), ["idle", "loading", "success", "error"])

        events = {event.get("id"): event.get("effect") for event in schema["events"]}
        self.assertEqual(events.get("add_document_submit"), "create_document_request")
        self.assertEqual(events.get("add_document_success"), "refresh_documents_list_without_reload")
        self.assertEqual(events.get("add_document_error"), "show_validation_or_api_error")

    def test_document_type_values_are_synced_between_types_and_html(self) -> None:
        type_values = self._parse_document_type_union()
        html_values = self._parse_html_document_type_options()
        self.assertSetEqual(
            type_values,
            html_values,
            "DocumentType union and #documentType options must stay in sync",
        )


if __name__ == "__main__":
    unittest.main()

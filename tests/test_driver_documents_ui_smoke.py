import unittest
from pathlib import Path
import re


class DriverDocumentsUISmokeTests(unittest.TestCase):
    def test_add_document_button_and_form_exist(self) -> None:
        html = Path('public/guest_feed.html').read_text(encoding='utf-8')
        self.assertIn('id="addDocumentBtn"', html)
        self.assertIn('id="addDocumentForm"', html)
        self.assertIn('Добавить документ', html)
        self.assertIn('id="driverOverviewDocuments"', html)
        self.assertIn('Профиль водителя', html)
        self.assertNotIn('Добавить поездку', html)

    def test_documents_flow_functions_exist_in_script(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('loadDriverDocuments', script)
        self.assertIn('submitDriverDocument', script)
        self.assertIn('/api/driver/documents', script)
        self.assertIn('renderDriverOverviewDocuments', script)
        self.assertIn('mapDocumentStatus', script)
        self.assertRegex(
            script,
            re.compile(r"function setActiveProfileTab\(tab\)[\s\S]+if \(tab === 'documents'\)\s*\{\s*loadDriverDocuments\(\);", re.MULTILINE),
        )

    def test_documents_list_covers_loading_empty_and_error_states(self) -> None:
        html = Path('public/guest_feed.html').read_text(encoding='utf-8')
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('id="driverDocumentsLoadingState"', html)
        self.assertIn('id="driverDocumentsEmptyState"', html)
        self.assertIn('id="driverDocumentsErrorState"', html)
        self.assertIn('Загружаем документы...', html)
        self.assertIn('function setDriverDocumentsListState(state, errorMessage = \'\')', script)
        self.assertRegex(
            script,
            re.compile(
                r"async function loadDriverDocuments\(\)\s*\{\s*setDriverDocumentsListState\('loading'\);[\s\S]+setDriverDocumentsListState\('error', errorMessage\);",
                re.MULTILINE,
            ),
        )

    def test_documents_tab_has_trust_signals_prepared_for_verification_states(self) -> None:
        html = Path('public/guest_feed.html').read_text(encoding='utf-8')
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('id="profileVerificationBadge"', html)
        self.assertIn('id="profileTrustBadge"', html)
        self.assertIn('id="profileVerificationReason"', html)
        self.assertIn('id="profileVerificationResubmitBtn"', html)
        self.assertIn('function resolveVerificationState(profile)', script)
        self.assertIn('function renderProfileTrustSignals(profile)', script)
        self.assertIn('async function submitProfileForResubmission()', script)
        self.assertIn('pending_verification', script)
        self.assertIn('verification_state', script)

    def test_pending_verification_from_api_payload_is_wired_to_trust_signal_rendering(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertRegex(
            script,
            re.compile(
                r"const localProfile = \{[\s\S]+isVerified: Boolean\(payload\.is_verified\),[\s\S]+"
                r"verificationState: String\(payload\.verification_state \|\| payload\.verificationState \|\| ''\)\.trim\(\),[\s\S]+\};",
                re.MULTILINE,
            ),
        )
        self.assertRegex(
            script,
            re.compile(r"pending_verification:\s*'на проверке'"),
        )
        self.assertRegex(
            script,
            re.compile(r"const trustLabel = verificationState === 'verified' \? 'подтверждённый' : 'базовый';"),
        )

    def test_verification_state_falls_back_to_verified_when_only_is_verified_flag_is_present(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertRegex(
            script,
            re.compile(r"function resolveVerificationState\(profile\)\s*\{[\s\S]+const rawState = String\(profile\?\.verification_state \|\| profile\?\.verificationState \|\| ''\)\.trim\(\);"),
        )
        self.assertRegex(
            script,
            re.compile(r"if \(rawState\) return rawState;\s*if \(profile\?\.is_verified \|\| profile\?\.isVerified\) return 'verified';"),
        )

    def test_verified_verification_state_from_api_payload_maps_to_verified_trust_signals(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertRegex(
            script,
            re.compile(r"verificationState: String\(payload\.verification_state \|\| payload\.verificationState \|\| ''\)\.trim\(\),"),
        )
        self.assertRegex(
            script,
            re.compile(r"verified:\s*'подтверждена'"),
        )
        self.assertRegex(
            script,
            re.compile(r"profileVerificationBadge\.textContent = `Верификация: \$\{verificationLabels\[verificationState\] \|\| verificationState\}`;"),
        )
        self.assertRegex(
            script,
            re.compile(r"const trustLabel = verificationState === 'verified' \? 'подтверждённый' : 'базовый';"),
        )
        self.assertRegex(
            script,
            re.compile(r"profileTrustBadge\.textContent = `Trust badge: \$\{trustLabel\}`;"),
        )

    def test_explicit_verification_state_has_priority_over_boolean_verified_flag(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertRegex(
            script,
            re.compile(
                r"function resolveVerificationState\(profile\)\s*\{[\s\S]+const rawState = String\(profile\?\.verification_state \|\| profile\?\.verificationState \|\| ''\)\.trim\(\);\s*if \(rawState\) return rawState;\s*if \(profile\?\.is_verified \|\| profile\?\.isVerified\) return 'verified';",
            ),
        )
        self.assertRegex(
            script,
            re.compile(r"pending_verification:\s*'на проверке'"),
        )

    def test_verification_state_defaults_to_unverified_when_no_api_verification_fields_are_present(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertRegex(
            script,
            re.compile(
                r"function resolveVerificationState\(profile\)\s*\{[\s\S]+if \(rawState\) return rawState;\s*if \(profile\?\.is_verified \|\| profile\?\.isVerified\) return 'verified';\s*return 'unverified';",
            ),
        )
        self.assertRegex(
            script,
            re.compile(r"unverified:\s*'не начата'"),
        )
        self.assertRegex(
            script,
            re.compile(r"const trustLabel = verificationState === 'verified' \? 'подтверждённый' : 'базовый';"),
        )

    def test_verification_state_resolver_accepts_camel_case_field_from_profile_state(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertRegex(
            script,
            re.compile(
                r"const rawState = String\(profile\?\.verification_state \|\| profile\?\.verificationState \|\| ''\)\.trim\(\);",
            ),
        )

    def test_profile_save_normalization_accepts_camel_case_verification_state_from_api_payload(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertRegex(
            script,
            re.compile(
                r"const localProfile = \{[\s\S]+verificationState: String\(payload\.verification_state \|\| payload\.verificationState \|\| ''\)\.trim\(\),[\s\S]+\};",
                re.MULTILINE,
            ),
        )


if __name__ == '__main__':
    unittest.main()

import unittest
from pathlib import Path
import re


class DriverDocumentsUISmokeTests(unittest.TestCase):
    def test_add_document_button_and_form_exist(self) -> None:
        html = Path('public/guest_feed.html').read_text(encoding='utf-8')
        self.assertTrue(
            'id="addDocumentBtn"' in html or 'id="driverAddDocumentBtn"' in html,
            'Expected either legacy addDocumentBtn or new driverAddDocumentBtn trigger',
        )
        self.assertIn('id="addDocumentForm"', html)
        self.assertIn('id="documentFileInput"', html)
        self.assertIn('Файл документа (PDF)', html)
        self.assertIn('580-ФЗ и правила сервиса', html)
        self.assertIn('ОСГОП', html)
        self.assertIn('Журнал заказов', html)
        self.assertIn('Добавить документ', html)
        self.assertIn('id="driverOverviewDocuments"', html)
        self.assertIn('Профиль водителя', html)
        self.assertNotIn('Добавить поездку', html)

    def test_driver_profile_has_hero_progress_and_readiness_status_card(self) -> None:
        html = Path('public/guest_feed.html').read_text(encoding='utf-8')
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('id="driverProfileProgressBadge"', html)
        self.assertIn('id="driverReadinessStatusCard"', html)
        self.assertIn('id="driverReadinessStatusLabel"', html)
        self.assertIn('id="driverReadinessReason"', html)
        self.assertIn('id="driverReadinessNextStep"', html)
        self.assertIn('function applyDriverReadinessCard(summary = {})', script)
        self.assertIn('function getDriverRequiredFieldStats(profileData = {}, complianceData = {})', script)
        self.assertIn("driverReadinessActionState.primaryActionLabel = 'Перейти к заказам';", script)
        self.assertIn("driverReadinessActionState.primaryActionLabel = 'Добавить документ';", script)

    def test_documents_flow_functions_exist_in_script(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('loadDriverDocuments', script)
        self.assertIn('submitDriverDocument', script)
        self.assertIn('submitWaybillClose', script)
        self.assertIn('toggleWaybillCloseForm', script)
        self.assertIn('setDocumentStatusForType', script)
        self.assertIn('/api/driver/documents/${docId}/close', script)
        self.assertIn('/api/driver/documents', script)
        self.assertIn('/api/driver/documents/upload', script)
        self.assertIn('uploadDriverDocumentFile', script)
        self.assertIn('renderDriverOverviewDocuments', script)
        self.assertIn('mapDocumentStatus', script)
        self.assertIn("osgop: 'ОСГОП'", script)
        self.assertRegex(
            script,
            re.compile(
                r"function setActiveProfileTab\(tab\)[\s\S]+if \(activeTab === 'documents'\)\s*\{\s*refreshDriverProfileData\(\);",
                re.MULTILINE,
            ),
        )

    def test_waybill_close_form_and_controls_exist(self) -> None:
        html = Path('public/guest_feed.html').read_text(encoding='utf-8')
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('id="waybillCloseForm"', html)
        self.assertIn('id="submitWaybillCloseBtn"', html)
        self.assertIn('id="cancelWaybillCloseBtn"', html)
        self.assertIn('id="waybillPostshiftMedicalAt"', html)
        self.assertIn('id="waybillPostshiftMedicalResult"', html)
        self.assertIn('id="waybillActualReturnAt"', html)
        self.assertIn('id="waybillOdometerEnd"', html)
        self.assertIn('id="waybillDistanceKm"', html)
        self.assertIn('id="waybillFuelSpentLiters"', html)
        self.assertIn('id="waybillVehicleCondition"', html)
        self.assertIn('id="waybillStopsInfo"', html)
        self.assertIn('id="waybillCloseNotes"', html)
        self.assertIn('Закрыть путевой лист', html)
        self.assertIn("open: { tone: 'info', label: 'Открыт' }", script)
        self.assertIn("closed: { tone: 'neutral', label: 'Закрыт' }", script)

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
                r"async function loadDriverDocuments\(\)\s*\{[\s\S]+setDriverDocumentsListState\('loading'\);[\s\S]+setDriverDocumentsListState\('error', errorMessage\);",
                re.MULTILINE,
            ),
        )

    def test_driver_documents_network_error_uses_single_error_block(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        load_documents_match = re.search(
            r"async function loadDriverDocuments\(\)\s*\{[\s\S]+?\n    \}",
            script,
            re.MULTILINE,
        )
        self.assertIsNotNone(load_documents_match)
        load_documents_block = load_documents_match.group(0)
        self.assertIn("setDriverDocumentsListState('error', errorMessage);", load_documents_block)
        self.assertNotIn("setDocumentAlert(errorMessage);", load_documents_block)
        self.assertIn("setDocumentAlert('');", load_documents_block)

    def test_network_error_message_is_always_human_readable(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn(
            "const fallbackMessage = String(fallback || '').trim() || 'Не удалось выполнить запрос. Попробуйте ещё раз.';",
            script,
        )
        self.assertIn("if (message.includes('Failed to fetch') || message.includes('NetworkError')) {", script)
        self.assertIn("if (/http\\s*\\d{3}/i.test(message)) {", script)

    def test_driver_compliance_error_uses_user_friendly_network_message(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        load_compliance_match = re.search(
            r"async function loadDriverComplianceOverview\(\)\s*\{[\s\S]+?\n    \}",
            script,
            re.MULTILINE,
        )
        self.assertIsNotNone(load_compliance_match)
        load_compliance_block = load_compliance_match.group(0)
        self.assertIn("const complianceFallbackMessage = 'Не удалось загрузить сведения о допуске.';", load_compliance_block)
        self.assertIn("const friendlyComplianceError = toUserFriendlyNetworkError(", load_compliance_block)
        self.assertIn("driverHeaderQuickState.profileError = friendlyComplianceError;", load_compliance_block)
        self.assertIn("driverHeaderQuickState.complianceError = friendlyComplianceError;", load_compliance_block)
        self.assertIn("reason: friendlyComplianceError,", load_compliance_block)
        self.assertNotIn("String(error.message", load_compliance_block)

    def test_documents_tab_has_trust_signals_prepared_for_verification_states(self) -> None:
        html = Path('public/guest_feed.html').read_text(encoding='utf-8')
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('id="profileVerificationBadge"', html)
        self.assertIn('id="profileTrustBadge"', html)
        self.assertIn('id="profileVerificationReason"', html)
        self.assertIn('id="profileVerificationResubmitBtn"', html)
        self.assertIn('id="profileApiBaseIndicator"', html)
        self.assertIn('Текущий API base:', html)
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
            re.compile(r"renderStatusChip\(profileVerificationBadge, verificationState, \{"),
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

    def test_guest_profile_payload_sanitizes_unknown_verification_state_before_publish(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertRegex(
            script,
            re.compile(
                r"const allowedVerificationStates = new Set\(\['unverified', 'pending_verification', 'verified', 'rejected', 'expired'\]\);",
            ),
        )
        self.assertRegex(
            script,
            re.compile(
                r"const rawVerificationState = String\(stored\.verificationState \|\| stored\.verification_state \|\| ''\)\.trim\(\)\.toLowerCase\(\);",
            ),
        )
        self.assertRegex(
            script,
            re.compile(
                r"verification_state: safeVerificationState \|\| '',",
            ),
        )

    def test_feed_api_base_resolution_prefers_query_then_valid_storage_and_local_dev_port_fallback(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('function sanitizeStoredApiBase(rawValue)', script)
        self.assertRegex(
            script,
            re.compile(
                r"const apiBaseFromQuery = normalizeApiBase\(url\.searchParams\.get\('apiBase'\)\);[\s\S]+"
                r"if \(apiBaseFromQuery\) \{[\s\S]+return apiBaseFromQuery;",
                re.MULTILINE,
            ),
        )
        self.assertRegex(
            script,
            re.compile(
                r"const apiBaseFromStorage = sanitizeStoredApiBase\(localStorage\.getItem\(FEED_API_BASE_STORAGE_KEY\)\);[\s\S]+"
                r"if \(apiBaseFromStorage\) \{\s*return apiBaseFromStorage;\s*\}",
                re.MULTILINE,
            ),
        )
        self.assertIn("const locationOrigin = normalizeApiBase(window.location.origin);", script)
        self.assertIn("if (isLocalDevHost(window.location.hostname)) {", script)
        self.assertIn("const localPort = String(window.location.port || '').trim();", script)
        self.assertIn("if (localPort === '8000') {", script)
        self.assertIn("return 'http://localhost:8001';", script)
        local_dev_branch_index = script.find("if (isLocalDevHost(window.location.hostname)) {")
        same_origin_fallback_index = script.find("if (locationOrigin) return locationOrigin;")
        self.assertGreaterEqual(local_dev_branch_index, 0)
        self.assertGreaterEqual(same_origin_fallback_index, 0)
        self.assertLess(local_dev_branch_index, same_origin_fallback_index)
        self.assertIn("const FEED_API_PREFIX = normalizeApiBase(FEED_API_BASE) === normalizeApiBase(window.location.origin) ? '' : FEED_API_BASE;", script)

    def test_profile_diagnostic_block_shows_current_api_base_label(self) -> None:
        script = Path('public/web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn("const profileApiBaseIndicator = document.getElementById('profileApiBaseIndicator');", script)
        self.assertIn("profileApiBaseIndicator.textContent = `Текущий API base: ${FEED_API_BASE_LABEL}`;", script)
        self.assertIn("const FEED_API_BASE_LABEL = FEED_API_PREFIX || `${normalizeApiBase(window.location.origin) || 'same-origin'} (/api/...)`;", script)


if __name__ == '__main__':
    unittest.main()

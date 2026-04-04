import re
import unittest
from pathlib import Path


class CashOnlyUiRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = Path('public/guest_feed.html').read_text(encoding='utf-8')
        self.script = Path('public/web/js/feed.js').read_text(encoding='utf-8')

    def test_html_contains_cash_only_confirmation_and_trip_completion_steps(self) -> None:
        self.assertIn('id="cashOnlyConfirmStep"', self.html)
        self.assertIn('id="cashOnlyConfirmBanner"', self.html)
        self.assertIn('id="cashOnlyConfirmCheckbox"', self.html)
        self.assertIn('id="cashOnlyConfirmOrderBtn"', self.html)
        self.assertIn('id="cashOnlyTripCompleteStep"', self.html)
        self.assertIn('Только наличные • оплата водителю при завершении поездки.', self.html)

    def test_script_uses_unified_cash_only_badge_text_and_style(self) -> None:
        self.assertIn("const CASH_ONLY_BADGE_TEXT = 'Только наличные • оплата водителю при завершении поездки.';", self.script)
        self.assertIn('const CASH_ONLY_BADGE_CLASSNAME =', self.script)
        self.assertIn('function createCashOnlyBadge()', self.script)
        self.assertIn("cashOnlyOfferBadge.setAttribute('data-cash-only-point', 'offer-card');", self.script)

    def test_final_confirmation_is_blocked_without_explicit_cash_only_acknowledgement(self) -> None:
        self.assertIn('function updateCashOnlyConfirmationGuardState()', self.script)
        self.assertIn('cashOnlyConfirmOrderBtn.disabled = !isConfirmed;', self.script)
        self.assertIn('function confirmCashOnlyOrder()', self.script)
        self.assertIn("showAppNotification('Подтвердите cash-only условие перед финальным подтверждением.', 'error');", self.script)
        self.assertRegex(
            self.script,
            re.compile(r"cashOnlyConfirmCheckbox\?\.addEventListener\('change',\s*updateCashOnlyConfirmationGuardState\);"),
        )

    def test_trip_completion_step_is_revealed_after_guarded_confirmation(self) -> None:
        self.assertIn("cashOnlyTripCompleteStep.classList.remove('hidden');", self.script)
        self.assertIn("cashOnlyTripCompleteStep.setAttribute('aria-hidden', 'false');", self.script)


if __name__ == '__main__':
    unittest.main()

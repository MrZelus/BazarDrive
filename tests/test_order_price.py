import unittest

from app.services.order_pricing_service import OrderPricingService, TariffConfig


class OrderPriceTests(unittest.TestCase):
    def test_calculate_fare_is_deterministic_with_fixed_tariff(self) -> None:
        tariff = TariffConfig(base_fare=99.0, per_km=18.5, per_minute=4.0, surge_multiplier=1.0)
        total = OrderPricingService.calculate_fare(distance_km=12.4, duration_minutes=21, tariff=tariff)
        self.assertEqual(total, 412.4)

    def test_calculate_fare_applies_surge_multiplier(self) -> None:
        tariff = TariffConfig(base_fare=120.0, per_km=20.0, per_minute=3.0, surge_multiplier=1.25)
        total = OrderPricingService.calculate_fare(distance_km=5, duration_minutes=10, tariff=tariff)
        self.assertEqual(total, 312.5)


if __name__ == "__main__":
    unittest.main()

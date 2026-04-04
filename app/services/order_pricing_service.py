from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TariffConfig:
    base_fare: float
    per_km: float
    per_minute: float
    surge_multiplier: float = 1.0


class OrderPricingService:
    """Deterministic fare calculator for CI-safe pricing checks."""

    @staticmethod
    def calculate_fare(*, distance_km: float, duration_minutes: float, tariff: TariffConfig) -> float:
        distance = max(0.0, float(distance_km))
        duration = max(0.0, float(duration_minutes))
        subtotal = tariff.base_fare + distance * tariff.per_km + duration * tariff.per_minute
        total = subtotal * max(0.0, float(tariff.surge_multiplier))
        return round(total, 2)

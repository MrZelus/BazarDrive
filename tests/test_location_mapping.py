import unittest

from app.services.location_mapping_service import LocationMappingService


class LocationMappingTests(unittest.TestCase):
    def test_estimate_route_returns_eta_and_distance_for_known_points(self) -> None:
        # Moscow city-center points with a stable great-circle expectation.
        result = LocationMappingService.estimate_route(
            pickup_lat=55.7558,
            pickup_lng=37.6176,
            dropoff_lat=55.7517,
            dropoff_lng=37.6178,
        )

        self.assertEqual(result.status, "ok")
        self.assertAlmostEqual(result.distance_km, 0.456, delta=0.08)
        self.assertGreater(result.eta_minutes, 0.0)

    def test_estimate_route_uses_degraded_state_when_pickup_gps_missing(self) -> None:
        result = LocationMappingService.estimate_route(
            pickup_lat=None,
            pickup_lng=None,
            dropoff_lat=55.7517,
            dropoff_lng=37.6178,
        )

        self.assertEqual(result.status, "degraded")
        self.assertEqual(result.distance_km, 0.0)
        self.assertEqual(result.eta_minutes, 0.0)


if __name__ == "__main__":
    unittest.main()

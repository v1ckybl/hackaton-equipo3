from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


DRY_FORECAST = {
    "rain_24h_mm": 12,
    "rain_72h_mm": 29,
    "forecast_rain_6h_mm": 8,
    "forecast_rain_12h_mm": 16,
}
STORM_FORECAST = {
    "rain_24h_mm": 122,
    "rain_72h_mm": 245,
    "forecast_rain_6h_mm": 68,
    "forecast_rain_12h_mm": 110,
}


def analysis_payload(forecast: dict[str, float], latitude: float = -27.4692, longitude: float = -58.8306) -> dict:
    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "forecast": forecast,
        "safety_margin_minutes": 40,
    }


class BackendApiTests(unittest.TestCase):
    def test_health_and_static_frontend(self) -> None:
        with TestClient(app) as client:
            health = client.get("/api/health")
            self.assertEqual(health.status_code, 200)
            self.assertTrue(health.json()["model_loaded"])
            self.assertEqual(health.json()["model_version"], "synthetic-v1")
            self.assertIn("Última Ventana", client.get("/").text)
            self.assertEqual(client.get("/static/styles.css").status_code, 200)
            self.assertEqual(client.get("/static/app.js").status_code, 200)

    def test_direct_prediction_and_validation(self) -> None:
        dry = {**DRY_FORECAST, "elevation_mean_m": 67, "slope_mean_pct": 3.1, "water_coverage_100m_ratio": 0.04}
        storm = {**STORM_FORECAST, "elevation_mean_m": 35, "slope_mean_pct": 0.2, "water_coverage_100m_ratio": 0.46}
        with TestClient(app) as client:
            dry_response = client.post("/api/predict", json=dry)
            storm_response = client.post("/api/predict", json=storm)
            self.assertEqual(dry_response.status_code, 200)
            self.assertEqual(storm_response.status_code, 200)
            self.assertGreater(storm_response.json()["risk_score"], dry_response.json()["risk_score"])
            invalid = client.post("/api/predict", json={**dry, "rain_72h_mm": 1})
            self.assertEqual(invalid.status_code, 422)

    def test_storm_analysis_returns_routes_alerts_and_timeline(self) -> None:
        with TestClient(app) as client:
            response = client.post("/api/demo/analyze", json=analysis_payload(STORM_FORECAST))
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertTrue(body["triggered"])
            self.assertEqual(body["mode"], "SYNTHETIC_DEMO")
            self.assertEqual(len(body["routes"]), 3)
            self.assertTrue(body["alerts"])
            for route in body["routes"]:
                self.assertEqual(route["geometry"]["type"], "LineString")
                self.assertEqual(len(route["timeline"]), 12)
                self.assertGreaterEqual(route["peak_risk_score"], 0)
                self.assertLessEqual(route["peak_risk_score"], 1)

    def test_dry_scenario_does_not_activate_weather_trigger(self) -> None:
        with TestClient(app) as client:
            response = client.post("/api/demo/analyze", json=analysis_payload(DRY_FORECAST))
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["triggered"])

    def test_location_translates_demo_geometries(self) -> None:
        with TestClient(app) as client:
            first = client.post("/api/demo/analyze", json=analysis_payload(DRY_FORECAST)).json()
            second = client.post("/api/demo/analyze", json=analysis_payload(DRY_FORECAST, -30.0, -60.0)).json()
            first_point = first["routes"][0]["geometry"]["coordinates"][0]
            second_point = second["routes"][0]["geometry"]["coordinates"][0]
            self.assertNotEqual(first_point, second_point)
            self.assertAlmostEqual(second_point[0], -60.0, places=4)
            self.assertAlmostEqual(second_point[1], -30.0, places=4)


if __name__ == "__main__":
    unittest.main()

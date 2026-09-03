# Model card — Última Ventana synthetic-v1

- **Algoritmo:** XGBoost binario
- **Features:** rain_24h_mm, rain_72h_mm, forecast_rain_6h_mm, forecast_rain_12h_mm, elevation_mean_m, slope_mean_pct, water_coverage_100m_ratio
- **Target:** `intransitable_within_6h` a 6 horas
- **Origen:** datos y labels completamente sintéticos
- **ROC-AUC test sintético:** 0.830
- **Uso previsto:** demostración técnica del pipeline y del contrato de inferencia
- **Uso no permitido:** afirmar precisión, seguridad o transitabilidad real

El score es un índice experimental. Debe recalibrarse con observaciones reales antes de cualquier uso productivo.

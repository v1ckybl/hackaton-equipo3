from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.train_synthetic_v1 import (
    FEATURE_COLUMNS_V1,
    create_splits,
    generate_synthetic_dataset,
    run_pipeline,
    validate_dataset,
)
from ultima_ventana_ml import (
    PredictionInputError,
    RiskPredictor,
    calculate_last_safe_departure,
    find_critical_time,
    generate_demo_timeline,
    risk_level,
)


class SyntheticDatasetTests(unittest.TestCase):
    def test_generation_is_reproducible_and_matches_contract(self) -> None:
        first = generate_synthetic_dataset(rows=500, seed=42)
        second = generate_synthetic_dataset(rows=500, seed=42)

        np.testing.assert_array_equal(first.features, second.features)
        np.testing.assert_array_equal(first.target, second.target)
        self.assertEqual(first.features.shape, (500, len(FEATURE_COLUMNS_V1)))
        validate_dataset(first)

    def test_different_seeds_produce_different_data(self) -> None:
        first = generate_synthetic_dataset(rows=500, seed=1)
        second = generate_synthetic_dataset(rows=500, seed=2)

        self.assertFalse(np.array_equal(first.features, second.features))
        self.assertFalse(np.array_equal(first.target, second.target))

    def test_splits_are_disjoint_stratified_and_reproducible(self) -> None:
        dataset = generate_synthetic_dataset(rows=1_000, seed=42)
        first = create_splits(dataset.target, seed=42)
        second = create_splits(dataset.target, seed=42)

        np.testing.assert_array_equal(first.train, second.train)
        np.testing.assert_array_equal(first.validation, second.validation)
        np.testing.assert_array_equal(first.test, second.test)
        all_indices = np.concatenate((first.train, first.validation, first.test))
        self.assertEqual(np.unique(all_indices).shape[0], 1_000)
        self.assertEqual(set(dataset.target[first.train].tolist()), {0, 1})
        self.assertEqual(set(dataset.target[first.validation].tolist()), {0, 1})
        self.assertEqual(set(dataset.target[first.test].tolist()), {0, 1})


class TrainingPipelineTests(unittest.TestCase):
    def test_pipeline_exports_and_reloads_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            summary = run_pipeline(
                rows=2_000,
                seed=42,
                dataset_path=root / "dataset.csv",
                model_dir=root / "model",
                n_estimators=80,
                minimum_roc_auc=0.70,
            )

            self.assertGreaterEqual(summary["test_roc_auc"], 0.70)
            self.assertGreater(
                summary["test_roc_auc"], summary["baseline_dummy_test_roc_auc"]
            )
            self.assertGreater(
                summary["severe_scenario_score"], summary["dry_scenario_score"]
            )
            self.assertTrue((root / "dataset.csv").is_file())
            self.assertTrue((root / "model" / "model.json").is_file())
            self.assertTrue((root / "model" / "feature_schema.json").is_file())
            self.assertTrue((root / "model" / "metrics.json").is_file())
            self.assertTrue((root / "model" / "metadata.json").is_file())

            metadata = json.loads(
                (root / "model" / "metadata.json").read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["training_data_type"], "fully_synthetic")
            self.assertFalse(metadata["production_eligible"])
            self.assertEqual(metadata["feature_columns"], list(FEATURE_COLUMNS_V1))

            predictor = RiskPredictor.load(
                root / "model" / "model.json",
                root / "model" / "feature_schema.json",
            )
            dry = dict(zip(FEATURE_COLUMNS_V1, [12.0, 29.0, 8.0, 16.0, 67.0, 3.1, 0.04]))
            severe = dict(zip(FEATURE_COLUMNS_V1, [122.0, 245.0, 68.0, 110.0, 48.0, 0.3, 0.42]))
            self.assertGreater(predictor.predict(severe), predictor.predict(dry))

            batch = pd.DataFrame([{"segment_id": 1, **dry}, {"segment_id": 2, **severe}])
            scored = predictor.predict_many(batch)
            self.assertEqual(scored["segment_id"].tolist(), [1, 2])
            self.assertTrue(scored["risk_score"].between(0.0, 1.0).all())
            self.assertIn(scored.loc[0, "risk_level"], {"LOW", "MODERATE", "HIGH", "CRITICAL"})

            with self.assertRaises(PredictionInputError):
                predictor.predict({name: dry[name] for name in FEATURE_COLUMNS_V1[:-1]})
            with self.assertRaises(PredictionInputError):
                predictor.predict({**dry, "unexpected": 1.0})
            with self.assertRaises(PredictionInputError):
                predictor.predict({**dry, "water_coverage_100m_ratio": 1.5})


class RiskAndTimelineTests(unittest.TestCase):
    def test_risk_level_boundaries(self) -> None:
        self.assertEqual(risk_level(0.0), "LOW")
        self.assertEqual(risk_level(0.30), "MODERATE")
        self.assertEqual(risk_level(0.50), "HIGH")
        self.assertEqual(risk_level(0.70), "CRITICAL")
        with self.assertRaises(ValueError):
            risk_level(1.1)

    def test_timeline_and_last_departure(self) -> None:
        timeline = generate_demo_timeline()
        self.assertEqual(len(timeline), 12)
        predictions = timeline[["prediction_time"]].copy()
        predictions["risk_score"] = np.linspace(0.1, 0.9, len(timeline))
        critical_time = find_critical_time(predictions)
        self.assertIsNotNone(critical_time)
        departure = calculate_last_safe_departure(critical_time, 80, 40)
        self.assertEqual((critical_time - departure).total_seconds(), 7_200)


if __name__ == "__main__":
    unittest.main()

"""Entrenamiento, evaluación y exportación del modelo sintético v1."""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Any

import numpy as np
import sklearn
import xgboost
from sklearn.dummy import DummyClassifier
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from xgboost import XGBClassifier

from .contract import (
    CRITICAL_RISK_THRESHOLD,
    FEATURE_COLUMNS_V1,
    FEATURE_SCHEMA_VERSION,
    LABEL_RULE_VERSION,
    MODEL_VERSION,
    SYNTHETIC_GENERATOR_VERSION,
    TARGET_HORIZON_HOURS,
    TARGET_NAME,
)
from .synthetic import (
    DatasetSplits,
    SyntheticDataset,
    create_splits,
    export_synthetic_dataset,
    feature_schema,
    generate_synthetic_dataset,
    sha256_file,
    write_json,
)

DRY_SCENARIO = np.array([[12.0, 29.0, 8.0, 16.0, 67.0, 3.1, 0.04]], dtype=np.float64)
SEVERE_SCENARIO = np.array([[122.0, 245.0, 68.0, 110.0, 48.0, 0.3, 0.42]], dtype=np.float64)


def heuristic_risk_scores(features: np.ndarray) -> np.ndarray:
    """Transparent fallback score; it is an MVP heuristic, not scientific truth."""
    values = np.asarray(features, dtype=np.float64)
    rain_24h = values[:, 0] / 200.0
    rain_72h = values[:, 1] / 400.0
    forecast_6h = values[:, 2] / 150.0
    forecast_12h = values[:, 3] / 250.0
    low_elevation = 1.0 - (values[:, 4] - 20.0) / 100.0
    low_slope = 1.0 - values[:, 5] / 10.0
    water = values[:, 6]
    linear = -3.2 + 1.0 * rain_24h + 1.6 * rain_72h + 1.4 * forecast_6h
    linear += 0.6 * forecast_12h + 1.8 * water + 0.6 * low_slope + 0.5 * low_elevation
    return 1.0 / (1.0 + np.exp(-linear))


def _threshold_metrics(target: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, Any]:
    prediction = (probabilities >= threshold).astype(np.int8)
    return {
        "threshold": threshold,
        "precision": float(precision_score(target, prediction, zero_division=0)),
        "recall": float(recall_score(target, prediction, zero_division=0)),
        "f1": float(f1_score(target, prediction, zero_division=0)),
        "confusion_matrix": confusion_matrix(target, prediction, labels=(0, 1)).tolist(),
    }


def evaluate_probabilities(target: np.ndarray, probabilities: np.ndarray) -> dict[str, Any]:
    return {
        "rows": int(target.shape[0]),
        "positive_prevalence": float(np.mean(target)),
        "roc_auc": float(roc_auc_score(target, probabilities)),
        "at_0_50": _threshold_metrics(target, probabilities, 0.50),
        "at_0_70": _threshold_metrics(target, probabilities, CRITICAL_RISK_THRESHOLD),
    }


def train_models(dataset: SyntheticDataset, splits: DatasetSplits, seed: int, n_estimators: int) -> tuple[XGBClassifier, dict[str, Any]]:
    train, validation, test = splits.train, splits.validation, splits.test
    dummy = DummyClassifier(strategy="prior", random_state=seed)
    dummy.fit(dataset.features[train], dataset.target[train])
    model = XGBClassifier(
        objective="binary:logistic", eval_metric="logloss", n_estimators=n_estimators,
        max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        tree_method="hist", random_state=seed, n_jobs=2,
    )
    model.fit(dataset.features[train], dataset.target[train], eval_set=[(dataset.features[validation], dataset.target[validation])], verbose=False)
    metrics = {
        "baseline_dummy_test": evaluate_probabilities(dataset.target[test], dummy.predict_proba(dataset.features[test])[:, 1]),
        "baseline_heuristic_test": evaluate_probabilities(dataset.target[test], heuristic_risk_scores(dataset.features[test])),
        "validation": evaluate_probabilities(dataset.target[validation], model.predict_proba(dataset.features[validation])[:, 1]),
        "test": evaluate_probabilities(dataset.target[test], model.predict_proba(dataset.features[test])[:, 1]),
    }
    return model, metrics


def smoke_test_saved_model(model_path: Path) -> dict[str, Any]:
    reloaded = XGBClassifier()
    reloaded.load_model(model_path)
    dry_score = float(reloaded.predict_proba(DRY_SCENARIO)[0, 1])
    severe_score = float(reloaded.predict_proba(SEVERE_SCENARIO)[0, 1])
    if not 0.0 <= dry_score <= 1.0 or not 0.0 <= severe_score <= 1.0:
        raise RuntimeError("saved model produced a risk score outside [0, 1]")
    if severe_score <= dry_score:
        raise RuntimeError("severe scenario must score above the dry scenario")
    return {"dry_scenario_score": dry_score, "severe_scenario_score": severe_score}


def _write_model_card(path: Path, metrics: dict[str, Any]) -> None:
    content = f"""# Model card — Última Ventana {MODEL_VERSION}

- **Algoritmo:** XGBoost binario
- **Features:** {', '.join(FEATURE_COLUMNS_V1)}
- **Target:** `{TARGET_NAME}` a {TARGET_HORIZON_HOURS} horas
- **Origen:** datos y labels completamente sintéticos
- **ROC-AUC test sintético:** {metrics['test']['roc_auc']:.3f}
- **Uso previsto:** demostración técnica del pipeline y del contrato de inferencia
- **Uso no permitido:** afirmar precisión, seguridad o transitabilidad real

El score es un índice experimental. Debe recalibrarse con observaciones reales antes de cualquier uso productivo.
"""
    path.write_text(content, encoding="utf-8", newline="\n")


def run_pipeline(rows: int, seed: int, dataset_path: Path, model_dir: Path, n_estimators: int = 200, minimum_roc_auc: float = 0.75) -> dict[str, Any]:
    dataset = generate_synthetic_dataset(rows=rows, seed=seed)
    splits = create_splits(dataset.target, seed=seed)
    manifest_path = dataset_path.with_name(f"{dataset_path.stem}_manifest.json")
    dataset_manifest = export_synthetic_dataset(dataset, splits, dataset_path, manifest_path)
    model, metrics = train_models(dataset, splits, seed, n_estimators)
    test_auc = metrics["test"]["roc_auc"]
    dummy_auc = metrics["baseline_dummy_test"]["roc_auc"]
    if test_auc < minimum_roc_auc:
        raise RuntimeError(f"test ROC-AUC {test_auc:.3f} is below the gate {minimum_roc_auc:.3f}")
    if test_auc <= dummy_auc:
        raise RuntimeError("XGBoost did not outperform the dummy baseline")

    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "model.json"
    schema_path = model_dir / "feature_schema.json"
    metrics_path = model_dir / "metrics.json"
    metadata_path = model_dir / "metadata.json"
    model_card_path = model_dir / "MODEL_CARD.md"
    model.save_model(str(model_path))
    write_json(schema_path, feature_schema())
    smoke_test = smoke_test_saved_model(model_path)
    metrics["smoke_test"] = smoke_test
    write_json(metrics_path, metrics)

    metadata = {
        "model_version": MODEL_VERSION,
        "algorithm": "xgboost",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_columns": list(FEATURE_COLUMNS_V1),
        "target": TARGET_NAME,
        "target_horizon_hours": TARGET_HORIZON_HOURS,
        "critical_risk_threshold": CRITICAL_RISK_THRESHOLD,
        "training_data_type": "fully_synthetic",
        "production_eligible": False,
        "synthetic_generator_version": SYNTHETIC_GENERATOR_VERSION,
        "label_origin": "SYNTHETIC",
        "label_rule_version": LABEL_RULE_VERSION,
        "seed": seed,
        "rows": rows,
        "positive_prevalence": float(np.mean(dataset.target)),
        "split_rows": dataset_manifest["split_rows"],
        "model_parameters": {
            "n_estimators": n_estimators, "max_depth": 4, "learning_rate": 0.05,
            "subsample": 0.8, "colsample_bytree": 0.8, "tree_method": "hist",
            "random_state": seed, "n_jobs": 2,
        },
        "dataset_path": dataset_path.as_posix(),
        "dataset_sha256": dataset_manifest["dataset_sha256"],
        "model_sha256": sha256_file(model_path),
        "feature_schema_sha256": sha256_file(schema_path),
        "dependency_versions": {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__, "xgboost": xgboost.__version__},
        "quality_statement": "Índice experimental entrenado con datos totalmente sintéticos; no mide precisión real de transitabilidad.",
    }
    write_json(metadata_path, metadata)
    _write_model_card(model_card_path, metrics)
    return {
        "dataset_path": str(dataset_path), "dataset_manifest_path": str(manifest_path),
        "model_path": str(model_path), "model_dir": str(model_dir), "rows": rows,
        "positive_prevalence": metadata["positive_prevalence"],
        "baseline_dummy_test_roc_auc": dummy_auc,
        "baseline_heuristic_test_roc_auc": metrics["baseline_heuristic_test"]["roc_auc"],
        "validation_roc_auc": metrics["validation"]["roc_auc"], "test_roc_auc": test_auc,
        **smoke_test,
    }

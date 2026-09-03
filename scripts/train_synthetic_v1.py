"""CLI para generar datos, entrenar XGBoost y probar el artefacto v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ultima_ventana_ml import (
    CRITICAL_RISK_THRESHOLD,
    FEATURE_COLUMNS_V1,
    FEATURE_DEFINITIONS,
    FEATURE_SCHEMA_VERSION,
    LABEL_RULE_VERSION,
    SYNTHETIC_GENERATOR_VERSION,
    TARGET_HORIZON_HOURS,
    TARGET_NAME,
    DatasetSplits,
    SyntheticDataset,
    create_splits,
    evaluate_probabilities,
    generate_synthetic_dataset,
    heuristic_risk_scores,
    run_pipeline,
    smoke_test_saved_model,
    train_models,
    validate_dataset,
    write_dataset_csv,
)

__all__ = [
    "CRITICAL_RISK_THRESHOLD", "FEATURE_COLUMNS_V1", "FEATURE_DEFINITIONS",
    "FEATURE_SCHEMA_VERSION", "LABEL_RULE_VERSION", "SYNTHETIC_GENERATOR_VERSION",
    "TARGET_HORIZON_HOURS", "TARGET_NAME", "DatasetSplits", "SyntheticDataset",
    "create_splits", "evaluate_probabilities", "generate_synthetic_dataset",
    "heuristic_risk_scores", "run_pipeline", "smoke_test_saved_model", "train_models",
    "validate_dataset", "write_dataset_csv",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic data, train XGBoost, and test model v1.")
    parser.add_argument("--rows", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dataset-out", type=Path, default=Path("data/processed/training_dataset_synthetic_v1.csv"))
    parser.add_argument("--model-dir", type=Path, default=Path("models/synthetic_v1"))
    parser.add_argument("--n-estimators", type=int, default=200)
    parser.add_argument("--min-roc-auc", type=float, default=0.75)
    args = parser.parse_args(argv)
    if args.rows < 100:
        parser.error("--rows must be at least 100")
    if args.n_estimators < 1:
        parser.error("--n-estimators must be at least 1")
    if not 0.0 <= args.min_roc_auc <= 1.0:
        parser.error("--min-roc-auc must be between 0 and 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_pipeline(
            rows=args.rows, seed=args.seed, dataset_path=args.dataset_out,
            model_dir=args.model_dir, n_estimators=args.n_estimators,
            minimum_roc_auc=args.min_roc_auc,
        )
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Training failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

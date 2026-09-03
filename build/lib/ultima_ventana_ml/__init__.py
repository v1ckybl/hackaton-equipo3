"""Herramientas para el MVP sintético de Última Ventana."""

from .contract import (
    CRITICAL_RISK_THRESHOLD,
    FEATURE_COLUMNS_V1,
    FEATURE_DEFINITIONS,
    FEATURE_SCHEMA_VERSION,
    LABEL_RULE_VERSION,
    SYNTHETIC_GENERATOR_VERSION,
    TARGET_HORIZON_HOURS,
    TARGET_NAME,
    risk_level,
)
from .modeling import (
    evaluate_probabilities,
    heuristic_risk_scores,
    run_pipeline,
    smoke_test_saved_model,
    train_models,
)
from .predictor import PredictionInputError, RiskPredictor
from .synthetic import (
    DatasetSplits,
    SyntheticDataset,
    create_splits,
    export_synthetic_dataset,
    generate_synthetic_dataset,
    validate_dataset,
    write_dataset_csv,
)
from .timeline import (
    calculate_last_safe_departure,
    find_critical_time,
    generate_demo_timeline,
)

__all__ = [
    "CRITICAL_RISK_THRESHOLD",
    "DatasetSplits",
    "FEATURE_COLUMNS_V1",
    "FEATURE_DEFINITIONS",
    "FEATURE_SCHEMA_VERSION",
    "LABEL_RULE_VERSION",
    "PredictionInputError",
    "RiskPredictor",
    "SYNTHETIC_GENERATOR_VERSION",
    "SyntheticDataset",
    "TARGET_HORIZON_HOURS",
    "TARGET_NAME",
    "calculate_last_safe_departure",
    "create_splits",
    "evaluate_probabilities",
    "export_synthetic_dataset",
    "find_critical_time",
    "generate_demo_timeline",
    "generate_synthetic_dataset",
    "heuristic_risk_scores",
    "risk_level",
    "run_pipeline",
    "smoke_test_saved_model",
    "train_models",
    "validate_dataset",
    "write_dataset_csv",
]

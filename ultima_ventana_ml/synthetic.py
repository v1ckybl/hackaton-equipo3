"""Generación y exportación del dataset sintético v1."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.model_selection import train_test_split

from .contract import (
    FEATURE_COLUMNS_V1,
    FEATURE_DEFINITIONS,
    FEATURE_SCHEMA_VERSION,
    LABEL_RULE_VERSION,
    SYNTHETIC_GENERATOR_VERSION,
    TARGET_HORIZON_HOURS,
    TARGET_NAME,
)


@dataclass(frozen=True)
class SyntheticDataset:
    sample_ids: np.ndarray
    features: np.ndarray
    target: np.ndarray


@dataclass(frozen=True)
class DatasetSplits:
    train: np.ndarray
    validation: np.ndarray
    test: np.ndarray


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-values))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for block in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file_handle:
        json.dump(value, file_handle, indent=2, sort_keys=True, ensure_ascii=False)
        file_handle.write("\n")


def feature_schema() -> dict[str, Any]:
    return {
        "version": FEATURE_SCHEMA_VERSION,
        "target": {
            "name": TARGET_NAME,
            "type": "binary",
            "horizon_hours": TARGET_HORIZON_HOURS,
        },
        "features": [
            {"position": position, **definition}
            for position, definition in enumerate(FEATURE_DEFINITIONS, start=1)
        ],
    }


def generate_synthetic_dataset(rows: int, seed: int) -> SyntheticDataset:
    """Generate correlated weather and terrain scenarios without external data."""
    if rows < 100:
        raise ValueError("rows must be at least 100")

    rng = np.random.default_rng(seed)
    regime = rng.choice(3, size=rows, p=(0.55, 0.30, 0.15))
    rain_24h = rng.gamma(np.array((1.1, 2.2, 4.0))[regime], np.array((7.0, 18.0, 28.0))[regime])
    rain_24h = np.clip(rain_24h, 0.0, 200.0)
    previous_48h = rng.gamma(np.array((1.0, 2.0, 4.0))[regime], np.array((8.0, 20.0, 35.0))[regime])
    rain_72h = np.clip(rain_24h + previous_48h, rain_24h, 400.0)
    forecast_6h = rng.gamma(np.array((1.0, 2.0, 3.5))[regime], np.array((5.0, 12.0, 22.0))[regime])
    forecast_6h = np.clip(forecast_6h + 0.12 * rain_24h + rng.normal(0.0, 3.0, rows), 0.0, 150.0)
    following_6h = rng.gamma(np.array((1.0, 1.5, 2.5))[regime], np.array((4.0, 10.0, 20.0))[regime])
    forecast_12h = np.clip(forecast_6h + following_6h + 0.20 * forecast_6h, forecast_6h, 250.0)
    elevation = 20.0 + 100.0 * rng.beta(2.2, 2.5, rows)
    slope = 10.0 * rng.beta(1.4, 3.5, rows)

    low_elevation = 1.0 - (elevation - 20.0) / 100.0
    low_slope = 1.0 - slope / 10.0
    water_logit = -4.2 + 0.011 * rain_72h + 0.018 * forecast_6h
    water_logit += 1.4 * low_elevation + 0.9 * low_slope + rng.normal(0.0, 0.55, rows)
    water_coverage = np.clip(_sigmoid(water_logit) + rng.normal(0.0, 0.035, rows), 0.0, 1.0)

    features = np.column_stack((rain_24h, rain_72h, forecast_6h, forecast_12h, elevation, slope, water_coverage))
    features = np.round(features.astype(np.float64), decimals=6)
    normalized = features / np.array((200.0, 400.0, 150.0, 250.0, 120.0, 10.0, 1.0))
    normalized_elevation = (features[:, 4] - 20.0) / 100.0
    label_logit = -3.5 + 1.0 * normalized[:, 0] + 1.8 * normalized[:, 1]
    label_logit += 1.6 * normalized[:, 2] + 0.7 * normalized[:, 3] + 2.2 * normalized[:, 6]
    label_logit += 0.8 * (1.0 - normalized[:, 5]) + 0.7 * (1.0 - normalized_elevation)
    label_logit += 1.4 * normalized[:, 1] * normalized[:, 6] + rng.normal(0.0, 0.45, rows)
    target = rng.binomial(1, _sigmoid(label_logit)).astype(np.int8)

    dataset = SyntheticDataset(np.arange(rows, dtype=np.int64), features, target)
    validate_dataset(dataset)
    return dataset


def validate_dataset(dataset: SyntheticDataset) -> None:
    features, target = dataset.features, dataset.target
    if features.ndim != 2 or features.shape[1] != len(FEATURE_COLUMNS_V1):
        raise ValueError("dataset does not match the seven-feature v1 contract")
    if features.dtype != np.float64 or not np.isfinite(features).all():
        raise ValueError("all features must be finite float64 values")
    if dataset.sample_ids.shape != (features.shape[0],) or target.shape != (features.shape[0],):
        raise ValueError("sample IDs, features, and target have different lengths")
    for position, definition in enumerate(FEATURE_DEFINITIONS):
        column = features[:, position]
        if np.any(column < definition["min"]) or np.any(column > definition["max"]):
            raise ValueError(f"{definition['name']} is outside its synthetic range")
    if np.any(features[:, 1] < features[:, 0]):
        raise ValueError("rain_72h_mm must be greater than or equal to rain_24h_mm")
    if np.any(features[:, 3] < features[:, 2]):
        raise ValueError("forecast_rain_12h_mm must be greater than or equal to forecast_rain_6h_mm")
    if set(np.unique(target).tolist()) != {0, 1}:
        raise ValueError("target must contain both binary classes")
    prevalence = float(np.mean(target))
    if not 0.10 <= prevalence <= 0.60:
        raise ValueError(f"unexpected synthetic target prevalence: {prevalence:.3f}")


def create_splits(target: np.ndarray, seed: int) -> DatasetSplits:
    indices = np.arange(target.shape[0])
    train, remainder = train_test_split(indices, test_size=0.30, random_state=seed, stratify=target)
    validation, test = train_test_split(remainder, test_size=0.50, random_state=seed + 1, stratify=target[remainder])
    return DatasetSplits(np.sort(train), np.sort(validation), np.sort(test))


def write_dataset_csv(path: Path, dataset: SyntheticDataset, splits: DatasetSplits) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    split_by_row = np.empty(dataset.target.shape[0], dtype="<U10")
    split_by_row[splits.train], split_by_row[splits.validation], split_by_row[splits.test] = "TRAIN", "VALIDATION", "TEST"
    header = ("synthetic_sample_id", *FEATURE_COLUMNS_V1, TARGET_NAME, "split", "label_origin", "label_rule_version")
    with path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.writer(file_handle, lineterminator="\n")
        writer.writerow(header)
        for row_index in range(dataset.target.shape[0]):
            writer.writerow((int(dataset.sample_ids[row_index]), *(f"{value:.6f}" for value in dataset.features[row_index]), int(dataset.target[row_index]), split_by_row[row_index], "SYNTHETIC", LABEL_RULE_VERSION))
    return sha256_file(path)


def export_synthetic_dataset(dataset: SyntheticDataset, splits: DatasetSplits, dataset_path: Path, manifest_path: Path) -> dict[str, Any]:
    digest = write_dataset_csv(dataset_path, dataset, splits)
    manifest = {
        "dataset_path": dataset_path.as_posix(),
        "dataset_sha256": digest,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "generator_version": SYNTHETIC_GENERATOR_VERSION,
        "label_origin": "SYNTHETIC",
        "label_rule_version": LABEL_RULE_VERSION,
        "rows": int(dataset.target.shape[0]),
        "positive_prevalence": float(np.mean(dataset.target)),
        "split_rows": {"train": len(splits.train), "validation": len(splits.validation), "test": len(splits.test)},
    }
    write_json(manifest_path, manifest)
    return manifest

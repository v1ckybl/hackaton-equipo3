"""CLI para generar solamente el dataset sintético v1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ultima_ventana_ml import create_splits, export_synthetic_dataset, generate_synthetic_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the synthetic v1 dataset without external data.")
    parser.add_argument("--rows", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dataset-out", type=Path, default=Path("data/processed/training_dataset_synthetic_v1.csv"))
    args = parser.parse_args()
    dataset = generate_synthetic_dataset(args.rows, args.seed)
    splits = create_splits(dataset.target, args.seed)
    manifest_path = args.dataset_out.with_name(f"{args.dataset_out.stem}_manifest.json")
    manifest = export_synthetic_dataset(dataset, splits, args.dataset_out, manifest_path)
    print(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

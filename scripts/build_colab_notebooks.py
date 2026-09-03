"""Genera los notebooks Colab versionados con celdas sin outputs."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
COLAB_BASE = "https://colab.research.google.com/github/v1ckybl/hackaton-equipo3/blob/feature/ultima-ventana/notebooks"


def markdown(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": dedent(source).strip() + "\n"}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(source).strip() + "\n",
    }


def configuration(output_name: str, rows: int = 10_000) -> dict:
    return code(f"""
        # COLAB_CONFIG — editar solo esta celda
        REPO_URL = "https://github.com/v1ckybl/hackaton-equipo3.git"
        REPO_REF = "feature/ultima-ventana"
        REPO_DIR = "/content/hackaton-equipo3"
        OUTPUT_ROOT = "/content/ultima_ventana_outputs/{output_name}"
        ROWS = {rows}
        RANDOM_SEED = 42
        N_ESTIMATORS = 200
        MIN_ROC_AUC = 0.75
        DOWNLOAD_OUTPUTS = False
    """)


def setup() -> dict:
    return code("""
        # COLAB_SETUP — una sola preparación idempotente por runtime
        import importlib
        import os
        import subprocess
        import sys
        from pathlib import Path

        repo_dir = Path(REPO_DIR)
        if repo_dir.exists() and not (repo_dir / ".git").is_dir():
            raise RuntimeError(f"{repo_dir} existe pero no es un clone Git válido")
        if not repo_dir.exists():
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", REPO_REF, REPO_URL, str(repo_dir)],
                check=True,
            )
        else:
            subprocess.run(["git", "-C", str(repo_dir), "fetch", "--depth", "1", "origin", REPO_REF], check=True)
            subprocess.run(["git", "-C", str(repo_dir), "checkout", "--detach", "FETCH_HEAD"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", str(repo_dir)], check=True)
        os.chdir(repo_dir)
        for module_name in list(sys.modules):
            if module_name == "ultima_ventana_ml" or module_name.startswith("ultima_ventana_ml."):
                del sys.modules[module_name]
        importlib.invalidate_caches()

        commit = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "--short", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        print(f"Entorno listo · Python {sys.version.split()[0]} · commit {commit}")
    """)


def archive_cell(output_variable: str = "output_dir") -> dict:
    return code(f"""
        import shutil
        archive_path = shutil.make_archive(str({output_variable}), "zip", root_dir={output_variable})
        print(f"Artefactos empaquetados: {{archive_path}}")
        if DOWNLOAD_OUTPUTS:
            from google.colab import files
            files.download(archive_path)
    """)


def notebook(name: str, cells: list[dict]) -> None:
    payload = {
        "cells": cells,
        "metadata": {
            "colab": {"name": name, "provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    (NOTEBOOK_DIR / name).write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def build_master() -> None:
    name = "00_pipeline_sintetico_colab.ipynb"
    cells = [
        markdown(f"""
            # Última Ventana — pipeline sintético completo

            [Abrir este notebook en Google Colab]({COLAB_BASE}/{name})

            Este flujo genera todos sus datos dentro de Colab, entrena XGBoost, evalúa el
            modelo, exporta artefactos y prueba inferencia individual, batch y temporal.
            No consulta APIs, Supabase, Google Drive ni datasets externos.

            **Entrada:** configuración de la siguiente celda.  
            **Salida:** archivos bajo `/content/ultima_ventana_outputs/00_pipeline`.
        """),
        configuration("00_pipeline"),
        markdown("## 1. Preparar el runtime"),
        setup(),
        markdown("## 2. Generar, entrenar, evaluar y exportar"),
        code("""
            import json
            from pathlib import Path
            import matplotlib.pyplot as plt
            import numpy as np
            import pandas as pd

            from ultima_ventana_ml import FEATURE_COLUMNS_V1, TARGET_NAME, run_pipeline

            if ROWS < 100 or N_ESTIMATORS < 1:
                raise ValueError("ROWS debe ser >= 100 y N_ESTIMATORS >= 1")
            output_dir = Path(OUTPUT_ROOT)
            dataset_path = output_dir / "training_dataset_synthetic_v1.csv"
            model_dir = output_dir / "model"
            summary = run_pipeline(
                rows=ROWS, seed=RANDOM_SEED, dataset_path=dataset_path,
                model_dir=model_dir, n_estimators=N_ESTIMATORS,
                minimum_roc_auc=MIN_ROC_AUC,
            )
            display(pd.Series(summary, name="resultado"))
        """),
        markdown("## 3. Inspeccionar el dataset sintético"),
        code("""
            data = pd.read_csv(dataset_path)
            print(f"Filas: {len(data):,} · Nulos: {int(data.isna().sum().sum())}")
            display(data.head())
            display(data[list(FEATURE_COLUMNS_V1)].describe().T)
            display(data.groupby("split")[TARGET_NAME].agg(["count", "mean"]))

            selected = ["rain_72h_mm", "forecast_rain_6h_mm", "water_coverage_100m_ratio", TARGET_NAME]
            data[selected].hist(figsize=(11, 7), bins=30)
            plt.suptitle("Distribuciones sintéticas")
            plt.tight_layout()
            plt.show()
        """),
        code("""
            correlation = data[list(FEATURE_COLUMNS_V1) + [TARGET_NAME]].corr()
            fig, ax = plt.subplots(figsize=(9, 7))
            image = ax.imshow(correlation, cmap="coolwarm", vmin=-1, vmax=1)
            ax.set_xticks(range(len(correlation)), correlation.columns, rotation=75, ha="right")
            ax.set_yticks(range(len(correlation)), correlation.index)
            fig.colorbar(image, ax=ax, label="correlación")
            ax.set_title("Correlaciones del dataset generado")
            plt.tight_layout()
            plt.show()
        """),
        markdown("## 4. Revisar métricas y umbrales"),
        code("""
            metrics = json.loads((model_dir / "metrics.json").read_text(encoding="utf-8"))
            rows = []
            for key in ("baseline_dummy_test", "baseline_heuristic_test", "validation", "test"):
                item = metrics[key]
                rows.append({"evaluación": key, "roc_auc": item["roc_auc"], **item["at_0_70"]})
            metrics_table = pd.DataFrame(rows).drop(columns="confusion_matrix")
            display(metrics_table.style.format({"roc_auc": "{:.3f}", "precision": "{:.3f}", "recall": "{:.3f}", "f1": "{:.3f}"}))
        """),
        code("""
            from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay
            from ultima_ventana_ml import RiskPredictor

            predictor = RiskPredictor.load(model_dir / "model.json", model_dir / "feature_schema.json")
            test_frame = data.loc[data["split"] == "TEST"].copy()
            test_predictions = predictor.predict_many(test_frame)
            y_true = test_frame[TARGET_NAME].to_numpy()
            y_score = test_predictions["risk_score"].to_numpy()
            fig, axes = plt.subplots(1, 2, figsize=(11, 4))
            RocCurveDisplay.from_predictions(y_true, y_score, ax=axes[0], name="XGBoost")
            ConfusionMatrixDisplay.from_predictions(y_true, y_score >= 0.70, ax=axes[1], colorbar=False)
            axes[1].set_title("Matriz de confusión · umbral 0.70")
            plt.tight_layout()
            plt.show()
        """),
        markdown("## 5. Probar inferencia y la Última Ventana demostrativa"),
        code("""
            dry = dict(zip(FEATURE_COLUMNS_V1, [12.0, 29.0, 8.0, 16.0, 67.0, 3.1, 0.04]))
            severe = dict(zip(FEATURE_COLUMNS_V1, [122.0, 245.0, 68.0, 110.0, 48.0, 0.3, 0.42]))
            scenarios = pd.DataFrame([
                {"scenario": "seco", **dry},
                {"scenario": "severo", **severe},
            ])
            scenario_predictions = predictor.predict_many(scenarios)
            display(scenario_predictions[["scenario", "risk_score", "risk_level"]])
            assert scenario_predictions.loc[1, "risk_score"] > scenario_predictions.loc[0, "risk_score"]
        """),
        code("""
            from ultima_ventana_ml import (
                calculate_last_safe_departure, find_critical_time, generate_demo_timeline,
            )

            timeline = predictor.predict_many(generate_demo_timeline())
            timeline.to_csv(output_dir / "timeline_predictions.csv", index=False)
            critical_time = find_critical_time(timeline)
            if critical_time is None:
                raise RuntimeError("El escenario controlado no alcanzó el umbral crítico")
            last_departure = calculate_last_safe_departure(critical_time, 80, 40)
            display(timeline[["prediction_time", "risk_score", "risk_level"]])
            print(f"Hora crítica: {critical_time} · Última salida demostrativa: {last_departure}")

            plt.plot(timeline["prediction_time"], timeline["risk_score"], marker="o")
            plt.axhline(0.70, color="red", linestyle="--", label="umbral crítico")
            plt.xticks(rotation=45); plt.ylabel("risk_score"); plt.legend(); plt.tight_layout(); plt.show()
        """),
        markdown("## 6. Empaquetar resultados"),
        archive_cell(),
        markdown("Las métricas anteriores describen únicamente consistencia sobre labels sintéticos; no representan precisión sobre caminos reales."),
    ]
    notebook(name, cells)


def build_generation() -> None:
    name = "01_generacion_eda_sintetica.ipynb"
    cells = [
        markdown(f"""
            # Última Ventana — generación y EDA sintética

            [Abrir este notebook en Google Colab]({COLAB_BASE}/{name})

            Genera un dataset reproducible con el contrato v1 y revisa rangos, nulos,
            clases, distribuciones y correlaciones. No requiere ningún dato externo.
        """),
        configuration("01_generacion_eda"),
        markdown("## 1. Preparar el runtime"),
        setup(),
        markdown("## 2. Generar y validar"),
        code("""
            from pathlib import Path
            import matplotlib.pyplot as plt
            import pandas as pd

            from ultima_ventana_ml import (
                FEATURE_COLUMNS_V1, TARGET_NAME, create_splits,
                export_synthetic_dataset, generate_synthetic_dataset, validate_dataset,
            )

            output_dir = Path(OUTPUT_ROOT)
            dataset_path = output_dir / "training_dataset_synthetic_v1.csv"
            manifest_path = output_dir / "training_dataset_synthetic_v1_manifest.json"
            dataset = generate_synthetic_dataset(ROWS, RANDOM_SEED)
            validate_dataset(dataset)
            splits = create_splits(dataset.target, RANDOM_SEED)
            manifest = export_synthetic_dataset(dataset, splits, dataset_path, manifest_path)
            display(pd.Series(manifest, name="manifest"))
        """),
        markdown("## 3. Explorar calidad y distribución"),
        code("""
            data = pd.read_csv(dataset_path)
            assert data[list(FEATURE_COLUMNS_V1)].notna().all().all()
            assert set(data[TARGET_NAME].unique()) == {0, 1}
            print(f"Filas: {len(data):,} · duplicados: {data.duplicated().sum()}")
            display(data.head())
            display(data[list(FEATURE_COLUMNS_V1)].describe().T)
            display(data.groupby("split")[TARGET_NAME].agg(filas="count", prevalencia="mean"))
        """),
        code("""
            axes = data[list(FEATURE_COLUMNS_V1) + [TARGET_NAME]].hist(figsize=(14, 10), bins=30)
            plt.suptitle("Distribuciones del dataset sintético v1")
            plt.tight_layout(); plt.show()

            correlation = data[list(FEATURE_COLUMNS_V1) + [TARGET_NAME]].corr()
            fig, ax = plt.subplots(figsize=(9, 7))
            image = ax.imshow(correlation, cmap="coolwarm", vmin=-1, vmax=1)
            ax.set_xticks(range(len(correlation)), correlation.columns, rotation=75, ha="right")
            ax.set_yticks(range(len(correlation)), correlation.index)
            fig.colorbar(image, ax=ax); plt.tight_layout(); plt.show()
        """),
        markdown("## 4. Empaquetar dataset y manifest"),
        archive_cell(),
        markdown("El target y todas las features son sintéticos. Este dataset sirve para validar el software, no para medir transitabilidad real."),
    ]
    notebook(name, cells)


def build_training() -> None:
    name = "02_entrenamiento_evaluacion_inferencia.ipynb"
    cells = [
        markdown(f"""
            # Última Ventana — entrenamiento, evaluación e inferencia

            [Abrir este notebook en Google Colab]({COLAB_BASE}/{name})

            Entrena desde cero con datos sintéticos generados en el mismo runtime, compara
            dos baselines, exporta el modelo y prueba inferencia nominal, batch y temporal.
        """),
        configuration("02_entrenamiento_evaluacion"),
        markdown("## 1. Preparar el runtime"),
        setup(),
        markdown("## 2. Ejecutar entrenamiento reproducible"),
        code("""
            import json
            from pathlib import Path
            import matplotlib.pyplot as plt
            import pandas as pd

            from ultima_ventana_ml import FEATURE_COLUMNS_V1, TARGET_NAME, RiskPredictor, run_pipeline

            output_dir = Path(OUTPUT_ROOT)
            dataset_path = output_dir / "training_dataset_synthetic_v1.csv"
            model_dir = output_dir / "model"
            summary = run_pipeline(
                ROWS, RANDOM_SEED, dataset_path, model_dir,
                n_estimators=N_ESTIMATORS, minimum_roc_auc=MIN_ROC_AUC,
            )
            display(pd.Series(summary, name="resultado"))
        """),
        markdown("## 3. Evaluar modelo y baselines"),
        code("""
            metrics = json.loads((model_dir / "metrics.json").read_text(encoding="utf-8"))
            report = []
            for key in ("baseline_dummy_test", "baseline_heuristic_test", "validation", "test"):
                report.append({"evaluación": key, "roc_auc": metrics[key]["roc_auc"], **metrics[key]["at_0_70"]})
            display(pd.DataFrame(report).drop(columns="confusion_matrix").style.format(precision=3))

            model = RiskPredictor.load(model_dir / "model.json", model_dir / "feature_schema.json")
            data = pd.read_csv(dataset_path)
            test = data.loc[data["split"] == "TEST"].copy()
            scored = model.predict_many(test)
        """),
        code("""
            from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay
            y_true, y_score = test[TARGET_NAME], scored["risk_score"]
            fig, axes = plt.subplots(1, 2, figsize=(11, 4))
            RocCurveDisplay.from_predictions(y_true, y_score, ax=axes[0], name="XGBoost")
            ConfusionMatrixDisplay.from_predictions(y_true, y_score >= 0.70, ax=axes[1], colorbar=False)
            axes[1].set_title("Matriz de confusión · 0.70")
            plt.tight_layout(); plt.show()

            importance = pd.Series(model.feature_importances, index=FEATURE_COLUMNS_V1).sort_values()
            importance.plot.barh(title="Importancia de features"); plt.tight_layout(); plt.show()
        """),
        markdown("## 4. Probar predictor individual y batch"),
        code("""
            one = {
                "rain_24h_mm": 61.4, "rain_72h_mm": 138.2,
                "forecast_rain_6h_mm": 34.0, "forecast_rain_12h_mm": 62.0,
                "elevation_mean_m": 48.7, "slope_mean_pct": 0.42,
                "water_coverage_100m_ratio": 0.27,
            }
            print(f"Predicción individual: {model.predict(one):.3f}")
            batch = model.predict_many(test.head(8))
            batch.to_csv(output_dir / "batch_predictions.csv", index=False)
            display(batch[["synthetic_sample_id", "risk_score", "risk_level"]])
        """),
        markdown("## 5. Probar serie temporal y hora crítica"),
        code("""
            from ultima_ventana_ml import (
                calculate_last_safe_departure, find_critical_time, generate_demo_timeline,
            )
            timeline = model.predict_many(generate_demo_timeline())
            critical_time = find_critical_time(timeline)
            if critical_time is None:
                raise RuntimeError("El escenario controlado no alcanzó el umbral crítico")
            last_departure = calculate_last_safe_departure(critical_time, 80, 40)
            timeline.to_csv(output_dir / "timeline_predictions.csv", index=False)
            display(timeline[["prediction_time", "risk_score", "risk_level"]])
            print(f"Hora crítica: {critical_time} · Última salida demostrativa: {last_departure}")
        """),
        markdown("## 6. Empaquetar artefactos"),
        archive_cell(),
        markdown("El score es experimental y está entrenado contra labels sintéticos; no expresa precisión real."),
    ]
    notebook(name, cells)


def main() -> None:
    build_master()
    build_generation()
    build_training()
    print(f"Notebooks generados en {NOTEBOOK_DIR}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path


NOTEBOOKS = (
    "00_pipeline_sintetico_colab.ipynb",
    "01_generacion_eda_sintetica.ipynb",
    "02_entrenamiento_evaluacion_inferencia.ipynb",
)


class ColabNotebookTests(unittest.TestCase):
    def test_notebooks_are_clean_linear_and_offline_for_data(self) -> None:
        root = Path(__file__).resolve().parents[1] / "notebooks"
        forbidden = ("drive.mount", "files.upload", "requests.get", "urlretrieve", "supabase", "kaggle")

        for name in NOTEBOOKS:
            with self.subTest(notebook=name):
                payload = json.loads((root / name).read_text(encoding="utf-8"))
                self.assertEqual(payload["nbformat"], 4)
                code_cells = [cell for cell in payload["cells"] if cell["cell_type"] == "code"]
                source = "\n".join(cell["source"] for cell in code_cells)
                self.assertEqual(source.count("# COLAB_CONFIG"), 1)
                self.assertEqual(source.count("# COLAB_SETUP"), 1)
                self.assertFalse(any(term in source.lower() for term in forbidden))
                for cell in code_cells:
                    self.assertIsNone(cell["execution_count"])
                    self.assertEqual(cell["outputs"], [])
                    self.assertLessEqual(len(cell["source"].splitlines()), 50)
                    ast.parse(cell["source"])

    def test_notebook_builder_is_reproducible(self) -> None:
        builder = Path(__file__).resolve().parents[1] / "scripts" / "build_colab_notebooks.py"
        ast.parse(builder.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

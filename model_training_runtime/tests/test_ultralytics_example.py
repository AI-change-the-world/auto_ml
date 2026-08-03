from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from package_validation import validate_model_package_archive, validate_package_archive


EXAMPLE_DIR = Path(__file__).resolve().parents[1] / "examples" / "ultralytics-detection"
PYTORCH_EXAMPLE_DIR = Path(__file__).resolve().parents[1] / "examples" / "pytorch-image-classifier"


def load_example_module():
    spec = importlib.util.spec_from_file_location("ultralytics_detection_example", EXAMPLE_DIR / "train.py")
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load Ultralytics example module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UltralyticsExampleTest(unittest.TestCase):
    def test_pytorch_classifier_builder_produces_valid_runnable_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "pytorch-image-classifier.zip"
            subprocess.run(
                [sys.executable, str(PYTORCH_EXAMPLE_DIR / "build_package_zip.py"), str(output)],
                check=True,
            )
            report = validate_package_archive(output.read_bytes())
            self.assertEqual(report.manifest.key, "pytorch-image-classifier")
            self.assertIn("script_managed", [mode.value for mode in report.manifest.input_modes])
            with ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {"training_package.json", "train.py"})

    def test_code_package_builder_produces_valid_dependency_free_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "ultralytics-detection.zip"
            subprocess.run(
                [sys.executable, str(EXAMPLE_DIR / "build_package_zip.py"), str(output)],
                check=True,
            )
            report = validate_package_archive(output.read_bytes())
            self.assertEqual(report.manifest.key, "ultralytics-detection")
            self.assertEqual(report.manifest.runtime.id, "ultralytics-8.3.0-pytorch-2.5-cu124")
            with ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {"training_package.json", "train.py"})

    def test_model_package_builder_separates_initialize_and_resume_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            weights = root / "weights.pt"
            checkpoint = root / "last.pt"
            weights.write_bytes(b"weights")
            checkpoint.write_bytes(b"checkpoint")
            output = root / "model.zip"
            subprocess.run(
                [
                    sys.executable,
                    str(EXAMPLE_DIR / "build_model_package_zip.py"),
                    str(weights),
                    str(output),
                    "--classes",
                    "person,car",
                    "--resume-checkpoint",
                    str(checkpoint),
                ],
                check=True,
            )
            report = validate_model_package_archive(output.read_bytes())
            self.assertEqual(report.manifest.framework.id, "ultralytics")
            self.assertEqual(report.manifest.artifact_path, "weights/model.pt")
            self.assertEqual(report.manifest.resume_checkpoint_path, "checkpoints/last.pt")

    def test_example_imports_framework_only_inside_entrypoint(self) -> None:
        module = load_example_module()
        source = (EXAMPLE_DIR / "train.py").read_text(encoding="utf-8")
        self.assertEqual(module.ULTRALYTICS_VERSION, "8.3.0")
        self.assertIn("from ultralytics import YOLO", source)
        self.assertNotIn("requirements.txt", source)

    def test_dataset_adapter_converts_materialized_items_to_yolo_layout(self) -> None:
        module = load_example_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_dir = root / "input"
            output_dir = root / "output"
            first_dir = input_dir / "dataset" / "first"
            second_dir = input_dir / "dataset" / "second"
            first_dir.mkdir(parents=True)
            second_dir.mkdir(parents=True)
            (first_dir / "cat.jpg").write_bytes(b"image-1")
            (first_dir / "cat.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
            (second_dir / "car.jpg").write_bytes(b"image-2")
            (second_dir / "car.txt").write_text("1 0.4 0.4 0.1 0.1\n", encoding="utf-8")
            dataset = {
                "class_names": ["cat", "car"],
                "items": [
                    {
                        "item_id": "first",
                        "split": "train",
                        "media_path": "dataset/first/cat.jpg",
                        "annotation_path": "dataset/first/cat.txt",
                    },
                    {
                        "item_id": "second",
                        "split": "val",
                        "media_path": "dataset/second/car.jpg",
                        "annotation_path": "dataset/second/car.txt",
                    },
                ],
            }
            data_yaml, sample_count = module._prepare_dataset(
                dataset,
                input_dir=input_dir,
                output_dir=output_dir,
                val_fraction=0.2,
            )
            self.assertEqual(sample_count, 2)
            self.assertTrue((output_dir / "_ultralytics_dataset" / "images" / "train" / "00000000_cat.jpg").is_file())
            self.assertEqual(
                (output_dir / "_ultralytics_dataset" / "labels" / "val" / "00000001_car.txt").read_text(encoding="utf-8"),
                "1 0.4 0.4 0.1 0.1\n",
            )
            self.assertIn("names:", data_yaml.read_text(encoding="utf-8"))

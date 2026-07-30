"""Build the uploadable ZIP with all package files at its root."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PACKAGE_FILES = (
    "README.md",
    "batch_script.json",
    "requirements.txt",
    "image_center_box.py",
    "box_utils.py",
)


def main() -> None:
    package_dir = Path(__file__).resolve().parent
    output_path = package_dir.parent / "batch-script-zip-example.zip"

    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        for name in PACKAGE_FILES:
            archive.write(package_dir / name, arcname=name)

    print(f"Built upload package: {output_path}")


if __name__ == "__main__":
    main()

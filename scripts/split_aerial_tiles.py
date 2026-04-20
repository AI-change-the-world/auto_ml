#!/usr/bin/env python3
"""
Split a large aerial/mosaic image into overlapping tiles for dataset import tests.

Default output names follow the aerial dataset convention:
    {scene}_{rows}x{cols}_r{row}_c{col}.png

Example:
    python scripts/split_aerial_tiles.py
    python scripts/split_aerial_tiles.py --rows 3 --cols 4 --overlap 0.2
"""

from __future__ import annotations

import argparse
import json
import math
import zipfile
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - runtime environment hint
    raise SystemExit(
        "Pillow is required. Install it with: python -m pip install pillow"
    ) from exc


DEFAULT_INPUT = Path("readme/building_example.png")
DEFAULT_OUTPUT_DIR = Path("readme/aerial_tiles")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a large image into overlapping aerial tiles."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Source image path. Default: {DEFAULT_INPUT}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--scene",
        default="buildingA",
        help="Scene name prefix used in tile filenames. Default: buildingA",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=3,
        help="Vertical tile count. Default: 3",
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=4,
        help="Horizontal tile count. Default: 4",
    )
    parser.add_argument(
        "--overlap",
        type=float,
        default=0.2,
        help="Target overlap ratio between adjacent tiles. Default: 0.2",
    )
    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "jpg", "jpeg", "webp"],
        help="Output image format. Default: png",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=95,
        help="Quality for jpg/jpeg/webp output. Default: 95",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Do not create a zip archive containing generated tiles.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.input.exists():
        raise SystemExit(f"Input image not found: {args.input}")
    if args.rows < 1 or args.cols < 1:
        raise SystemExit("--rows and --cols must be greater than 0")
    if not 0 <= args.overlap < 0.8:
        raise SystemExit("--overlap must be in [0, 0.8)")
    if not 1 <= args.quality <= 100:
        raise SystemExit("--quality must be between 1 and 100")


def compute_tile_size(total: int, count: int, overlap: float) -> int:
    if count == 1:
        return total
    effective_count = count - overlap * (count - 1)
    return min(total, math.ceil(total / effective_count))


def compute_starts(total: int, count: int, tile_size: int) -> list[int]:
    if count == 1:
        return [0]
    max_start = max(0, total - tile_size)
    return [round(i * max_start / (count - 1)) for i in range(count)]


def image_save_kwargs(fmt: str, quality: int) -> dict[str, Any]:
    if fmt in {"jpg", "jpeg", "webp"}:
        return {"quality": quality}
    return {}


def split_image(args: argparse.Namespace) -> dict[str, Any]:
    validate_args(args)

    output_dir = args.output_dir / args.scene
    output_dir.mkdir(parents=True, exist_ok=True)

    fmt = args.format.lower()
    suffix = "jpg" if fmt == "jpeg" else fmt
    save_format = "JPEG" if fmt in {"jpg", "jpeg"} else fmt.upper()

    with Image.open(args.input) as image:
        image = image.convert("RGB")
        width, height = image.size

        tile_width = compute_tile_size(width, args.cols, args.overlap)
        tile_height = compute_tile_size(height, args.rows, args.overlap)
        x_starts = compute_starts(width, args.cols, tile_width)
        y_starts = compute_starts(height, args.rows, tile_height)

        manifest: dict[str, Any] = {
            "source_image": str(args.input),
            "scene_name": args.scene,
            "rows": args.rows,
            "cols": args.cols,
            "overlap_ratio": args.overlap,
            "image_size": {"width": width, "height": height},
            "tile_size": {"width": tile_width, "height": tile_height},
            "naming_pattern": "{scene}_{rows}x{cols}_r{row}_c{col}.{ext}",
            "sequence_order": "row_major",
            "tiles": [],
        }

        for row_index, y0 in enumerate(y_starts, start=1):
            for col_index, x0 in enumerate(x_starts, start=1):
                x1 = min(width, x0 + tile_width)
                y1 = min(height, y0 + tile_height)
                tile = image.crop((x0, y0, x1, y1))
                file_name = (
                    f"{args.scene}_{args.rows}x{args.cols}_"
                    f"r{row_index:02d}_c{col_index:02d}.{suffix}"
                )
                tile_path = output_dir / file_name
                tile.save(tile_path, format=save_format, **image_save_kwargs(fmt, args.quality))

                manifest["tiles"].append(
                    {
                        "file_name": file_name,
                        "row": row_index,
                        "col": col_index,
                        "x": x0,
                        "y": y0,
                        "width": x1 - x0,
                        "height": y1 - y0,
                        "global_bbox": [x0, y0, x1, y1],
                    }
                )

    manifest_path = output_dir / f"{args.scene}_{args.rows}x{args.cols}_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if not args.no_zip:
        zip_path = args.output_dir / f"{args.scene}_{args.rows}x{args.cols}_tiles.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for tile_info in manifest["tiles"]:
                tile_path = output_dir / tile_info["file_name"]
                archive.write(tile_path, arcname=tile_info["file_name"])
            archive.write(manifest_path, arcname=manifest_path.name)
        manifest["zip_path"] = str(zip_path)

    manifest["output_dir"] = str(output_dir)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def main() -> None:
    manifest = split_image(parse_args())
    print(
        "Generated "
        f"{len(manifest['tiles'])} tiles in {manifest['output_dir']}\n"
        f"Manifest: {manifest['manifest_path']}"
    )
    if "zip_path" in manifest:
        print(f"Zip: {manifest['zip_path']}")


if __name__ == "__main__":
    main()

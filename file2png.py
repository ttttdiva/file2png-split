from __future__ import annotations

import argparse
import random
import tempfile
from pathlib import Path

from file2png_common import (
    BASE_DIR,
    DEFAULT_VOLUME_SIZE,
    OUTPUT_DIR,
    WORK_DIR,
    ensure_work_dir,
    find_7zip,
    list_base_pngs,
    prepare_output_dir,
    resolve_dir,
    run_7zip,
    safe_temp_prefix,
    split_part_to_png_name,
)
from zipaspng import disguise_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Embed files or folders into PNG files."
    )
    parser.add_argument("--src", nargs="+", required=True, help="Source files/folders")
    parser.add_argument(
        "--base-dir",
        default=None,
        help=f"Embedding PNG directory. Default: {BASE_DIR}",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=f"Output root directory. Default: {OUTPUT_DIR}",
    )
    parser.add_argument(
        "--work-dir",
        default=None,
        help=f"Temporary work directory. Default: {WORK_DIR}",
    )
    parser.add_argument(
        "--volume-size",
        default=DEFAULT_VOLUME_SIZE,
        help=f"7-Zip split volume size. Default: {DEFAULT_VOLUME_SIZE}",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing non-empty output directory.",
    )
    return parser.parse_args()


def disguise_with_retry(secret_zip: Path, base_pngs: list[Path], output_image: Path) -> None:
    last_error: Exception | None = None
    for embedding in random.sample(base_pngs, len(base_pngs)):
        try:
            print(f"Embedding with {embedding}")
            disguise_file(str(secret_zip), str(embedding), str(output_image))
            return
        except RuntimeError as exc:
            last_error = exc
            output_image.unlink(missing_ok=True)

    raise RuntimeError(f"No usable base PNG found for {output_image}") from last_error


def split_archive_parts(work_path: Path, source_name: str) -> list[Path]:
    part_pattern = f"{source_name}.zip."
    parts = [
        path
        for path in work_path.iterdir()
        if path.is_file()
        and path.name.startswith(part_pattern)
        and path.name[len(part_pattern) :].isdigit()
    ]
    parts.sort(key=lambda path: path.name)
    if not parts:
        raise RuntimeError(f"7-Zip did not create split archive parts for {source_name}")
    return parts


def embed_source(
    source: Path,
    base_pngs: list[Path],
    output_root: Path,
    work_root: Path,
    seven_zip: Path,
    volume_size: str,
    replace: bool,
) -> Path:
    if not source.exists():
        raise FileNotFoundError(f"Source does not exist: {source}")

    source = source.resolve()
    output_dir = output_root / source.name
    prepare_output_dir(output_dir, replace=replace)

    with tempfile.TemporaryDirectory(
        prefix=safe_temp_prefix(source.name), dir=work_root
    ) as temp_dir:
        work_path = Path(temp_dir)
        split_zip = work_path / f"{source.name}.zip"

        run_7zip(
            seven_zip,
            ["a", "-mx=0", f"-v{volume_size}", split_zip, source.name],
            cwd=source.parent,
        )

        for part in split_archive_parts(work_path, source.name):
            wrapped_zip = work_path / f"{part.name}.zip"
            run_7zip(seven_zip, ["a", "-mx=0", wrapped_zip.name, part.name], cwd=work_path)

            output_image = output_dir / split_part_to_png_name(part.name)
            disguise_with_retry(wrapped_zip, base_pngs, output_image)
            print(f"Wrote {output_image}")

    return output_dir


def run() -> int:
    args = parse_args()
    base_dir = resolve_dir(args.base_dir, BASE_DIR)
    output_root = resolve_dir(args.output_dir, OUTPUT_DIR)
    work_root = resolve_dir(args.work_dir, WORK_DIR)
    ensure_work_dir(work_root)
    output_root.mkdir(parents=True, exist_ok=True)

    base_pngs = list_base_pngs(base_dir)
    seven_zip = find_7zip()
    sources = [Path(src).expanduser() for src in args.src]

    print(f"Tool root: {Path(__file__).resolve().parent}")
    print(f"Base PNGs: {base_dir}")
    print(f"Outputs: {output_root}")
    print(f"Work: {work_root}")
    print(f"7-Zip: {seven_zip}")
    print(f"Will embed {len(sources)} source(s)")

    for source in sources:
        output_dir = embed_source(
            source=source,
            base_pngs=base_pngs,
            output_root=output_root,
            work_root=work_root,
            seven_zip=seven_zip,
            volume_size=args.volume_size,
            replace=args.replace,
        )
        print(f"Completed {source} -> {output_dir}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)

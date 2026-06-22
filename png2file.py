from __future__ import annotations

import argparse
import shutil
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from file2png_common import (
    WORK_DIR,
    ensure_work_dir,
    find_7zip,
    parse_png_part_name,
    resolve_dir,
    run_7zip,
    safe_temp_prefix,
)


@dataclass(frozen=True)
class EmbeddedPart:
    path: Path
    number: int
    text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract original files from embedded PNG parts."
    )
    parser.add_argument("--src", nargs="+", required=True, help="Embedded PNG files")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Extraction directory. Default: the selected PNG directory.",
    )
    parser.add_argument(
        "--work-dir",
        default=None,
        help=f"Temporary work directory. Default: {WORK_DIR}",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files when extracting the restored archive.",
    )
    parser.add_argument(
        "--remove-source",
        action="store_true",
        help="Delete selected embedded PNG files after successful extraction.",
    )
    return parser.parse_args()


def group_sources(paths: list[str]) -> dict[tuple[Path, str], list[EmbeddedPart]]:
    groups: dict[tuple[Path, str], list[EmbeddedPart]] = defaultdict(list)
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Embedded PNG does not exist: {path}")

        name, number, text = parse_png_part_name(path)
        groups[(path.parent, name)].append(EmbeddedPart(path=path, number=number, text=text))

    return dict(groups)


def validate_parts(name: str, parts: list[EmbeddedPart]) -> list[EmbeddedPart]:
    ordered = sorted(parts, key=lambda part: part.number)
    numbers = [part.number for part in ordered]

    if len(numbers) != len(set(numbers)):
        raise ValueError(f"Duplicate PNG part number found for {name}: {numbers}")

    expected = list(range(1, numbers[-1] + 1))
    if numbers != expected:
        raise ValueError(f"Missing PNG parts for {name}: expected {expected}, got {numbers}")

    return ordered


def combine_files(parts: list[Path], output_zip: Path) -> None:
    with output_zip.open("wb") as destination:
        for part in parts:
            with part.open("rb") as source:
                shutil.copyfileobj(source, destination)


def extract_group(
    source_dir: Path,
    name: str,
    parts: list[EmbeddedPart],
    output_dir: Path | None,
    work_root: Path,
    seven_zip: Path,
    overwrite: bool,
    remove_source: bool,
) -> Path:
    ordered = validate_parts(name, parts)
    destination = output_dir or source_dir
    destination.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=safe_temp_prefix(name), dir=work_root) as temp_dir:
        work_path = Path(temp_dir)
        wrappers_dir = work_path / "wrappers"
        split_dir = work_path / "split"
        wrappers_dir.mkdir()
        split_dir.mkdir()

        split_parts: list[Path] = []
        for part in ordered:
            wrapper_name = f"{name}.zip.{part.text}.zip"
            wrapper_path = wrappers_dir / wrapper_name
            shutil.copy2(part.path, wrapper_path)

            run_7zip(seven_zip, ["x", "-y", f"-o{split_dir}", wrapper_path])

            split_part = split_dir / f"{name}.zip.{part.text}"
            if not split_part.is_file():
                raise FileNotFoundError(f"Restored split part was not found: {split_part}")
            split_parts.append(split_part)

        restored_zip = work_path / f"{name}.zip"
        combine_files(split_parts, restored_zip)

        overwrite_mode = "-aoa" if overwrite else "-aos"
        run_7zip(seven_zip, ["x", "-y", overwrite_mode, f"-o{destination}", restored_zip])

    if remove_source:
        for part in ordered:
            part.path.unlink()

    return destination


def run() -> int:
    args = parse_args()
    work_root = resolve_dir(args.work_dir, WORK_DIR)
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    ensure_work_dir(work_root)

    seven_zip = find_7zip()
    groups = group_sources(args.src)

    print(f"Tool root: {Path(__file__).resolve().parent}")
    print(f"Work: {work_root}")
    print(f"7-Zip: {seven_zip}")
    print(f"Will extract {len(groups)} archive(s)")

    for (source_dir, name), parts in groups.items():
        destination = extract_group(
            source_dir=source_dir,
            name=name,
            parts=parts,
            output_dir=output_dir,
            work_root=work_root,
            seven_zip=seven_zip,
            overwrite=args.overwrite,
            remove_source=args.remove_source,
        )
        print(f"Completed {name} -> {destination}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parent
BASE_DIR = ROOT_DIR / "base"
OUTPUT_DIR = ROOT_DIR / "outputs"
WORK_DIR = ROOT_DIR / "work"

MARKER = "-S7e4H1ln16-"
DEFAULT_VOLUME_SIZE = "100m"
DEFAULT_7ZIP = Path(r"C:\Program Files\7-Zip\7z.exe")

_SPLIT_PART_RE = re.compile(r"^(?P<name>.+)\.zip\.(?P<part>\d{3,})$")
_PNG_PART_RE = re.compile(
    rf"^(?P<name>.+){re.escape(MARKER)}\.(?P<part>\d{{3,}})\.png$",
    re.IGNORECASE,
)


def resolve_dir(value: str | None, default: Path) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return default


def find_7zip() -> Path:
    candidates: list[Path] = []
    if configured := os.environ.get("FILE2PNG_7ZIP"):
        candidates.append(Path(configured))

    candidates.append(DEFAULT_7ZIP)

    for command in ("7z.exe", "7z", "7zz.exe", "7zz"):
        if found := shutil.which(command):
            candidates.append(Path(found))

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "7-Zip executable was not found. Install 7-Zip or set FILE2PNG_7ZIP."
    )


def run_7zip(exe: Path, args: Iterable[object], cwd: Path | None = None) -> None:
    command = [str(exe), *(str(arg) for arg in args)]
    subprocess.run(command, cwd=cwd, check=True)


def ensure_work_dir(work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)


def list_base_pngs(base_dir: Path) -> list[Path]:
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Base PNG directory does not exist: {base_dir}")

    pngs = sorted(
        path for path in base_dir.iterdir() if path.is_file() and path.suffix.lower() == ".png"
    )
    if not pngs:
        raise FileNotFoundError(f"No PNG files found in base directory: {base_dir}")
    return pngs


def prepare_output_dir(output_dir: Path, replace: bool) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        if not replace:
            raise FileExistsError(
                f"Output directory is not empty: {output_dir}. "
                "Remove it or pass --replace."
            )
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)


def split_part_to_png_name(part_name: str) -> str:
    match = _SPLIT_PART_RE.match(part_name)
    if not match:
        raise ValueError(f"Unexpected split archive part name: {part_name}")
    return f"{match.group('name')}{MARKER}.{match.group('part')}.png"


def parse_png_part_name(path: Path) -> tuple[str, int, str]:
    match = _PNG_PART_RE.match(path.name)
    if not match:
        raise ValueError(
            f"Unexpected embedded PNG name: {path.name}. "
            f"Expected '<name>{MARKER}.001.png'."
        )
    part_text = match.group("part")
    return match.group("name"), int(part_text), part_text


def safe_temp_prefix(name: str) -> str:
    prefix = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
    return (prefix or "file2png")[:60] + "_"

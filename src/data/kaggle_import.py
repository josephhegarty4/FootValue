from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def _collect_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*") if path.is_file())


def _import_with_kagglehub(
    dataset: str,
    output_dir: Path,
    file_name: str | None = None,
) -> list[Path]:
    try:
        import kagglehub
    except Exception as error:
        raise RuntimeError("kagglehub is not installed. Install with `pip install kagglehub`.") from error

    downloaded_path = Path(kagglehub.dataset_download(dataset))
    source_files = _collect_files(downloaded_path)
    if file_name is not None:
        source_files = [path for path in source_files if path.name == file_name]

    if not source_files:
        raise RuntimeError(
            f"No files found for dataset '{dataset}'"
            + (f" with file_name='{file_name}'" if file_name else "")
        )

    imported_files: list[Path] = []
    for source_file in source_files:
        destination_file = output_dir / source_file.name
        shutil.copy2(source_file, destination_file)
        imported_files.append(destination_file)
    return imported_files


def _import_with_kaggle_cli(
    dataset: str,
    output_dir: Path,
    file_name: str | None = None,
    unzip: bool = True,
) -> list[Path]:
    kaggle_path = shutil.which("kaggle")
    if kaggle_path is None:
        raise RuntimeError(
            "Kaggle CLI not found. Install with `pip install kaggle` and ensure `kaggle` is on PATH."
        )

    command = [kaggle_path, "datasets", "download", "-d", dataset, "-p", str(output_dir)]
    if file_name:
        command.extend(["-f", file_name])
    if unzip:
        command.append("--unzip")

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"Kaggle import failed: {stderr or result.stdout.strip()}")

    return sorted(path for path in output_dir.iterdir() if path.is_file())


def run_kaggle_import(
    dataset: str,
    output_dir: str | Path,
    file_name: str | None = None,
    unzip: bool = True,
    backend: str = "kagglehub",
) -> list[Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    normalized_backend = backend.lower().strip()
    if normalized_backend == "kagglehub":
        return _import_with_kagglehub(dataset=dataset, output_dir=destination, file_name=file_name)
    if normalized_backend == "kaggle-cli":
        return _import_with_kaggle_cli(dataset=dataset, output_dir=destination, file_name=file_name, unzip=unzip)
    raise ValueError("backend must be 'kagglehub' or 'kaggle-cli'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download dataset files from Kaggle")
    parser.add_argument("--dataset", required=True, help="Kaggle dataset slug, e.g. owner/dataset")
    parser.add_argument("--output-dir", default="src/data/raw/incoming", help="Directory to save downloaded files")
    parser.add_argument("--file-name", default=None, help="Optional specific file inside dataset")
    parser.add_argument("--no-unzip", action="store_true", help="Do not unzip downloaded archive")
    parser.add_argument("--backend", default="kagglehub", choices=["kagglehub", "kaggle-cli"], help="Download backend")
    args = parser.parse_args()

    imported_files = run_kaggle_import(
        dataset=args.dataset,
        output_dir=args.output_dir,
        file_name=args.file_name,
        unzip=not args.no_unzip,
        backend=args.backend,
    )

    print("Imported files:")
    for path in imported_files:
        print(path)

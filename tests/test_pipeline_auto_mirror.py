from pathlib import Path
import os
import time

from src.pipeline_phase1 import _resolve_mirror_csv_path


def test_resolve_latest_csv_from_incoming(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    incoming.mkdir(parents=True, exist_ok=True)

    older = incoming / "older.csv"
    newer = incoming / "newer.csv"

    older.write_text("a,b\n1,2\n", encoding="utf-8")
    newer.write_text("a,b\n3,4\n", encoding="utf-8")

    now = time.time()
    os.utime(older, (now - 10, now - 10))
    os.utime(newer, (now, now))

    resolved = _resolve_mirror_csv_path(
        fbref_mirror_csv=None,
        auto_fbref_mirror=True,
        incoming_dir=incoming,
    )

    assert resolved == newer

from pathlib import Path
import hashlib
import pandas as pd


def calculate_sha256(file_path):
    sha = hashlib.sha256()

    with open(file_path, "rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024), b""
        ):
            sha.update(block)

    return sha.hexdigest()


def detect_duplicates(data_path):
    rows = []

    for path in sorted(
        Path(data_path).rglob("*.pdf")
    ):
        rows.append({
            "filename": path.name,
            "path": str(path),
            "sha256": calculate_sha256(path)
        })

    df = pd.DataFrame(
        rows,
        columns=["filename", "path", "sha256"]
    )

    return df[
        df.duplicated("sha256", keep=False)
    ].copy()

from datetime import datetime, timezone
from pathlib import Path
import json


def save_quality_report(records, findings, duplicates, output_path):
    errors = int(
        (findings["severity"] == "ERROR").sum()
    )
    warnings = int(
        (findings["severity"] == "WARNING").sum()
    )

    report = {
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "documents": len(set(
            r["document_id"] for r in records
        )),
        "pages": len(records),
        "native_pages": sum(
            r["extraction_method"] == "NATIVE"
            for r in records
        ),
        "ocr_pages": sum(
            r["extraction_method"] == "OCR"
            for r in records
        ),
        "quality_errors": errors,
        "quality_warnings": warnings,
        "duplicate_file_entries": len(duplicates),
        "findings": findings.to_dict(
            orient="records"
        )
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True, exist_ok=True
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return report

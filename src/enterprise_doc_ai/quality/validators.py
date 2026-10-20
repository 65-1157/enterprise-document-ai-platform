import re
import pandas as pd

REQUIRED_FIELDS = [
    "document_id",
    "filename",
    "relative_path",
    "page_number",
    "text",
    "extraction_method"
]


def validate_records(records, min_characters=40):
    """Return page-level data-quality findings."""

    findings = []
    seen_pages = set()

    for idx, record in enumerate(records):

        document = record.get("filename", "UNKNOWN")
        page = record.get("page_number")

        def add(rule, severity, detail):
            findings.append({
                "record_index": idx,
                "filename": document,
                "page_number": page,
                "rule": rule,
                "severity": severity,
                "detail": detail
            })

        for field in REQUIRED_FIELDS:
            value = record.get(field)

            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                add(
                    "MISSING_FIELD",
                    "ERROR",
                    f"Missing or empty field: {field}"
                )

        text = record.get("text", "")
        if not isinstance(text, str):
            text = ""

        clean = re.sub(r"\\s+", " ", text).strip()

        if not clean:
            add(
                "EMPTY_TEXT",
                "ERROR",
                "No usable extracted text."
            )
        elif len(clean) < min_characters:
            add(
                "SHORT_TEXT",
                "WARNING",
                f"Only {len(clean)} characters."
            )

        if type(page) is not int or page < 1:
            add(
                "INVALID_PAGE",
                "ERROR",
                "Page number must be positive."
            )

        doc_id = record.get("document_id")

        if doc_id and type(page) is int and page >= 1:
            key = (doc_id, page)

            if key in seen_pages:
                add(
                    "DUPLICATE_PAGE",
                    "ERROR",
                    "Repeated document ID and page."
                )
            else:
                seen_pages.add(key)

        if record.get("extraction_method") not in (
            "NATIVE", "OCR"
        ):
            add(
                "INVALID_METHOD",
                "ERROR",
                "Unexpected extraction method."
            )

    return pd.DataFrame(
        findings,
        columns=[
            "record_index", "filename", "page_number",
            "rule", "severity", "detail"
        ]
    )

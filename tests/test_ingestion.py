from pathlib import Path
import sys
from copy import deepcopy

import pytest

# Enable src-layout imports in Colab and local execution
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_doc_ai.ingestion.pdf_extractor import extract_pdf
from enterprise_doc_ai.quality.validators import validate_records
from enterprise_doc_ai.quality.duplicates import (
    calculate_sha256,
    detect_duplicates
)

DATA = ROOT / "sample_data"
PDF_FILES = sorted(DATA.rglob("*.pdf"))


@pytest.fixture(scope="module")
def extracted_records():
    records = []

    for pdf_path in PDF_FILES:
        records.extend(extract_pdf(pdf_path, root=ROOT))

    return records


def test_dataset_contains_six_documents():
    assert len(PDF_FILES) == 6


def test_native_and_ocr_extraction(extracted_records):
    assert len(extracted_records) == 6

    native = [
        r for r in extracted_records
        if r["extraction_method"] == "NATIVE"
    ]

    ocr = [
        r for r in extracted_records
        if r["extraction_method"] == "OCR"
    ]

    assert len(native) == 5
    assert len(ocr) == 1

    assert "USD 2 million" in ocr[0]["text"]


def test_metadata_integrity(extracted_records):
    for record in extracted_records:
        assert record["document_id"]
        assert record["filename"]
        assert record["relative_path"]
        assert record["page_number"] >= 1
        assert record["text"].strip()


def test_clean_dataset_passes(extracted_records):
    findings = validate_records(extracted_records)

    errors = findings[
        findings["severity"] == "ERROR"
    ]

    assert errors.empty


def test_fault_detection(extracted_records):
    faulty = deepcopy(extracted_records)

    bad = deepcopy(faulty[0])
    bad["document_id"] = "bad_test_document"
    bad["filename"] = "bad.pdf"
    bad["text"] = ""

    faulty.append(bad)
    faulty.append(deepcopy(faulty[0]))

    findings = validate_records(faulty)
    rules = set(findings["rule"])

    assert "EMPTY_TEXT" in rules
    assert "DUPLICATE_PAGE" in rules


def test_no_duplicate_documents():
    duplicates = detect_duplicates(DATA)

    assert duplicates.empty

    hashes = [
        calculate_sha256(p)
        for p in PDF_FILES
    ]

    assert len(hashes) == len(set(hashes))

from pathlib import Path
import hashlib
import io
import time

import pymupdf
import pytesseract
from PIL import Image


def extract_pdf(pdf_path, root=None, dpi=200):
    """
    Extract page-level text from a PDF.

    Uses native extraction first and OCR when the
    page contains no native text.

    Parameters
    ----------
    pdf_path : str or Path
        PDF file to process.
    root : str or Path, optional
        Project root for relative paths.
    dpi : int
        Resolution for OCR rendering.

    Returns
    -------
    list[dict]
        One normalized record per page.
    """

    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    if dpi <= 0:
        raise ValueError("DPI must be positive.")

    document_id = hashlib.sha256(
        pdf_path.read_bytes()
    ).hexdigest()[:16]

    if root is None:
        relative_path = pdf_path.name
    else:
        relative_path = str(
            pdf_path.relative_to(Path(root).resolve())
        )

    records = []

    with pymupdf.open(pdf_path) as doc:

        for page_index, page in enumerate(doc):

            start = time.perf_counter()
            text = page.get_text("text").strip()

            if text:
                method = "NATIVE"
            else:
                method = "OCR"

                pix = page.get_pixmap(
                    dpi=dpi,
                    colorspace=pymupdf.csRGB,
                    alpha=False
                )

                image = Image.open(
                    io.BytesIO(pix.tobytes("png"))
                ).convert("RGB")

                text = pytesseract.image_to_string(
                    image,
                    lang="eng",
                    config="--psm 6"
                ).strip()

            records.append({
                "document_id": document_id,
                "filename": pdf_path.name,
                "relative_path": relative_path,
                "page_number": page_index + 1,
                "text": text,
                "characters": len(text),
                "extraction_method": method,
                "processing_seconds": round(
                    time.perf_counter() - start, 4
                )
            })

    return records

"""Extract text from each page of a PDF and save it to a plain-text file."""

import sys
from pathlib import Path

import pdfplumber

MIN_ARGS = 3  # script name + <pdf_path> + <output_path>
USAGE = "Usage: uv run extract_pdf.py <pdf_path> <output_path>"


def extract_text_from_pdf(pdf_path: str, output_path: str) -> bool:
    """Extract text from each page of a PDF and save it to a text file."""
    if not Path(pdf_path).exists():
        print(f"[ERROR] PDF file not found: {pdf_path}")
        return False

    try:
        print(f"Opening {pdf_path}...")
        with pdfplumber.open(pdf_path) as pdf:
            text: str = ""
            total_pages: int = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                print(f"Extracting page {i + 1}/{total_pages}...")
                page_text: str | None = page.extract_text()
                if page_text:
                    text += f"--- Page {i + 1} ---\n"
                    text += page_text + "\n\n"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with Path(output_path).open("w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        print(f"[ERROR] Failed to extract text: {e}")
        return False

    print(f"Done! Text saved to {output_path}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < MIN_ARGS:
        print(USAGE)
        sys.exit(1)
    extract_text_from_pdf(sys.argv[1], sys.argv[2])

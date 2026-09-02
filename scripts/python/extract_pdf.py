# /// script
# dependencies = ["pdfplumber"]
# ///
import os

import pdfplumber


def extract_text_from_pdf(pdf_path: str, output_path: str) -> bool:
    """
    Extracts text from each page of a PDF and saves it to a text file.
    """
    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF file not found: {pdf_path}")
        return False

    try:
        print(f"Opening {pdf_path}...")
        with pdfplumber.open(pdf_path) as pdf:
            text: str = ""
            total_pages: int = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                print(f"Extracting page {i+1}/{total_pages}...")
                page_text: str | None = page.extract_text()
                if page_text:
                    text += f"--- Page {i+1} ---\n"
                    text += page_text + "\n\n"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Done! Text saved to {output_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to extract text: {e}")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: uv run extract_pdf.py <pdf_path> <output_path>")
        sys.exit(1)
    extract_text_from_pdf(sys.argv[1], sys.argv[2])

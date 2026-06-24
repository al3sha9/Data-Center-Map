from __future__ import annotations

import pdfplumber

from common import (
    EXTRACTED_DIR,
    clean_text,
    detect_title,
    ensure_dirs,
    extract_captions,
    extract_headings,
    keyword_hits_for_text,
    pdf_files,
    stable_slug,
    write_json,
)


def index_pdf(path):
    with pdfplumber.open(path) as pdf:
        source_id = stable_slug(path.stem)
        first_text = clean_text(pdf.pages[0].extract_text() if pdf.pages else "")
        index = {
            "source_id": source_id,
            "filename": path.name,
            "title": detect_title(path.name, first_text),
            "page_count": len(pdf.pages),
            "table_of_contents": [],
            "headings": [],
            "figures": [],
            "tables": [],
            "keyword_hits": [],
        }
        try:
            toc = getattr(pdf, "doc", None)
            if toc and hasattr(toc, "get_outlines"):
                outlines = []
                for item in toc.get_outlines() or []:
                    outlines.append({"text": str(item)[:300]})
                index["table_of_contents"] = outlines
        except Exception:
            index["table_of_contents"] = []

        for i, page in enumerate(pdf.pages, start=1):
            text = clean_text(page.extract_text())
            if not text:
                continue
            index["headings"].extend(extract_headings(text, i))
            index["figures"].extend(extract_captions(text, i, "Figure"))
            index["tables"].extend(extract_captions(text, i, "Table"))
            index["keyword_hits"].extend(keyword_hits_for_text(text, i))
        return index


def main() -> None:
    ensure_dirs()
    indexes = [index_pdf(path) for path in pdf_files()]
    write_json(EXTRACTED_DIR / "pdf_index.json", indexes)
    print(f"Indexed {len(indexes)} PDFs -> data/extracted/pdf_index.json")


if __name__ == "__main__":
    main()

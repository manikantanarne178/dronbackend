import fitz  # PyMuPDF


class PDFParser:

    @staticmethod
    def parse(file_path: str):
        doc = fitz.open(file_path)

        pages = []
        full_text = ""

        for page_number, page in enumerate(doc):
            text = page.get_text()

            pages.append({
                "page": page_number + 1,
                "width": page.rect.width,
                "height": page.rect.height,
                "text": text
            })

            full_text += text + "\n"

        metadata = doc.metadata

        result = {
            "type": "pdf",
            "page_count": len(doc),
            "metadata": {
                "title": metadata.get("title"),
                "author": metadata.get("author"),
                "creator": metadata.get("creator"),
                "producer": metadata.get("producer"),
                "subject": metadata.get("subject"),
            },
            "pages": pages,
            "text": full_text.strip()
        }

        doc.close()

        return result
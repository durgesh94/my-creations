
import pymupdf
import re

PDF_PATH = "../documents/hospital_policy_v1.0.pdf"


def normalize_text(text):

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Preserve headings such as:
    # 1. Patient Registration Policy
    # 2. Appointment Booking Policy
    text = re.sub(
        r"(?m)(?<!\n)(\n?)(\d+\.\s+[A-Z][^\n]*)",
        r"\n\n\2",
        text
    )

    # Preserve the document title and important labels
    text = re.sub(
        r"(?m)(?<!\n)(HOSPITAL POLICY HANDBOOK|Document ID:|Important:)",
        r"\n\n\1",
        text
    )

    # Merge line breaks inside sentences, but preserve:
    # - Blank lines
    # - Bullet points
    text = re.sub(
        r"(?<!\n)\n(?!\n|[ \t]*[•\-])",
        " ",
        text
    )

    # Reduce excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


doc = pymupdf.open(PDF_PATH)

pages = []

for page_number, page in enumerate(doc):

    text = page.get_text()

    # Remove repeated header
    text = re.sub(
        r"HSP-POL-001 \| Fictional RAG training sample",
        "",
        text
    )

    # Remove page numbers
    text = re.sub(r"Page \d+", "", text)

    # Normalize extracted text
    text = normalize_text(text)

    pages.append({
        "document_id": "HSP-POL-001",
        "page_number": page_number + 1,
        "text": text
    })

doc.close()


for page in pages:
    print(f"\n--- Page {page['page_number']} ---")
    print(page["text"])

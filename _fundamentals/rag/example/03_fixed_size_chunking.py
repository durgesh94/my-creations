
import pymupdf
import re

PDF_PATH = "../documents/hospital_policy_v1.0.pdf"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def normalize_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# Step 1: Load PDF
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

    # Remove page number
    text = re.sub(r"Page \d+", "", text)

    # Normalize extracted text
    text = normalize_text(text)

    pages.append({
        "document_id": "HSP-POL-001",
        "page_number": page_number + 1,
        "text": text
    })

doc.close()


# Step 2: Fixed-size chunking
def fixed_size_chunking(text, chunk_size, overlap):

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Overlap must be >= 0 and smaller than chunk size")

    chunks = []

    step_size = chunk_size - overlap

    for start in range(0, len(text), step_size):
        end = start + chunk_size

        chunk_text = text[start:end]

        if not chunk_text:
            break

        chunks.append(chunk_text)

    return chunks


# Step 3: Create chunks with metadata
all_chunks = []

for page in pages:

    page_chunks = fixed_size_chunking(
        page["text"],
        CHUNK_SIZE,
        CHUNK_OVERLAP
    )

    for chunk_index, chunk_text in enumerate(page_chunks):

        all_chunks.append({
            "chunk_id": f"page_{page['page_number']}_chunk_{chunk_index + 1}",
            "document_id": page["document_id"],
            "page_number": page["page_number"],
            "text": chunk_text
        })


# Step 4: Display results
print("Total Pages:", len(pages))
print("Total Chunks:", len(all_chunks))

for chunk in all_chunks:
    print("\n" + "=" * 60)
    print("Chunk ID:", chunk["chunk_id"])
    print("Document ID:", chunk["document_id"])
    print("Page Number:", chunk["page_number"])
    print("Character Count:", len(chunk["text"]))
    print("Text:", chunk["text"])

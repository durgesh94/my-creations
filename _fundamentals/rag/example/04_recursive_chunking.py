
import pymupdf
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

PDF_PATH = "../documents/hospital_policy_v1.0.pdf"

# Step 1: Load and clean PDF
doc = pymupdf.open(PDF_PATH)

pages = []

for page_number, page in enumerate(doc):
    text = page.get_text()

    text = re.sub(
        r"HSP-POL-001 \| Fictional RAG training sample",
        "",
        text
    )

    text = re.sub(r"Page \d+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    pages.append({
        "document_id": "HSP-POL-001",
        "page_number": page_number + 1,
        "text": text.strip()
    })

doc.close()


# Step 2: Configure recursive splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len
)


# Step 3: Generate chunks
all_chunks = []

for page in pages:

    page_chunks = text_splitter.split_text(page["text"])

    for chunk_index, chunk_text in enumerate(page_chunks):

        all_chunks.append({
            "chunk_id": f"page_{page['page_number']}_chunk_{chunk_index + 1}",
            "document_id": page["document_id"],
            "page_number": page["page_number"],
            "text": chunk_text
        })


# Step 4: Display results
print("Total Pages:", len(pages))
print("Total Recursive Chunks:", len(all_chunks))

for chunk in all_chunks:
    print("\n" + "=" * 60)
    print("Chunk ID:", chunk["chunk_id"])
    print("Page Number:", chunk["page_number"])
    print("Character Count:", len(chunk["text"]))
    print("Text:", chunk["text"])

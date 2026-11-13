
import pymupdf
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

PDF_PATH = "../documents/hospital_policy_v1.0.pdf"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


# Step 1: Load PDF and collect text
doc = pymupdf.open(PDF_PATH)

document_text = ""

for page in doc:
    text = page.get_text()

    # Remove repeated header
    text = re.sub(
        r"HSP-POL-001 \| Fictional RAG training sample",
        "",
        text
    )

    # Remove page numbers
    text = re.sub(r"Page \d+", "", text)

    document_text += text + "\n"

doc.close()


# Step 2: Normalize text
document_text = document_text.replace("\r\n", "\n")
document_text = re.sub(r"[ \t]+", " ", document_text)
document_text = re.sub(r"\n{3,}", "\n\n", document_text)
document_text = document_text.strip()


# Step 3: Identify section headings
heading_pattern = r"(?m)^\s*(\d+\.\s+[^\n]+)\s*$"

matches = list(re.finditer(heading_pattern, document_text))

sections = []

for index, match in enumerate(matches):

    section_title = match.group(1).strip()

    start = match.start()

    if index + 1 < len(matches):
        end = matches[index + 1].start()
    else:
        end = len(document_text)

    section_text = document_text[start:end].strip()

    sections.append({
        "section_title": section_title,
        "text": section_text
    })


# Step 4: Configure recursive splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len
)


# Step 5: Split each section separately
all_chunks = []

for section_index, section in enumerate(sections):

    section_title = section["section_title"]

    section_chunks = text_splitter.split_text(section["text"])

    for chunk_index, chunk_text in enumerate(section_chunks):

        all_chunks.append({
            "chunk_id": f"section_{section_index + 1}_chunk_{chunk_index + 1}",
            "section_title": section_title,
            "document_id": "HSP-POL-001",
            "text": chunk_text
        })


# Step 6: Display results
print("Total Sections:", len(sections))
print("Total Structure-Aware Chunks:", len(all_chunks))

for chunk in all_chunks:

    print("\n" + "=" * 60)
    print("Chunk ID:", chunk["chunk_id"])
    print("Section:", chunk["section_title"])
    print("Character Count:", len(chunk["text"]))
    print("Text:", chunk["text"])

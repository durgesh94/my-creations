
import pymupdf
import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

PDF_PATH = "../documents/hospital_policy_v1.0.pdf"

SIMILARITY_THRESHOLD = 0.5

DOCUMENT_ID = "HSP-POL-001"

MODEL_NAME = "all-MiniLM-L6-v2"


# --------------------------------------------------
# 2. Load and clean PDF
# --------------------------------------------------

doc = pymupdf.open(PDF_PATH)

pages = []

for page_number, page in enumerate(doc):

    text = page.get_text()

    # Remove repeated PDF header
    text = re.sub(
        r"HSP-POL-001 \| Fictional RAG training sample",
        "",
        text
    )

    # Remove page numbers
    text = re.sub(r"Page \d+", "", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Preserve bullet boundaries, merge other line breaks
    text = re.sub(
        r"\n[ \t]*([•\-])\s*",
        r"\n\1 ",
        text
    )

    text = re.sub(
        r"(?<!\n)\n(?![ \t]*[•\-])",
        " ",
        text
    )

    text = re.sub(r"\n{3,}", "\n\n", text)

    pages.append({
        "document_id": DOCUMENT_ID,
        "page_number": page_number + 1,
        "text": text.strip()
    })

doc.close()

# --------------------------------------------------
# 3. Extract sections using headings
# --------------------------------------------------

# Find numbered headings even when they appear
# in the middle of an extracted text line.
heading_pattern = re.compile(
    r"(?<!\d)(\d+\.\s*(?:\n\s*)?[A-Z][^\n]*)"
)

sections = []
current_section = None

for page in pages:

    page_text = page["text"]

    matches = list(heading_pattern.finditer(page_text))

    cursor = 0

    for match in matches:

        # Text before the next heading belongs
        # to the previous section.
        previous_text = page_text[cursor:match.start()].strip()

        if current_section and previous_text:
            current_section["text"] += "\n" + previous_text

        # Finish the previous section
        if current_section:
            sections.append(current_section)

        # Start a new section
        current_section = {
            "document_id": page["document_id"],
            "page_number": page["page_number"],
            "page_numbers": [page["page_number"]],
            "section_title": " ".join(match.group(1).split()),
            "text": ""
        }

        cursor = match.end()

    # Remaining text belongs to the current section.
    remaining_text = page_text[cursor:].strip()

    if current_section and remaining_text:

        current_section["text"] += "\n" + remaining_text

        if page["page_number"] not in current_section["page_numbers"]:
            current_section["page_numbers"].append(
                page["page_number"]
            )

# Add the final section
if current_section:
    sections.append(current_section)


# --------------------------------------------------
# 4. Split section text into sentences
# --------------------------------------------------

def split_into_sentences(text):

    # Split after sentence-ending punctuation.
    # Also preserve separate bullet points.
    parts = re.split(
        r"(?<=[.!?])\s+|\n(?=[•\-])",
        text
    )

    sentences = []

    for part in parts:

        sentence = part.strip()
        sentence = sentence.lstrip("•- ").strip()

        if sentence:
            sentences.append(sentence)

    return sentences


# --------------------------------------------------
# 5. Load embedding model
# --------------------------------------------------

model = SentenceTransformer(MODEL_NAME)


# --------------------------------------------------
# 6. Semantic chunking
# --------------------------------------------------

def semantic_chunking(
    sentences,
    embeddings,
    threshold
):

    chunks = []

    current_chunk = [sentences[0]]

    for index in range(1, len(sentences)):

        similarity = cosine_similarity(
            [embeddings[index - 1]],
            [embeddings[index]]
        )[0][0]

        print(
            f"Sentence {index} vs Sentence {index + 1}: "
            f"{similarity:.4f}"
        )

        if similarity < threshold:

            # Topic change: finish the current chunk
            chunks.append(current_chunk)

            # Start a new chunk
            current_chunk = [sentences[index]]

        else:

            # Similar meaning: keep sentences together
            current_chunk.append(sentences[index])

    # Add the remaining sentences
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# --------------------------------------------------
# 7. Process every section
# --------------------------------------------------

all_chunks = []

for section in sections:

    sentences = split_into_sentences(section["text"])

    if not sentences:
        continue

    # Generate sentence embeddings
    embeddings = model.encode(sentences)

    print("\n" + "=" * 70)
    print("Section:", section["section_title"])
    print("Total Sentences:", len(sentences))

    # Create semantic chunks
    semantic_chunks = semantic_chunking(
        sentences,
        embeddings,
        SIMILARITY_THRESHOLD
    )

    # Store chunks with metadata
    for chunk_index, chunk_sentences in enumerate(
        semantic_chunks
    ):

        chunk_text = " ".join(chunk_sentences)

        all_chunks.append({
            "chunk_id": (
                f"page_{section['page_number']}_"
                f"section_{len(all_chunks) + 1}"
            ),
            "document_id": section["document_id"],
            "page_number": section["page_number"],
            "section_title": section["section_title"],
            "text": (
                f"Section: {section['section_title']}\n\n"
                f"{chunk_text}"
            )
        })


# --------------------------------------------------
# 8. Display final results
# --------------------------------------------------

print("\n\n" + "#" * 70)
print("SEMANTIC CHUNKING RESULTS")
print("#" * 70)

print("Total Pages:", len(pages))
print("Total Sections:", len(sections))
print("Total Semantic Chunks:", len(all_chunks))

for chunk in all_chunks:

    print("\n" + "-" * 70)

    print("Chunk ID:", chunk["chunk_id"])
    print("Document ID:", chunk["document_id"])
    print("Page Number:", chunk["page_number"])
    print("Section:", chunk["section_title"])

    print("Character Count:", len(chunk["text"]))

    print("\nChunk Text:")
    print(chunk["text"])

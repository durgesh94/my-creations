
def chunk_text(text):
    # Split document into non-empty paragraphs
    blocks = [
        block.strip()
        for block in text.split("\n\n")
        if block.strip()
    ]

    chunks = []
    document_title = None
    i = 0

    while i < len(blocks):
        block = blocks[i]

        # Preserve the document title
        if block == "Hospital Admission Policy":
            document_title = block
            i += 1
            continue

        # Combine a section heading with its content
        if block.endswith(":") and i + 1 < len(blocks):
            section = f"{block}\n\n{blocks[i + 1]}"
            i += 2
        else:
            section = block
            i += 1

        if document_title:
            section = f"{document_title}\n\n{section}"

        chunks.append(section)

    return chunks


if __name__ == "__main__":
    with open("documents/hospital_policy.txt", "r") as file:
        document = file.read()

    chunks = chunk_text(document)

    for index, chunk in enumerate(chunks):
        print(f"\n--- Chunk {index + 1} ---")
        print(chunk)

    print("\nTotal chunks:", len(chunks))

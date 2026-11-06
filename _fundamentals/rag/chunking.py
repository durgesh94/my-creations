def chunk_text(text, chunk_size=200, overlap=40):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


with open("documents/hospital_policy.txt", "r") as file:
    document = file.read()


chunks = chunk_text(document)

for index, chunk in enumerate(chunks):

    print(f"\n--- Chunk {index + 1} ---")

    print(chunk)
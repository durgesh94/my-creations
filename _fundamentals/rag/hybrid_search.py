import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from chunking import chunk_text


# ---------------------------------
# 1. Load hospital policy document
# ---------------------------------

with open("documents/hospital_policy.txt", "r") as file:
    document = file.read()

chunks = chunk_text(document)

print("Total chunks:", len(chunks))


# ---------------------------------
# 2. Initialize BM25 keyword search
# ---------------------------------

tokenized_chunks = [
    chunk.lower().split()
    for chunk in chunks
]

bm25 = BM25Okapi(tokenized_chunks)


# ---------------------------------
# 3. Initialize vector search
# ---------------------------------

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(path="./chroma_db")

collection = chroma_client.get_collection(
    name="hams_hospital_policies"
)


# ---------------------------------
# 4. User question
# ---------------------------------

question = "Can I cancel my appointment one day before?"

# question = "What happens if I terminate my booking 24 hours in advance?"


# ---------------------------------
# 5. BM25 retrieval
# ---------------------------------

tokenized_query = question.lower().split()

bm25_scores = bm25.get_scores(tokenized_query)

bm25_ranked = sorted(
    enumerate(bm25_scores),
    key=lambda item: item[1],
    reverse=True
)

# Ignore documents with zero keyword relevance
bm25_ranked_ids = [
    f"policy_{index}"
    for index, score in bm25_ranked
    if score > 0
]


# ---------------------------------
# 6. Vector retrieval
# ---------------------------------

query_embedding = embedding_model.encode(question).tolist()

vector_results = collection.query(
    query_embeddings=[query_embedding],
    n_results=len(chunks)
)

vector_ranked_ids = vector_results["ids"][0]


# ---------------------------------
# 7. Reciprocal Rank Fusion (RRF)
# ---------------------------------

def reciprocal_rank_fusion(rankings, k=60):

    fused_scores = {}

    for ranking in rankings:

        for rank, doc_id in enumerate(ranking, start=1):

            score = 1 / (k + rank)

            fused_scores[doc_id] = (
                fused_scores.get(doc_id, 0) + score
            )

    return sorted(
        fused_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )


hybrid_results = reciprocal_rank_fusion([
    bm25_ranked_ids,
    vector_ranked_ids
])


# ---------------------------------
# 8. Display results
# ---------------------------------

print("\n========== BM25 RESULTS ==========")

for doc_id in bm25_ranked_ids:
    index = int(doc_id.split("_")[1])
    print(f"\n{doc_id}: {chunks[index]}")


print("\n========== VECTOR RESULTS ==========")

for doc_id in vector_ranked_ids:
    index = int(doc_id.split("_")[1])
    print(f"\n{doc_id}: {chunks[index]}")


print("\n========== HYBRID SEARCH RESULTS ==========")

for doc_id, score in hybrid_results:

    index = int(doc_id.split("_")[1])

    print(f"\nDocument ID: {doc_id}")
    print(f"RRF Score: {score:.6f}")
    print(f"Document: {chunks[index]}")
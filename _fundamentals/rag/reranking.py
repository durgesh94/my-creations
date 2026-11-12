
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

from chunking import chunk_text


# ==========================================
# 1. LOAD AND CHUNK HOSPITAL POLICY DOCUMENT
# ==========================================

with open("documents/hospital_policy.txt", "r") as file:
    document = file.read()

chunks = chunk_text(document)

print("Total chunks:", len(chunks))


# ==========================================
# 2. INITIALIZE BM25 KEYWORD SEARCH
# ==========================================

tokenized_chunks = [
    chunk.lower().split()
    for chunk in chunks
]

bm25 = BM25Okapi(tokenized_chunks)


# ==========================================
# 3. INITIALIZE VECTOR SEARCH
# ==========================================

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_collection(
    name="hams_hospital_policies"
)


# ==========================================
# 4. USER QUESTION
# ==========================================

question = "Can I cancel my appointment one day before?"

# Alternative test:
# question = "What is the refund policy for cancelled surgeries?"


# ==========================================
# 5. BM25 RETRIEVAL
# ==========================================

tokenized_query = question.lower().split()

bm25_scores = bm25.get_scores(tokenized_query)

bm25_ranked = sorted(
    enumerate(bm25_scores),
    key=lambda item: item[1],
    reverse=True
)

# Keep only documents with positive keyword scores
bm25_ranked_ids = [
    f"policy_{index}"
    for index, score in bm25_ranked
    if score > 0
]


# ==========================================
# 6. VECTOR RETRIEVAL
# ==========================================

query_embedding = embedding_model.encode(
    question
).tolist()

vector_results = collection.query(
    query_embeddings=[query_embedding],
    n_results=len(chunks)
)

vector_ranked_ids = vector_results["ids"][0]


# ==========================================
# 7. RECIPROCAL RANK FUSION (RRF)
# ==========================================

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


# ==========================================
# 8. DISPLAY BM25 RESULTS
# ==========================================

print("\n========== BM25 RESULTS ==========")

for doc_id in bm25_ranked_ids:

    index = int(doc_id.split("_")[1])

    print(f"\nDocument ID: {doc_id}")
    print("Document:", chunks[index])


# ==========================================
# 9. DISPLAY VECTOR RESULTS
# ==========================================

print("\n========== VECTOR RESULTS ==========")

for doc_id in vector_ranked_ids:

    index = int(doc_id.split("_")[1])

    print(f"\nDocument ID: {doc_id}")
    print("Document:", chunks[index])


# ==========================================
# 10. DISPLAY HYBRID SEARCH RESULTS
# ==========================================

print("\n========== HYBRID SEARCH RESULTS ==========")

for doc_id, score in hybrid_results:

    index = int(doc_id.split("_")[1])

    print(f"\nDocument ID: {doc_id}")
    print(f"RRF Score: {score:.6f}")
    print("Document:", chunks[index])


# ==========================================
# 11. CROSS-ENCODER RERANKING
# ==========================================

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# Select top 4 candidates from hybrid search
candidate_results = hybrid_results[:4]

# Prepare question-document pairs
pairs = []

for doc_id, rrf_score in candidate_results:

    index = int(doc_id.split("_")[1])

    doc = chunks[index]

    pairs.append((question, doc))


# Calculate Cross-Encoder relevance scores
rerank_scores = reranker.predict(pairs)


# Combine documents with their reranking scores
reranked_results = sorted(
    zip(candidate_results, rerank_scores),
    key=lambda item: float(item[1]),
    reverse=True
)


# ==========================================
# 12. DISPLAY FINAL RERANKED RESULTS
# ==========================================

print("\n========== FINAL RERANKED RESULTS ==========")

for (doc_id, rrf_score), rerank_score in reranked_results:

    index = int(doc_id.split("_")[1])

    print(f"\nDocument ID: {doc_id}")
    print(f"Original RRF Score: {rrf_score:.6f}")
    print(f"Cross-Encoder Score: {float(rerank_score):.6f}")
    print("Document:", chunks[index])


# ==========================================
# 13. SELECT TOP DOCUMENT
# ==========================================

if reranked_results:

    best_result = reranked_results[0]

    best_doc_id = best_result[0][0]

    best_index = int(best_doc_id.split("_")[1])

    best_document = chunks[best_index]

    print("\n========== BEST MATCH ==========")
    print("Question:", question)
    print("Best Document:", best_document)

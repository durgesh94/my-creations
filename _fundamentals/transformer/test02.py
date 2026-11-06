from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

sentence1 = "I like cooking"
sentence2 = "I like dancing"

embedding1 = model.encode(sentence1)
embedding2 = model.encode(sentence2)

print("Shape 1:", embedding1.shape)
print("Shape 2:", embedding2.shape)

print("Are embeddings identical:",
      np.allclose(embedding1, embedding2))
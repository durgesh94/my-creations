import tiktoken

encoding = tiktoken.get_encoding("cl100k_base")

text = "I love learning Artificial Intelligence"

tokens = encoding.encode(text)

print("Original Text:", text)
print("Token IDs:", tokens)
print("Total Tokens:", len(tokens))

print("\nIndividual Tokens:")

for token in tokens:
    print(encoding.decode([token]))
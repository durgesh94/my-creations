from transformers import AutoTokenizer

model_name = "distilbert-base-uncased"

tokenizer = AutoTokenizer.from_pretrained(model_name)

text = "Find cardiac doctors"

tokens = tokenizer.tokenize(text)
token_ids = tokenizer.encode(text)

print("Tokens:", tokens)
print("Token IDs:", token_ids)
print("Decoded:", tokenizer.decode(token_ids))


# Note:
# - The `tokenize` method splits the text into individual tokens.
# - The `encode` method converts the text into token IDs.
# - The `decode` method converts token IDs back into human-readable text.
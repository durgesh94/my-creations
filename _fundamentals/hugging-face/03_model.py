from transformers import pipeline

generator = pipeline(
    "text-generation",
    model="HuggingFaceTB/SmolLM2-135M-Instruct",
)

messages = [
    {
        "role": "user",
        "content": "Explain cardiology in one sentence."
    }
]

result = generator(
    messages,
    max_new_tokens=60,
)

print(result)

# Note:
# - The `pipeline` function creates a text generation model.
# - The `messages` list contains the input prompts for the model.
# - `max_new_tokens` specifies the maximum number of tokens to generate.
# - The result is a list of dictionaries with the generated text under the `generated_text` key.
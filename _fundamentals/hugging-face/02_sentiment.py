from transformers import pipeline

classifier = pipeline(
    task="sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
)

result = classifier(
    "The hospital staff was very helpful."
)

print(result)


# Note:
# - The `pipeline` function creates a sentiment analysis classifier.
# - The classifier returns a list of dictionaries with `label` and `score`.
# - `label` indicates the sentiment (e.g., POSITIVE or NEGATIVE).
# - `score` indicates the confidence of the prediction.
# This script demonstrates how to use the OpenAI API to generate content using the GPT model.

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Call OpenAI Responses API
response = client.responses.create(
    model="gpt-5.4-nano",
    input="Explain what RAG is in simple terms."
)

# Print generated response
print(response.output_text)

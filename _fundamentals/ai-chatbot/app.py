
import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types

load_dotenv()

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖"
)

st.title("🤖 My AI Chatbot")

# Select AI provider
provider = st.sidebar.selectbox(
    "Choose AI Provider",
    ["Gemini", "OpenAI"]
)

# Initialize conversation state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "provider" not in st.session_state:
    st.session_state.provider = provider

# Reset history when switching provider
if st.session_state.provider != provider:
    st.session_state.messages = []
    st.session_state.provider = provider

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Display existing messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
prompt = st.chat_input("Ask me anything...")

if prompt:
    api_key_name = (
        "OPENAI_API_KEY"
        if provider == "OpenAI"
        else "GEMINI_API_KEY"
    )

    if not os.getenv(api_key_name):
        st.error(f"Missing {api_key_name} in .env")
        st.stop()

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare conversation history
    history = st.session_state.messages + [
        {"role": "user", "content": prompt}
    ]

    try:
        with st.spinner("AI is thinking..."):

            if provider == "OpenAI":
                client = OpenAI()

                response = client.responses.create(
                    model=os.getenv(
                        "OPENAI_MODEL", "gpt-5.4-nano"
                    ),
                    input=history,
                    store=False
                )

                answer = response.output_text

            else:
                client = genai.Client(
                    api_key=os.getenv("GEMINI_API_KEY")
                )

                contents = [
                    types.Content(
                        role=(
                            "model"
                            if msg["role"] == "assistant"
                            else "user"
                        ),
                        parts=[
                            types.Part.from_text(
                                text=msg["content"]
                            )
                        ]
                    )
                    for msg in history
                ]

                response = client.models.generate_content(
                    model=os.getenv(
                        "GEMINI_MODEL", "gemini-2.5-flash"
                    ),
                    contents=contents
                )

                answer = response.text

        if not answer:
            raise ValueError("Model returned no text.")

        # Save successful conversation
        st.session_state.messages.extend([
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": answer}
        ])

        with st.chat_message("assistant"):
            st.markdown(answer)

    except Exception as error:
        st.error(f"API request failed: {error}")

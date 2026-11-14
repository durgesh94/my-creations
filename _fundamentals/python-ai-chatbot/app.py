
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai

# --------------------------------------------------
# 1. Load environment variables
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# --------------------------------------------------
# 2. Streamlit page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Gemini AI Chatbot",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Gemini AI Chatbot")
st.caption(f"Powered by Google Gemini ({MODEL})")

# --------------------------------------------------
# 3. Validate API key
# --------------------------------------------------

if not API_KEY:
    st.error("GEMINI_API_KEY is missing from .env")
    st.stop()

# --------------------------------------------------
# 4. Initialize Gemini client
# --------------------------------------------------

# Store the client in session state so it survives
# Streamlit reruns.

if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = genai.Client(
        api_key=API_KEY
    )

# --------------------------------------------------
# 5. Initialize Gemini chat session
# --------------------------------------------------

if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = (
        st.session_state.gemini_client.chats.create(
            model=MODEL
        )
    )

# --------------------------------------------------
# 6. Initialize conversation history for UI
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------------------------------
# 7. Sidebar
# --------------------------------------------------

with st.sidebar:
    st.header("⚙️ Chat Settings")

    st.write(f"**Model:** {MODEL}")

    st.divider()

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True
    ):
        # Create a fresh chat session
        st.session_state.gemini_chat = (
            st.session_state.gemini_client.chats.create(
                model=MODEL
            )
        )

        # Clear displayed messages
        st.session_state.messages = []

        st.rerun()

# --------------------------------------------------
# 8. Display previous messages
# --------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --------------------------------------------------
# 9. Chat input
# --------------------------------------------------

prompt = st.chat_input("Ask Gemini anything...")

if prompt:

    # Display current user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # --------------------------------------------------
    # 10. Generate Gemini response
    # --------------------------------------------------

    with st.chat_message("assistant"):

        try:
            with st.spinner("Gemini is thinking..."):

                response = (
                    st.session_state.gemini_chat.send_message(
                        prompt
                    )
                )

                answer = response.text

                if not answer:
                    raise ValueError(
                        "Gemini returned an empty response"
                    )

            # Display response
            st.markdown(answer)

            # --------------------------------------------------
            # 11. Save conversation history
            # --------------------------------------------------

            st.session_state.messages.extend([
                {
                    "role": "user",
                    "content": prompt
                },
                {
                    "role": "assistant",
                    "content": answer
                }
            ])

        except Exception as error:
            st.error(f"API request failed: {error}")

import streamlit as st
from app.agent import WeatherAgent
import traceback

st.set_page_config(
    page_title="Local Enterprise Agent",
    page_icon="🦙",
    layout="centered"
)

st.title("🦙 Local Agentic AI (Ollama)")
st.caption("Privacy-First Weather Agent running on Localhost")

# ✅ INIT AGENT
if "agent" not in st.session_state:
    try:
        with st.spinner("Connecting to Ollama..."):
            st.session_state.agent = WeatherAgent()
        st.success("✅ Local Systems Online")
    except Exception:
        st.error("❌ Ollama not running. Start with: ollama serve")
        st.code(traceback.format_exc())
        st.stop()

# ✅ CHAT HISTORY
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display messages
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ✅ INPUT
if prompt := st.chat_input("Ask about weather..."):

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.agent.ask(prompt)
            except Exception:
                response = "❌ Unexpected error occurred."
                st.code(traceback.format_exc())

            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
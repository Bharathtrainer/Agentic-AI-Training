import streamlit as st
from app.agent import WeatherAgent
import traceback

# 1. Setup the Page
st.set_page_config(page_title="Enterprise Weather Agent", page_icon="☁️", layout="centered")
st.title("☁️ Enterprise Agentic AI")
st.caption("Powered by Gemini and FastMCP")

# 2. Safe Initialization with Error Reporting
if "agent" not in st.session_state:
    try:
        # Show a spinner so we know it's working, not frozen
        with st.spinner("Connecting to Google Gemini API... Please wait."):
            st.session_state.agent = WeatherAgent()
            st.success("Systems Online!")
    except Exception as e:
        st.error("🚨 Backend Initialization Failed")
        # This will show you exactly WHY it's failing (likely API Quota)
        st.expander("Technical Traceback").code(traceback.format_exc())
        st.stop() 

# 3. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Chat Input
if user_prompt := st.chat_input("Ask me about the weather..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent is reasoning..."):
            response = st.session_state.agent.ask(user_prompt)
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
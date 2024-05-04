import streamlit as st
from streamlit_extras.app_logo import add_logo

st.set_page_config(
    page_title="V&S AI Apps",
    layout='wide'
)

with st.sidebar:
    add_logo("img/v-und-s.png")

st.header("V&S AI Applications")
st.write("""
[![view source code ](https://img.shields.io/badge/GitHub%20Repository-gray?logo=github)](https://github.com/bennoloeffler/sample-python)
""")
st.write("""
Here you find the V&S AI Applications

- **Chat with ChatGPT**: Interactive conversations with the OpenAI LLM.
- **Chat with Ollama**: Interactive conversations with the lokal LLM.

""")

# Add credit
st.markdown("""
---
Made by [V&S](https://v-und-s.de/)""")

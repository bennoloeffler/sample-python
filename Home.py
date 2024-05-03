import streamlit as st

st.set_page_config(
    page_title="V&S AI Apps",
    layout='wide'
)

st.header("V&S AI Applications")
st.write("""
[![view source code ](https://img.shields.io/badge/GitHub%20Repository-gray?logo=github)](https://github.com/bennoloeffler/sample-python)
""")
st.write("""
Here you find the V&S AI Applications

- **Chat with the bot**: Engage in interactive conversations with the LLM.
- **Chat with the bot streaming**: Interactive streaming conversations with the LLM.

""")

# Add credit
st.markdown("""
---
Made by [V&S](https://v-und-s.de/)""")

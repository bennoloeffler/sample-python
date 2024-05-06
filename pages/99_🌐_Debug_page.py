import streamlit as st
from streamlit_extras.app_logo import add_logo

st.set_page_config(page_title="Debug page")
st.title("Debug page")
st.write(st.session_state)
with st.sidebar:
    add_logo("img/v-und-s.png")

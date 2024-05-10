import streamlit as st
from streamlit_extras.app_logo import add_logo

st.set_page_config(page_title="Debug page", layout="wide", page_icon='🌐')
with st.sidebar:
    add_logo("img/v-und-s.png")

st.title("Debug page")
st.subheader("Session Data")
st.write(st.session_state)
st.subheader("Config Data")

config = []
for c in st.config.get_config_options().values():
    config.append(f'{c.key}: "{c.value}" is default: {c.is_default})')
st.write(config)

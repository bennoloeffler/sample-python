import os
import streamlit as st
from streamlit_extras.app_logo import add_logo

st.set_page_config(page_title="Debug page", layout="wide", page_icon='🌐')
with st.sidebar:
    add_logo("img/v-und-s.png")

st.title("Debug page")
st.subheader("Session Data:")
ses = list(map(lambda i: {"key": i[0], "value": i[1]}, st.session_state.to_dict().items()))
st.dataframe(ses, use_container_width=True)

st.subheader("Environment:")
env = list(map(lambda i: {"key": i, "value": os.getenv(i)}, sorted(os.environ)))
st.dataframe(env, use_container_width=True)

st.subheader("Config Data:")
conf = list(map(lambda i: {
    "key": i.key,
    "value": i.value,
    "default": i.is_default},
    st.config.get_config_options().values()))
st.dataframe(conf, use_container_width=True)

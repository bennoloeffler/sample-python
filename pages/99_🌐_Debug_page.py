import os
import streamlit as st
from streamlit_extras.app_logo import add_logo

from password import check_password, is_admin


st.set_page_config(page_title="Debug page", layout="wide", page_icon='🌐')
with st.sidebar:
    add_logo("img/v-und-s.png")

st.title("Debug page")

if not check_password():
    st.stop()

if not is_admin():
    st.error("Access denied")
    st.stop()

st.subheader("Session Data:")
ses = list(map(lambda i: {"key": i[0], "value": i[1]}, st.session_state.to_dict().items()))
st.dataframe(ses, use_container_width=True)

st.subheader("Environment:")
env = list(map(lambda i: {"key": i, "value": os.getenv(i)},
               filter(lambda i: not i.endswith("_KEY") and not i.startswith("SECRET"),
                      sorted(os.environ))))
st.dataframe(env, use_container_width=True)

st.subheader("Config Data:")
conf = list(map(lambda i: {
    "key": i.key,
    "value": i.value,
    "default": i.is_default},
    st.config.get_config_options().values()))
st.dataframe(conf, use_container_width=True)

# Import required libraries
from dotenv import load_dotenv
from typing import Any

import streamlit as st
from password import check_password
from util import ChatBase

from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel

from streamlit_extras.app_logo import add_logo

# Load environment variables
load_dotenv()

# Set streamlit page configuration
st.set_page_config(page_title="V&S Ollama ChatBot", page_icon="💬")
st.title("V&S Ollama ChatBot")
with st.sidebar:
    add_logo("img/v-und-s.png")

class OllamaChatBot(ChatBase):

    MODEL_NAME = 'model_name'
    MODEL_NAME_INPUT = 'model_name_input'

    def __init__(self):
        print('Init OllamaChatBot')

        super().__init__("ollama")

        super().set_session_state_if_not_set(self.MODEL_NAME, "phi3")

        self.setup_llm()


    def get_model(self):
        return super().get_session_state(self.MODEL_NAME)


    def setup_llm(self):
        model = self.get_model()
        print(f'Setup Ollama Model: {model}')
        self.llm = ChatOllama(model=model)


    def model_changed(self):
        temp = self.get_session_state(self.MODEL_NAME_INPUT)
        self.set_session_state(self.MODEL_NAME, temp)
        self.llm.model = temp
        self.setup_llm()


    def get_model_names(self) -> list:
        return ["phi3", "llama3", "gemma", "llama2", "mistral"]


    def main(self):
        if not check_password():
            st.stop()

        # print(f'Ollama Model: {model}')
        models = self.get_model_names()
        idx = models.index(self.get_model())

        # print(f'Index: {idx}')
        with st.sidebar:
            st.selectbox("Model", options=models, index=idx,
                         key=self.get_session_key_name(self.MODEL_NAME_INPUT),
                         on_change=self.model_changed)
            if st.button("Clear chat"):
                self.clear_history()
                st.rerun()

            st.divider()
            st.markdown("Made by [V&S](https://v-und-s.de/)")

        self.print_chat()


if __name__ == "__main__":
    obj = OllamaChatBot()
    obj.main()

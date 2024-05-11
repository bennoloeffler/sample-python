# Import required libraries
from typing import Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI

import streamlit as st
from streamlit_extras.app_logo import add_logo

from password import check_password
from pageutil import ChatBase


# Load environment variables
load_dotenv()

# Set streamlit page configuration
st.set_page_config(page_title="V&S OpenAI ChatBot", page_icon="💬")
st.title("V&S OpenAI ChatBot")
with st.sidebar:
    add_logo("img/v-und-s.png")

class OpenAIChatBot(ChatBase):

    TEMPERATURE = 'temperature'
    MODEL_NAME = 'model_name'

    TEMPERATURE_INPUT = 'temperature_input'
    MODEL_NAME_INPUT = 'model_name_input'

    def __init__(self):
        print('Init OpenAIChatBot')

        super().__init__("openai")

        self.set_session_state_if_not_set(self.TEMPERATURE, 0.5)
        self.set_session_state_if_not_set(self.MODEL_NAME, "gpt-4-turbo")

        self.setup_llm()


    def get_temp(self):
        return super().get_session_state(self.TEMPERATURE)

    def get_model(self):
        return super().get_session_state(self.MODEL_NAME)

    def setup_llm(self):
        # Initialize the ChatOpenAI model
        temp = self.get_temp()
        model = self.get_model()
        print(f'Setup OpenAI Model: {model}, Temperature: {temp}')
        self.llm = ChatOpenAI(temperature=temp, model_name=model)


    def get_model_names(self) -> list[str]:
        return ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"]


    def temp_changed(self):
        temp = self.get_session_state(self.TEMPERATURE_INPUT)
        self.set_session_state(self.TEMPERATURE, temp)
        self.llm.temperature = temp
        self.setup_llm()


    def model_changed(self):
        temp = self.get_session_state(self.MODEL_NAME_INPUT)
        self.set_session_state(self.MODEL_NAME, temp)
        self.llm.model_name = temp
        self.setup_llm()


    def main(self):
        if not check_password():
            st.stop()

        with st.sidebar:
            # print(f'Model: {self.get_model()}, Temperature: {self.get_temp()}')
            st.slider("Temperatur", 0.0, 1.0, self.get_temp(),
                            key = self.get_session_key_name(self.TEMPERATURE_INPUT),
                            on_change = self.temp_changed)
            models = self.get_model_names()
            idx = models.index(self.get_model())

            # print(f'Index: {idx}')
            st.selectbox("Model", options = models, index = idx,
                                key = self.get_session_key_name(self.MODEL_NAME_INPUT),
                                on_change = self.model_changed)
            if st.button("Clear chat", use_container_width=True):
                self.clear_history()
                st.rerun()

            # Add credit
            st.divider()
            st.markdown("Made by [V&S](https://v-und-s.de/)")

        self.print_chat()


if __name__ == "__main__":
    obj = OpenAIChatBot()
    obj.main()

# Import required libraries
import os
import glob
from typing import Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent

import streamlit as st
from streamlit_extras.app_logo import add_logo

from password import check_password
from pageutil import ChatBase


# Load environment variables
load_dotenv()

# Set streamlit page configuration
st.set_page_config(page_title="V&S DB ChatBot", page_icon="💬")
st.title("V&S DB ChatBot")
with st.sidebar:
    add_logo("img/v-und-s.png")

class DBChatBot(ChatBase):

    TEMPERATURE = 'temperature'
    MODEL_NAME = 'model_name'
    DATABASE = 'database'

    def __init__(self):
        print('Init OpenAIChatBot')

        super().__init__("dbchat")

        self.set_session_state_if_not_set(self.TEMPERATURE, 0.5)
        self.set_session_state_if_not_set(self.MODEL_NAME, "gpt-4-turbo")

        self.setup_llm()


    def get_temp(self):
        return self.get_session_state(self.TEMPERATURE)

    def get_model(self):
        return self.get_session_state(self.MODEL_NAME)

    def get_db(self):
        return self.get_session_state(self.DATABASE)

    def get_all_dbs(self):
        dir = os.getenv("DATABASE_DIR")
        return glob.glob("*.db", root_dir=dir)

    def setup_llm(self):
        # Initialize the ChatOpenAI model
        temp = self.get_temp()
        model = self.get_model()
        dbname = self.get_db()
        if dbname:
            print(f'Setup OpenAI Model: {model}, Temperature: {temp}')
            self.llm = ChatOpenAI(temperature=temp, model_name=model)

            dir = os.getenv("DATABASE_DIR")
            file_name = f'sqlite:///{dir}/{dbname}'

            print(f'Database: {file_name}')
            self.db = SQLDatabase.from_uri(file_name)

            self.agent_executor = create_sql_agent(self.llm, db=self.db, agent_type="openai-tools", verbose=True)
        else:
            print('No DB selected!')


    def get_model_names(self) -> list[str]:
        return ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"]


    @st.spinner('Analyzing database..')
    def request_ai_response(self, messages) -> list[Any] | str:
        # Generate response using the chat model
        ai_response = self.agent_executor.invoke(messages)
        return ai_response['output']

        # # create temporary container to stream answer in
        # msg = st.empty()
        # with msg.container():
        #   ai_response = st.write_stream(stream)
        #   # clear the answer
        #   msg.empty()

        # return ai_response[len(ai_response)-1]['output']


    def main(self):
        if not check_password():
            st.stop()

        with st.sidebar:
            # print(f'Model: {self.get_model()}, Temperature: {self.get_temp()}')
            temp = st.slider("Temperatur", 0.0, 1.0, self.get_temp())
            if temp:
                self.set_session_state(self.TEMPERATURE, temp)
                self.setup_llm()

            models = self.get_model_names()
            idx = models.index(self.get_model())

            # print(f'Index: {idx}')
            model = st.selectbox("Model", options = models, index = idx)
            if model:
                self.set_session_state(self.MODEL_NAME, model)
                self.setup_llm()

            dbname = st.selectbox("Select Database:", options = self.get_all_dbs())
            if dbname:
                self.set_session_state(self.DATABASE, dbname)
                self.setup_llm()

            if st.button("Clear chat"):
                self.clear_history()
                st.rerun()

            # Add credit
            st.divider()
            st.markdown("Made by [V&S](https://v-und-s.de/)")

        self.print_chat()


if __name__ == "__main__":
    obj = DBChatBot()
    obj.main()

# Import required libraries
from dotenv import load_dotenv
from itertools import zip_longest

import streamlit as st
from streamlit_chat import message
from password import check_password

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder



# Load environment variables
load_dotenv()

# Set streamlit page configuration
st.set_page_config(page_title="V&S Streaming ChatBot")
st.title("V&S Streaming ChatBot")

class StreamChatbot:

    def __init__(self):
        self.setup_chat()

    def setup_chat(self):
        # Initialize the ChatOpenAI model
        self.llm = ChatOpenAI(
            temperature=0.5,
            model="gpt-3.5-turbo"
#            model="gpt-4-turbo"
        )

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a helpful AI assistant talking with a human. If you do not know an answer, just say 'I don't know', do not make up an answer.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                SystemMessage(content="Hello, I am a bot. How can I help you?")
            ]

    def get_response(self, user_query): #  -> Iterator[Output]

        return self.chain.stream({
            "chat_history": st.session_state.chat_history,
            "user_question": user_query,
        })


    def main(self):
        if not check_password():
            st.stop()

        # conversation
        for message in st.session_state.chat_history:
            if isinstance(message, AIMessage) or isinstance(message, SystemMessage):
                with st.chat_message("AI"):
                    st.write(message.content)
            elif isinstance(message, HumanMessage):
                with st.chat_message("Human"):
                    st.write(message.content)

        # Create a text input for user
        user_query = st.chat_input('Type your question here...')

        if user_query is not None and user_query != "":
            st.session_state.chat_history.append(HumanMessage(content=user_query))

            with st.chat_message("Human"):
                st.markdown(user_query)

            with st.chat_message("AI"):
                response = st.write_stream(self.get_response(user_query))

            st.session_state.chat_history.append(AIMessage(content=response))



        # Add credit
        st.markdown("""
        ---
        Made by [V&S](https://v-und-s.de/)""")


if __name__ == "__main__":
    obj = StreamChatbot()
    obj.main()

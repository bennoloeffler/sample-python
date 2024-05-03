# Import required libraries
from dotenv import load_dotenv
from itertools import zip_longest

import streamlit as st
from streamlit_chat import message
from password import check_password

from langchain_openai import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

# Load environment variables
load_dotenv()

# Set streamlit page configuration
st.set_page_config(page_title="V&S ChatBot")
st.title("V&S ChatBot")

class Chatbot:

    def __init__(self):
        self.setup_chat()

    def setup_chat(self):
        # Initialize session state variables
        if 'generated' not in st.session_state:
            st.session_state['generated'] = []  # Store AI generated responses

        if 'past' not in st.session_state:
            st.session_state['past'] = []  # Store past user inputs

        if 'entered_prompt' not in st.session_state:
            st.session_state['entered_prompt'] = ""  # Store the latest user input

        # Initialize the ChatOpenAI model
        self.chat = ChatOpenAI(
            temperature=0.5,
            model="gpt-4-turbo"
        )

    def build_message_list(self):
        """
        Build a list of messages including system, human and AI messages.
        """
        # Start zipped_messages with the SystemMessage
        zipped_messages = [SystemMessage(
            content="You are a helpful AI assistant talking with a human. If you do not know an answer, just say 'I don't know', do not make up an answer.")]

        # Zip together the past and generated messages
        for human_msg, ai_msg in zip_longest(st.session_state['past'], st.session_state['generated']):
            if human_msg is not None:
                zipped_messages.append(HumanMessage(
                    content=human_msg))  # Add user messages
            if ai_msg is not None:
                zipped_messages.append(
                    AIMessage(content=ai_msg))  # Add AI messages

        return zipped_messages


    def generate_response(self):
        """
        Generate AI response using the ChatOpenAI model.
        """
        # Build the list of messages
        zipped_messages = self.build_message_list()

        # Generate response using the chat model
        ai_response = self.chat.invoke(zipped_messages)

        return ai_response.content


    # Define function to submit user input
    def submit(self):
        # Set entered_prompt to the current value of prompt_input
        st.session_state.entered_prompt = st.session_state.prompt_input
        # Clear prompt_input
        st.session_state.prompt_input = ""


    def main(self):
        if not check_password():
            st.stop()

        # Create a text input for user
        st.text_input('YOU: ', key='prompt_input', on_change=self.submit)

        if st.session_state.entered_prompt != "":
            # Get user query
            user_query = st.session_state.entered_prompt
            st.session_state.entered_prompt = ""

            # Append user query to past queries
            st.session_state.past.append(user_query)

            # Generate response
            output = self.generate_response()

            # Append AI response to generated responses
            st.session_state.generated.append(output)

        # Display the chat history
        if st.session_state['generated']:
            for i in range(len(st.session_state['generated'])-1, -1, -1):
                # Display AI response
                message(st.session_state["generated"][i], key=str(i), avatar_style="icons")
                # Display user message
                message(st.session_state['past'][i],
                        is_user=True, key=str(i) + '_user', avatar_style="lorelei-neutral")


        # Add credit
        st.markdown("""
        ---
        Made by [V&S](https://v-und-s.de/)""")


if __name__ == "__main__":
    obj = Chatbot()
    obj.main()

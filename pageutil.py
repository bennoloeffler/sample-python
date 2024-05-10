from typing import Optional, Union, Any
import streamlit as st
from streamlit_chat import message, AvatarStyle
from itertools import zip_longest
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

import util

class Page:

    def __init__(self, prefix):
        self.prefix = prefix


    def get_session_key_name(self, key):
      return self.prefix + '.' + key


    def get_session_state(self, key, default = None):
        name = self.get_session_key_name(key)
        if name in st.session_state:
            return st.session_state[name]
        else:
            return default


    def has_session_state(self, key):
        return self.get_session_key_name(key) in st.session_state


    def del_session_state(self, key):
        name = self.get_session_key_name(key)
        if name in st.session_state:
            del st.session_state[name]


    def set_session_state_if_not_set(self, key, value):
        name = self.get_session_key_name(key)
        if name not in st.session_state:
            # print(f'Set {name} = {value}')
            st.session_state[name] = value
        else:
            old_value = st.session_state[name]
            # print(f'Variable {name} already set to {old_value} ignore new value {value}')


    def set_session_state(self, key, value):
      name = self.get_session_key_name(key)
    #   print(f'Set {name} = {value}')
      st.session_state[name] = value


class ChatBase(Page):

    GENERATED = 'generated'
    PAST = 'past'
    ENTERED_PROMPT = 'entered_prompt'
    SYSTEM_PROMPT = 'system_prompt'

    BOT_AVATAR = "icons"
    USER_AVATAR = "lorelei-neutral"
    DEFAULT_PROMPT = "You are a helpful AI assistant talking with a human. If you do not know an answer, just say 'I don't know', do not make up an answer."

    def __init__(self, prefix):
        super().__init__(prefix)

        # Initialize session state variables
        self.set_session_state_if_not_set(self.GENERATED, [])  # Store AI generated responses
        self.set_session_state_if_not_set(self.PAST, [])  # Store past user inputs
        self.set_session_state_if_not_set(self.ENTERED_PROMPT, "")  # Store the latest user input
        self.set_session_state_if_not_set(self.SYSTEM_PROMPT, self.DEFAULT_PROMPT)  # Store the default system prompt


    def setup_llm(self):
        pass


    def set_system_prompt(self, prompt):
        self.set_session_state(self.SYSTEM_PROMPT, prompt)


    # Build a list of messages including system, human and AI messages.
    def build_message_list(self) -> list:
        # Start zipped_messages with the SystemMessage
        zipped_messages = [SystemMessage(content=self.get_session_state(self.SYSTEM_PROMPT))]

        # Zip together the past and generated messages
        for human_msg, ai_msg in zip_longest(self.get_session_state(self.PAST), 
                                             self.get_session_state(self.GENERATED)):
            if human_msg is not None:
                zipped_messages.append(HumanMessage(
                    content=human_msg))  # Add user messages
            if ai_msg is not None:
                zipped_messages.append(
                    AIMessage(content=ai_msg))  # Add AI messages

        return zipped_messages


    def print_user_message(self, text, key):
        message(text, is_user=True, key=key + '_user', avatar_style=self.USER_AVATAR)


    def print_ai_message(self, text, key):
        message(text, key=key, avatar_style=self.BOT_AVATAR)


    # Display the chat history
    def print_chat_history(self):
        if self.get_session_state(self.GENERATED):
            for i in range(0, len(self.get_session_state(self.GENERATED)), 1):
                # Display user message
                key = str(i);
                self.print_user_message(self.get_session_state(self.PAST)[i], key)
                # Display AI response
                self.print_ai_message(self.get_session_state(self.GENERATED)[i], key)


    # Define function to submit_question user input
    def submit_question(self):
        # Set entered_prompt to the current value of prompt_input
        self.set_session_state(self.ENTERED_PROMPT, st.session_state.prompt_input)


    def request_ai_response(self, messages) -> list[Any] | str:
        # Generate response using the chat model
        stream = self.llm.stream(messages)

        # create temporary container to stream answer in
        msg = st.empty()
        with msg.container():
          ai_response = st.write_stream(stream)
          # clear the answer
          msg.empty()

        return ai_response


    # Generate AI response using the Chat model.
    def generate_response(self, user_query):
        # append the user question to history
        self.get_session_state(self.PAST).append(user_query)

        # write the question as user chat message
        key = str(len(self.get_session_state(self.PAST)))
        self.print_user_message(user_query, key)

        ai_response = self.request_ai_response(self.build_message_list())

        # append the answer to history
        self.get_session_state(self.GENERATED).append(ai_response)

        # write the answer as bot chat message
        self.print_ai_message(ai_response, key)


    def clear_history(self):
        self.set_session_state(self.GENERATED, [])
        self.set_session_state(self.PAST, [])
        self.set_session_state(self.ENTERED_PROMPT, "")


    def reset_prompt(self):
        self.set_session_state(self.SYSTEM_PROMPT, self.DEFAULT_PROMPT)


    def handle_entered_prompt(self, entered_prompt):
      self.generate_response(entered_prompt)


    def print_chat(self, placeholder: str = 'YOU: '):
        self.print_chat_history()

        # Create a text input for user
        st.chat_input(placeholder, key='prompt_input', on_submit=self.submit_question)

        user_input = self.get_session_state(self.ENTERED_PROMPT)
        if user_input != "":
            self.set_session_state(self.ENTERED_PROMPT, "")
            self.handle_entered_prompt(user_input)

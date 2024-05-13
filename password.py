# Import required libraries
import hmac
import os
import json
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()


def is_admin():
    groups = st.secrets["groups"]
    admins = groups["admins"]
    user = st.session_state["secrets.user"]
    return user in admins


def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        st.header("Login")#(try test@test)
        with st.form("Credentials"):
            user = os.getenv("USER.NAME", None)
            passwd = os.getenv("USER.PASS", None)
            st.text_input("Username", key="username", value=user)
            st.text_input("Password", type="password", key="password", value=passwd)
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""

        secret_user = os.getenv('SECRET.USER')
        secrets = json.loads(secret_user)
        user = st.session_state["username"]
        passwd = st.session_state["password"]
        passwds = st.secrets["passwords"]
        if (user in passwds and hmac.compare_digest(passwd, passwds[user])) or \
           (user in secrets and hmac.compare_digest(passwd, secrets[user])):
            st.session_state["password_correct"] = True
            st.balloons()
            st.session_state["secrets.user"] = user
            del st.session_state["password"]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    def logout():
        st.session_state["password_correct"] = False
        st.rerun()

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        if st.sidebar.button("Logout", use_container_width=True):
            del st.session_state["password_correct"]
            st.rerun()
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("User not known or password incorrect")
    return False

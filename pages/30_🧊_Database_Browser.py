import os
import glob
import sqlite3
import pandas as pd
import streamlit as st
from streamlit_extras.app_logo import add_logo
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv

from password import check_password
from pageutil import Page


load_dotenv()

st.set_page_config(page_title="Database browser", layout="wide", page_icon='🧊')
st.title("Database browser")
with st.sidebar:
    add_logo("img/v-und-s.png")

DBNAME = "dbname"
TABLENAME = "tablename"
STATEMENT = "statement"


@st.experimental_dialog("Confirm your selection")
def yes_no_dialog():
    if st.button("Yes"):
        return True
    elif st.button("No"):
        return False

class SQLBrowserPage(Page):

    def __init__(self):
        print('Init SQLBrowserPage')
        super().__init__("dbview")

    def main(self):
        if not check_password():
            st.stop()

        dir = os.getenv("DATABASE_DIR")
        dblist = glob.glob("*.db", root_dir=dir)
        dbname = st.sidebar.selectbox("Select Database:", options=dblist)
        if dbname:
            self.set_session_state(DBNAME, dbname)
        else:
            dbname = self.get_session_state(DBNAME)

        file_name = f'{dir}/{dbname}'

        if st.sidebar.button("Delete Database:", use_container_width=True):
            os.remove(file_name)
            st.rerun()

        if dbname:
            db = sqlite3.connect(file_name)
            cursor = db.cursor()
            result = cursor.execute("SELECT tbl_name FROM sqlite_master WHERE type='table'").fetchall()
            tables = list(map(lambda x: x[0], result))

            idx = tables.index(self.get_session_state(TABLENAME)) if self.has_session_state(TABLENAME) else 0
            table = st.selectbox("Select SQL table:", options=tables, index=idx)
            if table and table != self.get_session_state(TABLENAME):
                self.set_session_state(TABLENAME, table)
                stmt = f"SELECT * FROM {table}"
                self.set_session_state(STATEMENT, stmt)

            def_stmt = self.get_session_state(STATEMENT)

            stmt = st.text_input("SQL command:", 
                                 value=def_stmt,
                                 placeholder=def_stmt)

            if st.button("Execute statement"):
                self.set_session_state(STATEMENT, stmt)
                df = pd.read_sql_query(stmt, db)
                st.dataframe(df, use_container_width=True)
            

if __name__ == "__main__":
    obj = SQLBrowserPage()
    obj.main()


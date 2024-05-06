import sqlite3
import streamlit as st
from streamlit_extras.app_logo import add_logo
from langchain_community.utilities import SQLDatabase
import pandas as pd

from password import check_password
from util import Page


st.set_page_config(page_title="Database browser")
st.title("Database browser")
with st.sidebar:
    add_logo("img/v-und-s.png")

class SQLBrowserPage(Page):

    def __init__(self):
        print('Init SQLBrowserPage')

    def main(self):
        if not check_password():
            st.stop()

        if "DB" in st.session_state:
            db = sqlite3.connect(st.session_state["DB"][10:])
            cursor = db.cursor()
            result = cursor.execute("SELECT tbl_name FROM sqlite_master WHERE type='table'").fetchall()
            tables = list(map(lambda x: x[0], result))

            table = st.selectbox("Select SQL table:", options=tables)

            if table:
                sql = f'SELECT * FROM "{table}"'
                df = pd.read_sql_query(sql, db)
                st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    obj = SQLBrowserPage()
    obj.main()


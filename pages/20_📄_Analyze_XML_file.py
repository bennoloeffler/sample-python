import os
import sqlite3
import tempfile
from xml.etree import ElementTree
from typing import IO

import streamlit as st
from streamlit_extras.app_logo import add_logo
from streamlit_tree_select import tree_select
from streamlit.runtime.scriptrunner import add_script_run_ctx
from dotenv import load_dotenv

from password import check_password
from pageutil import Page
from xmlutil import XML2TreeSelect
from sqlutil import CreateSQL, InsertSQL, SQLGlobals
from util import save_temp_file


load_dotenv()


st.set_page_config(page_title="Analyze XML File", page_icon='📄')
st.title("Analyze XML File")
with st.sidebar:
    add_logo("img/v-und-s.png")


# @st.cache_data
@st.spinner('Analyzing XML structure..')
def analyze_xml_file_structure(uploaded_file: str,
                               ignore_ns:     bool) -> {dict, list}:
    msg = st.empty()
    with msg.container():
        st.write("Parsing...")

        tree = ElementTree.parse(uploaded_file)

        struct, checked = XML2TreeSelect.convert(tree.getroot(), ignore_ns)

        # clear the answer
        msg.empty()

        return struct, checked


@st.spinner('Insert into SQL Database..')
def insert_sql(db: SQLGlobals, file_uploaded):
    tree = ElementTree.parse(file_uploaded)
    root = tree.getroot()
    db.begin()
    InsertSQL.search_checked_nodes(root, "", db)
    db.end()


@st.spinner('Insert into SQL Database..')
def create_sql(db: SQLGlobals, statements: list):
    db.begin()
    for stmt in statements:
        try:
            db.run(stmt)
        except:
            print(f'Last SQL: {stmt}')
            raise
    db.end()


class AnalyzeXMLPage(Page):

    UPLOADED_XML = 'uploaded_xml'
    CHECKED_NODES = 'checked_nodes'
    STATEMENTS = 'statements'
    FILE_UPLOADED = 'file_uploaded'
    XML_ANALYZED = 'xml_analyzed'
    DB_CREATED = 'db_created'
    SQL_CREATED = 'sql_created'
    DB_INSERTED = 'db_inserted'
    IGNORE_NS = 'ignore_ns'
    FULL_NAME = 'full_name'
    DB_NAME = 'dbname'

    def __init__(self):
        print('Init AnalyzeXMLPage')

        super().__init__("analyzexml")


    def main(self):
        if not check_password():
            st.stop()

        st.divider()
        status_view = st.empty().container()
        st.divider()

        uploaded = st.sidebar.file_uploader("Choose a XML file", type='xml', accept_multiple_files=False)
        if uploaded:
            file_path = save_temp_file(uploaded)
            self.set_session_state(self.FILE_UPLOADED, file_path)
        file_uploaded = self.get_session_state(self.FILE_UPLOADED)

        ignore_ns = st.sidebar.checkbox("Ignore XML namespaces", self.get_session_state(self.IGNORE_NS))
        self.set_session_state(self.IGNORE_NS, ignore_ns)

        status_view.checkbox("File uploaded", value=(file_uploaded is not None), disabled=True)

        if st.sidebar.button("Analyze XML strructure", use_container_width=True, disabled=(file_uploaded is None)):
            struct, checked = analyze_xml_file_structure(file_uploaded, ignore_ns)
            self.set_session_state(self.XML_ANALYZED, True)
            self.set_session_state(self.UPLOADED_XML, struct)
            self.set_session_state(self.CHECKED_NODES, checked)

        xml_analyzed = self.get_session_state(self.XML_ANALYZED, False)
        status_view.checkbox("XML Structure analyzed", value=xml_analyzed, disabled=True)

        full_name = st.sidebar.checkbox("Use full path for table names", self.get_session_state(self.FULL_NAME))
        self.set_session_state(self.FULL_NAME, full_name)

        if xml_analyzed:
            st.header("XML File structure:")
            st.subheader("Repeated entries are preselected")
            struct = self.get_session_state(self.UPLOADED_XML)
            checked = self.get_session_state(self.CHECKED_NODES)
            tree = tree_select([struct], checked=checked, no_cascade=True, show_expand_all=True)
            checked = tree["checked"]
            self.set_session_state(self.CHECKED_NODES, checked)

        if st.sidebar.button("Reset All", use_container_width=True):
            self.del_session_state(self.XML_ANALYZED)
            self.del_session_state(self.UPLOADED_XML)
            self.del_session_state(self.CHECKED_NODES)
            self.del_session_state(self.STATEMENTS)
            self.del_session_state(self.DB_CREATED)
            self.del_session_state(self.DB_INSERTED)
            self.del_session_state(self.SQL_CREATED)
            st.rerun()

        if st.sidebar.button("Generate SQL create statements", use_container_width=True, disabled=not xml_analyzed):
            statements = []
            CreateSQL.search_checked_nodes(struct, checked, statements, full_name)
            self.set_session_state(self.STATEMENTS, statements)

        statements = self.get_session_state(self.STATEMENTS)
        status_view.checkbox("DB structure generated", value=(statements is not None), disabled=True)

        if statements:
            st.subheader("SQL structure:")
            st.write(statements)

        dbname = st.sidebar.text_input("Database name:", self.get_session_state(self.DB_NAME, "database"))
        self.set_session_state(self.DB_NAME, dbname)

        if st.sidebar.button("Create SQL Database", use_container_width=True, disabled=(statements is None)):
            # dir = tempfile.TemporaryDirectory().name
            dir = os.getenv("DATABASE_DIR")
            os.makedirs(dir, exist_ok=True)
            url = f"sqlite:///{dir}/{dbname}.db"
            print(f'Database file: {url}')

            db = SQLGlobals(url, checked, ignore_ns, full_name)

            create_sql(db, statements)
            status_view.checkbox("DB structure created", value=True, disabled=True)

            insert_sql(db, file_uploaded)
            status_view.checkbox("DB data inserted", value=True, disabled=True)

            self.set_session_state(self.DB_CREATED, url)
            self.set_session_state(self.DB_INSERTED, True)

        else:
            status_view.checkbox("DB structure created", disabled=True,
                                 value=(self.get_session_state(self.DB_CREATED) is not None))
            status_view.checkbox("DB data inserted", disabled=True,
                                 value=(self.get_session_state(self.DB_INSERTED) is not None))

        if statements and st.sidebar.button("Create SQL file", use_container_width=True):
            dir = os.getenv("FILE_DIR")
            os.makedirs(dir, exist_ok=True)
            url = f"file:///{dir}/{dbname}.sql"
            print(f'Temporary file: {url}')

            db = SQLGlobals(url, checked, ignore_ns, full_name)
            create_sql(db, statements)
            status_view.checkbox("DB structure written", value=True, disabled=True)

            insert_sql(db, file_uploaded)
            status_view.checkbox("DB data written", value=True, disabled=True)

            self.set_session_state(self.SQL_CREATED, url)

        sql_file = self.get_session_state(self.SQL_CREATED)
        if sql_file:
            with open(sql_file[8:]) as f:
                st.sidebar.download_button('Download SQL file',
                                            data=f, 
                                            file_name=f"{dbname}.sql",
                                            mime='text/sql',
                                            use_container_width=True)


if __name__ == "__main__":
    obj = AnalyzeXMLPage()
    obj.main()

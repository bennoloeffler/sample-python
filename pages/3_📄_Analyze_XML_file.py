import os
import xml.etree.ElementTree as ET
import sqlite3
import tempfile
from typing import IO

import streamlit as st
from streamlit_extras.app_logo import add_logo
from streamlit_tree_select import tree_select
from streamlit.runtime.scriptrunner import add_script_run_ctx
from password import check_password
from langchain_community.utilities import SQLDatabase

from util import Page


CHILDREN = 'children'
LABEL = 'label'
COUNT = 'count'
VALUE = 'value'
LIST = 'list'

def save_file(file):
    folder = 'tmp'
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    file_path = f'./{folder}/{file.name}'
    with open(file_path, 'wb') as f:
        f.write(file.getvalue())

    return file_path


def add_child(target: dict, name:str, value:str):
    if CHILDREN not in target:
        target[CHILDREN] = []

    for child in target[CHILDREN]:
        if child[LABEL] == name:
            child[COUNT] += 1
            return child

    child = {LABEL: name, VALUE: value, COUNT: 1, LIST:False}
    target[CHILDREN].append(child)
    return child


def recursive_analyse_xml(root: ET, path: str, target: dict):

    subpaths = []
    for attrib in root.keys():
        subpath = path + '/' + attrib
        child = add_child(target, attrib, subpath)
        if subpath in subpaths:
            child[LIST] = True
        else:
            subpaths.append(subpath)

    for node in root:
        subpath = path + '/' + node.tag
        child = add_child(target, node.tag, subpath)
        if subpath in subpaths:
            child[LIST] = True
        else:
            subpaths.append(subpath)

        recursive_analyse_xml(node, subpath, child)


def recursive_add_count(node, checked):#, parent
    count = node[COUNT]
    # if count > parent[COUNT]:
    #     checked.append(node[VALUE])

    node[LABEL] += ':'
    if node[LIST]:
        node[LABEL] += f' []'
        checked.append(node[VALUE])

    node[LABEL] += f' ({count})'

    if CHILDREN in node:
        for child in node[CHILDREN]:
            recursive_add_count(child, checked)#, node


@st.cache_data
@st.spinner('Analyzing XML structure..')
def analyze_xml_file_structure(uploaded_file):
    msg = st.empty()
    with msg.container():
        st.write("Parsing...")

        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        struct = {LABEL: root.tag, VALUE: root.tag, COUNT : 1, LIST:False}
        recursive_analyse_xml(root, root.tag, struct)
        checked = []
        recursive_add_count(struct, checked)#, struct

        # clear the answer
        msg.empty()

        return struct, checked


def add_sql_fields(node, sql: str, checked, statements, foreign_key):
    nothing_added = True
    if CHILDREN in node:
        for child in node[CHILDREN]:
            value = child[VALUE]
            if value in checked:
                build_sql_create_statement(child, checked, statements, foreign_key)
            else:
                field = child[LABEL].split(':')[0]
                sql += ',\n\t"' + field + '" TEXT'
                sql, nothing_added = add_sql_fields(child, sql, checked, statements, foreign_key)
                nothing_added = False
    return sql, nothing_added


def build_sql_create_statement(node, checked, statements, foreign_key: str = None):
    tablename = node[LABEL].split(':')[0]

    statements.append(f'DROP TABLE IF EXISTS "{tablename}";')

    index = len(statements)

    sql = f'CREATE TABLE "{tablename}" ('
    sql += '\n\t"' + tablename + '_ID" INTEGER PRIMARY KEY' # AUTOINCREMENT

    my_foreign_key = f'\t"{tablename}_ID" INTEGER,\n\tFOREIGN KEY ("{tablename}_ID") REFERENCES "{tablename}"("{tablename}_ID")'

    sql, nothing_added = add_sql_fields(node, sql, checked, statements, my_foreign_key)
    if nothing_added:
        sql += ',\n\t"VALUE" TEXT'
    if foreign_key:
        sql += ',\n' + foreign_key

    sql += "\n);\n"
    statements.insert(index, sql)


def search_checked_nodes(node, checked, statements):
    if CHILDREN in node:
        for child in node[CHILDREN]:
            value = child[VALUE]
            if value in checked:
                build_sql_create_statement(child, checked, statements)
            else:
                search_checked_nodes(child, checked, statements)


class SQLStmt:
    columns: list;
    values: list;

    def __init__(self):
        self.columns = []
        self.values = []


class SQLRef:
    statements: list
    ref: str
    ref_id: int

    def __init__(self, ref: str, ref_id: int):
        self.statements = []
        self.ref = ref
        self.ref_id = ref_id


class SQLGlobals:
    db: object
    checked: list
    ids: dict

    def __init__(self, db, checked: list, ids: dict = dict()):
        if db and db.startswith('file:///'):
            self.db = open(db[8:], "w")
        elif db.startswith('sqlite:///'):
            self.db = sqlite3.connect(db[10:])
        else:
            self.db = SQLDatabase.from_uri(db)
            print("DB dialect: " + self.db.dialect)

        print('Use Database: ' + str(type(self.db)))

        self.checked = checked
        self.ids = ids

    def run(self, stmt):
        if isinstance(self.db, sqlite3.Connection):
            try:
                self.db.execute(stmt)
            except:
                print(f'Last SQL: {stmt}')
                raise
        elif isinstance(self.db, SQLDatabase):
            try:
                self.db.run(stmt)
            except:
                print(f'Last SQL: {stmt}')
                raise
        else:
            # print(stmt)
            self.db.write(stmt)
            self.db.write('\n')

    def begin(self):
        if isinstance(self.db, sqlite3.Connection):
            try:
                self.db.execute('PRAGMA synchronous = OFF;')
                self.db.execute('BEGIN TRANSACTION;')
            except:
                print(f'Last SQL: BEGIN TRANSACTION')
                raise
        elif isinstance(self.db, SQLDatabase):
            pass
        else:
            self.db.write('BEGIN TRANSACTION;\n')

    def end(self):
        if isinstance(self.db, sqlite3.Connection):
            try:
                self.db.execute('END TRANSACTION;')
            except:
                print(f'Last SQL: END TRANSACTION')
                raise
        elif isinstance(self.db, SQLDatabase):
            pass
            # try:
            #     self.db.run('END TRANSACTION;')
            # except:
            #     print(f'Last SQL: commit')
            #     raise
        else:
            self.db.write('END TRANSACTION;\n')
            self.db.flush()



def recursive_add_fields_sql_from_xml(stmt: SQLStmt,
                                      node: ET,
                                      path: str,
                                      db: SQLGlobals,
                                      ref: SQLRef):
    for attrib, value in node.items():
        if value:
            stmt.columns.append(f'{attrib}')
            stmt.values.append(value)

    for child in node:
        subpath = path + '/' + child.tag
        if subpath in db.checked:
            recursive_insert_sql_from_xml(child, subpath, db, ref)
        else:
            if child.text:
                stmt.columns.append(child.tag)
                stmt.values.append(child.text.strip().replace("'", '"'))
            recursive_add_fields_sql_from_xml(stmt, child, subpath, db, ref)


def recursive_insert_sql_from_xml(node: ET,
                                  path: str,
                                  db: SQLGlobals,
                                  parent_ref: SQLRef = None):

    # print(f'Check {path}')
    if path in db.checked:

        ref_name = f"'{node.tag}_ID'"
        ref_id = db.ids.get(ref_name, 0) + 1
        db.ids[ref_name] = ref_id

        ref = SQLRef(ref_name, ref_id)
        stmt = SQLStmt()

        recursive_add_fields_sql_from_xml(stmt, node, path, db, ref)

        sql = f"INSERT INTO '{node.tag}' ({ref_name}"

        if parent_ref:
            sql += ',' + parent_ref.ref

        for col in stmt.columns:
            sql += f",'{col}'"

        if len(stmt.columns) < 1 and node.text:
            sql += ",'VALUE'"

        sql += f") VALUES ({ref_id}"

        if parent_ref:
            sql += f',{parent_ref.ref_id}'

        for val in stmt.values:
            sql += f",'{val}'"

        if len(stmt.values) < 1 and node.text:
            sql += f",'{node.text}'"

        sql += ');'
        
        # We must insert the main table before the tables that reference to it
        if parent_ref:
            parent_ref.statements.append(sql)
            parent_ref.statements.extend(ref.statements)

        else:
            db.run(sql)
            for stmt in ref.statements:
                db.run(stmt)

    else:
        for child in node:
            subpath = path + '/' + child.tag
            recursive_insert_sql_from_xml(child, subpath, db, parent_ref)


st.set_page_config(page_title="Analyze XML File")
st.title("Analyze XML File")
with st.sidebar:
    add_logo("img/v-und-s.png")

class AnalyzeXMLPage(Page):

    UPLOADED_XML = 'uploaded_xml'
    CHECKED_NODES = 'checked_nodes'
    STATEMENTS = 'statements'
    FILE_UPLOADED = 'file_uploaded'
    XML_ANALYZED = 'xml_analyzed'
    DB_CREATED = 'db_created'
    SQL_CREATED = 'sql_created'
    DB_INSERTED = 'db_inserted'

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
            file_path = save_file(uploaded)
            self.set_session_state(self.FILE_UPLOADED, file_path)

        file_uploaded = self.get_session_state(self.FILE_UPLOADED)
        status_view.checkbox("File uploaded", value=(file_uploaded is not None), disabled=True)

        if file_uploaded and st.sidebar.button("Analyze XML strructure", use_container_width=True):
            struct, checked = analyze_xml_file_structure(file_uploaded)
            self.set_session_state(self.XML_ANALYZED, True)
            self.set_session_state(self.UPLOADED_XML, struct)
            self.set_session_state(self.CHECKED_NODES, checked)

        xml_analyzed = self.get_session_state(self.XML_ANALYZED)
        status_view.checkbox("XML Structure analyzed", value=xml_analyzed, disabled=True)

        if xml_analyzed:
            st.header("XML File structure:")
            st.subheader("Repeated entries are preselected")
            struct = self.get_session_state(self.UPLOADED_XML)
            checked = self.get_session_state(self.CHECKED_NODES)
            tree = tree_select([struct], checked=checked, no_cascade=True, show_expand_all=True)
            checked = tree["checked"]
            self.set_session_state(self.CHECKED_NODES, checked)

            if st.sidebar.button("Generate SQL create statements", use_container_width=True):
                statements = []
                search_checked_nodes(struct, checked, statements)
                self.set_session_state(self.STATEMENTS, statements)

        statements = self.get_session_state(self.STATEMENTS)
        status_view.checkbox("DB structure generated", value=(statements is not None), disabled=True)

        if statements:
            st.subheader("SQL structure:")
            st.write(statements)
            to_file = st.sidebar.checkbox("Write to file")

        if statements and st.sidebar.button("Create SQL Database", use_container_width=True):
            dir = tempfile.TemporaryDirectory().name
            os.makedirs(dir)
            url = (f"file:///{dir}/import.sql" if to_file else f"sqlite:///{dir}/import.db")
            print(f'Temporary file: {url}')

            db = SQLGlobals(url, checked)
            db.begin()
            for stmt in statements:
                try:
                    db.run(stmt)
                except:
                    print(f'Last SQL: {stmt}')
                    raise

            db.end()

            if not to_file:
                st.session_state["DB"] = url
                self.set_session_state(self.DB_CREATED, url)
                status_view.checkbox("DB structure created", value=True, disabled=True)

            tree = ET.parse(file_uploaded)
            root = tree.getroot()
            db.begin()
            recursive_insert_sql_from_xml(root, root.tag, db)
            db.end()
            if not to_file:
                self.set_session_state(self.DB_INSERTED, True)
                status_view.checkbox("DB data inserted", value=True, disabled=True)
            else:
                self.set_session_state(self.SQL_CREATED, url)

            sql_file = self.get_session_state(self.SQL_CREATED)

            if sql_file:
                with open(sql_file[8:]) as f:
                    st.sidebar.download_button('Download SQL file',
                                                data=f, 
                                                file_name="statements.sql",
                                                mime='text/sql',
                                                use_container_width=True)

        else:
            status_view.checkbox("DB structure created", disabled=True,
                                 value=(self.get_session_state(self.DB_CREATED) is not None))
            status_view.checkbox("DB data inserted", disabled=True,
                                 value=(self.get_session_state(self.DB_INSERTED) is not None))

if __name__ == "__main__":
    obj = AnalyzeXMLPage()
    obj.main()

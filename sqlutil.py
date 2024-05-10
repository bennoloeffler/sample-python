import os
import sqlite3
import tempfile
from xml.etree import ElementTree
from langchain_community.utilities import SQLDatabase

from util import (
  get_node_name, get_tag_name, prefix_field_name,
  VALUE, CHILDREN, LABEL
)


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
    ignore_ns: bool
    full_name: bool

    def __init__(self,
                 db:        object,
                 checked:   list,
                 ignore_ns: bool,
                 full_name: bool,
                 ids:       dict = dict()):
        if db and db.startswith('file:///'):
            self.db = open(db[8:], "w")
        elif db.startswith('sqlite:///'):
            self.db = sqlite3.connect(db[10:])
        else:
            self.db = SQLDatabase.from_uri(db)
            print("DB dialect: " + self.db.dialect)

        print('Use Database: ' + str(type(self.db)))

        self.checked = checked
        self.ignore_ns = ignore_ns
        self.full_name = full_name
        self.ids = ids

    def run(self,
            stmt: str):
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


class CreateSQL:

    @staticmethod
    def get_clean_name(node: dict) -> str:
        return node[LABEL].split(': ')[0]


    @staticmethod
    def get_table_name(node:      dict,
                       full_name: bool) -> {str, str}:
        tablename_id = CreateSQL.get_clean_name(node)
        tablename = node[VALUE] if full_name else tablename_id
        return tablename, tablename_id


    @staticmethod
    def create_sql_fields(node:        dict,
                          columns:     list,
                          checked:     list,
                          statements:  list,
                          prefix:      str,
                          full_name:   bool,
                          foreign_key: str):
        if CHILDREN in node:
            for child in node[CHILDREN]:
                field = prefix_field_name(CreateSQL.get_clean_name(child), prefix)
                columns.append(field)

                if child[VALUE] in checked:
                    CreateSQL.create_sql_table(child, checked, statements, full_name, foreign_key)
                else:
                    CreateSQL.create_sql_fields(child, columns, checked, statements, field + '.',
                                                full_name, foreign_key)


    @staticmethod
    def create_sql_table(node:        dict,
                         checked:     list,
                         statements:  list,
                         full_name:   bool,
                         foreign_key: str = None):
        tablename, tablename_id = CreateSQL.get_table_name(node, full_name)

        statements.append(f'DROP TABLE IF EXISTS "{tablename}";')

        index = len(statements)

        sql = f'CREATE TABLE "{tablename}" ('
        sql += '\n\t"' + tablename_id + '_ID" INTEGER PRIMARY KEY' # AUTOINCREMENT

        my_foreign_key = f'\t"REFERENCE_ID" INTEGER,\n\tFOREIGN KEY ("REFERENCE_ID") REFERENCES "{tablename}"("{tablename_id}_ID")'

        columns = []
        CreateSQL.create_sql_fields(node, columns, checked, statements, "", full_name,
                                    my_foreign_key)

        if len(columns) > 0:
            for col in columns:
                sql += f',\n\t"{col}" TEXT'
        else:
            sql += ',\n\t"VALUE" TEXT'

        if foreign_key:
            sql += ',\n' + foreign_key

        sql += "\n);\n"
        statements.insert(index, sql)


    @staticmethod
    def search_checked_nodes(node:       dict,
                             checked:    list,
                             statements: list,
                             full_name:  bool):
        value = node[VALUE]
        if value in checked:
            CreateSQL.create_sql_table(node, checked, statements, full_name)
        elif CHILDREN in node:
            for child in node[CHILDREN]:
                CreateSQL.search_checked_nodes(child, checked, statements, full_name)


class InsertSQL:

    @staticmethod
    def insert_sql_fields(node:        ElementTree,
                          parent_path: str,
                          prefix:      str,
                          db:          SQLGlobals,
                          stmt:        SQLStmt,
                          ref:         SQLRef):
        for attrib, text in node.items():
            value = None if text is None else text.strip()
            if value:
                name, subpath = get_tag_name(attrib, parent_path, db.ignore_ns)
                field = prefix_field_name(name, prefix)
                stmt.columns.append(field)
                stmt.values.append(value)

        for child in node:
            name, subpath = get_node_name(child, parent_path, db.ignore_ns)
            field = prefix_field_name(name, prefix)
            value = None if child.text is None else child.text.strip()
            if value:
                if len(value) > 0:
                    stmt.columns.append(field)
                    stmt.values.append(value)

            if subpath in db.checked:
                InsertSQL.insert_sql_table(child, name, subpath, db, ref)
            else:
                InsertSQL.insert_sql_fields(child, subpath, field + '.', db, stmt, ref)


    @staticmethod
    def insert_sql_table(node:        ElementTree,
                         tablename:   str,
                         tablepath:   str,
                         db:          SQLGlobals,
                         parent_ref:  SQLRef = None):

        # print(f'Check {parent_path}')
        tablename_id = tablename
        if db.full_name:
            tablename = tablepath

        ref_name = f'"{tablename_id}_ID"'
        ref_id = db.ids.get(ref_name, 0) + 1
        db.ids[ref_name] = ref_id

        ref = SQLRef(ref_name, ref_id)
        stmt = SQLStmt()

        InsertSQL.insert_sql_fields(node, tablepath, "", db, stmt, ref)

        sql = f'INSERT INTO "{tablename}" ({ref_name}'

        if parent_ref:
            sql += ',REFERENCE_ID'# + parent_ref.ref

        for col in stmt.columns:
            sql += f',"{col}"'

        value = None if node.text is None else node.text.strip()

        if len(stmt.columns) < 1 and value:
            sql += ',"VALUE"'

        sql += f') VALUES ({ref_id}'

        if parent_ref:
            sql += f',{parent_ref.ref_id}'

        for v in stmt.values:
            val = v.replace('"', '&quot;')
            sql += f',"{val}"'

        if len(stmt.values) < 1 and value:
            v = value.replace('"', '&quot;')
            sql += f',"{v}"'

        sql += ');'
        
        # We must insert the main table before the tables that reference to it
        if parent_ref:
            parent_ref.statements.append(sql)
            parent_ref.statements.extend(ref.statements)

        else:
            db.run(sql)
            for stmt in ref.statements:
                db.run(stmt)

    @staticmethod
    def search_checked_nodes(node:        ElementTree,
                             parent_path: str,
                             db:          SQLGlobals,
                             parent_ref:  SQLRef = None):
        name, subpath = get_node_name(node, parent_path, db.ignore_ns)
        if subpath in db.checked:
            InsertSQL.insert_sql_table(node, name, subpath, db, parent_ref)
        else:
            for child in node:
                InsertSQL.search_checked_nodes(child, subpath, db, parent_ref)

import sublime
import sublime_plugin
import sys
import os
import base64

print("connect", sys.path)
directory = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.join(directory, "lib")
sys.path.append(lib_path)
print("connect2", sys.path)
import pyodbc
import decimal
from datetime import datetime, timedelta, date


def crypt(string, encoding="ascii", encode=True):
    string_encode = string.encode(encoding)
    if encode:
        base64_bytes = base64.b64encode(string_encode)
        print("Encoding...")
    else:
        base64_bytes = base64.b64decode(string_encode)
    return base64_bytes.decode(encoding)


def get_uid_pw():
    user = os.getenv("TERADATAUSERNAMEENCODED")
    assert user is not None, "Teradata uid and pw not set, run setup_local in cmd"
    pw = os.getenv("TERADATAPWENCODED")
    return crypt(user, encode=False), crypt(pw, encode=False)


class teradata_connect:
    def __init__(self):
        user, pw = get_uid_pw()
        self.conn = pyodbc.connect(
            Driver="{Teradata Database ODBC Driver 17.10}",
            DBCName="tdprod",
            uid=user,
            pwd=pw,
            autocommit=True,
        )
        self.cursor = self.conn.cursor()

    def execute(self, query):
        self.cursor.execute(query)

    def close(self):
        if not self.conn.closed:
            self.conn.close()

    def get_tbl_meta_cols_only(self, tbl):
        db, tblname = tbl.split(".")

        query = f"""
        SELECT columnname as col  from dbc.columns 
        where DatabaseName = '{db}' and TableName = '{tblname}'

        """
        try:
            self.cursor.execute(query)
        except pyodbc.ProgrammingError:
            return None

        cols = self.cursor.fetchall()
        if len(cols) == 0:
            print(f"no such table {tbl}")
            return None
        cols = [col[0].replace(" ", "") for col in cols]
        return cols

    def get_all_accessible_meta(self):
        query = """
        WITH temp AS (

        SELECT DISTINCT B.DATABASENAME

        FROM DBC.ROLEMEMBERS A
        JOIN DBC.ALLROLERIGHTS B ON A.ROLENAME=B.ROLENAME
        JOIN DBC.USERS C ON C.USERNAME=A.GRANTEE 
        where b.accessright = 'R'
        ),
        accessible_table as (
        SELECT * FROM dbc.tables as a 
        where a.DatabaseName in (select * from temp )
        )
        SELECT a.DatabaseName,a.TableName,a.ColumnName FROM dbc.columns as a 
        where (a.DatabaseName, a.TableName) in (SELECT databasename, TableName from accessible_table) 
        """
        # -- and a.DatabaseName <>'workdb'
        self.cursor.execute(query)

    def parse_all_accessible_meta(self):
        lst = self.cursor.fetchall()
        final = {}
        all_lst = set()
        for row in lst:
            db, tbl, col = row
            db = db.replace(" ", "").lower()
            tbl = tbl.replace(" ", "").lower()
            col = col.replace(" ", "")
            all_lst.add(f"{db}.{tbl}.{col}")

            if db not in final:
                final[db] = {tbl: [col]}
            else:
                if tbl in final[db]:
                    final[db][tbl].append(col)
                else:
                    final[db].update({tbl: [col]})
        print(len(all_lst), "unique columns in autocomplete")
        return {"completions": final}, list(all_lst)

    def get_tbl_meta(self, tbl, cols_only=False, simplify=False):
        if simplify:
            mapping = {
                int: "i",
                decimal.Decimal: "f",
                datetime: "t",
                date: "d",
                str: "s",
                bool: "b",
                float: "f",
            }
        else:
            mapping = {
                int: "int",
                decimal.Decimal: "float",
                datetime: "timestamp",
                date: "date",
                str: "string",
                bool: "boolean",
                float: "float",
            }

        query = f"""
        select top 3 * from {tbl}
        """
        try:
            self.cursor.execute(query)
        except pyodbc.ProgrammingError:
            return None
        meta = {}
        for x in self.cursor.description:
            col = x[0]
            dtype = x[1]
            dtype = mapping.get(dtype)
            if dtype is None:
                dtype = "None"
            meta[col] = dtype
        if cols_only:
            return list(meta)
        return meta

    def query_to_cur_transpose_compare(self, query):
        self.execute(query)
        lst = self.cursor.fetchall()
        cols = [ele[0] for ele in self.cursor.description]
        return [ele for ele in zip(cols, *lst) if len(set(ele[1:])) != 1]

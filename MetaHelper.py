import sublime
import sublime_plugin
import sys
import os
import base64
import time
import json
import threading
import ctypes
import csv

# need to dynamic later
package_path = sublime.packages_path()
lib_path = f"{package_path}\\Sublime_Teradata_Plugin\\lib"
plugin_path = f"{package_path}\\Sublime_Teradata_Plugin"
metastore_path = f"{plugin_path}\\metastore"
connection_group_list_path = f"{metastore_path}\\EDW_SQL.connection-group-list"


if lib_path not in sys.path:
    sys.path.append(lib_path)
if plugin_path not in sys.path:
    sys.path.append(plugin_path)

from connect import teradata_connect, crypt

# comment out since run_sql will create a global conn
# from run_sql import stop_thread


def stop_thread(t1):
    if isinstance(t1, int):
        thread_id = t1
    else:
        thread_id = t1.native_id
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        thread_id, ctypes.py_object(SystemExit)
    )
    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        print("Exception raise failure")
    print(f"Successfull stop thread {thread_id}")


def credential_set(show_msg=True):
    if (
        os.getenv("TERADATAUSERNAMEENCODED") is not None
        and os.getenv("TERADATAPWENCODED") is not None
    ):
        if show_msg:
            sublime.message_dialog("Teradata username and password has set up!")
        return True
    else:
        return False


# def open_auto_complete_file


class MetaPassword(sublime_plugin.WindowCommand):
    def run(self):
        self.counter = 0
        self.prompts = ["Enter Teradata Username", "Enter Teradata Password"]

        self.show_prompt()

    def show_prompt(self):
        # user
        if self.counter == 0:
            panel = self.window.show_input_panel(
                self.prompts[self.counter], "", self.on_done, None, None
            )
        else:
            panel = self.window.show_input_panel(
                self.prompts[self.counter], "", self.on_done, None, None
            )
            panel.settings().set("password", True)

    def on_done(self, user_input):
        self.counter += 1
        user_input = crypt(user_input)
        # user
        if self.counter < len(self.prompts):
            os.system(
                f"""powershell -command "[System.Environment]::SetEnvironmentVariable('TeradataUserNameEncoded','{user_input}',[System.EnvironmentVariableTarget]::User)"
    """
            )
            # sublime.message_dialog("username entered: '%s'" % user_input)
            self.show_prompt()
        # password
        else:
            os.system(
                f"""powershell -command "[System.Environment]::SetEnvironmentVariable('TeradataPWEncoded','{user_input}',[System.EnvironmentVariableTarget]::User)"
    """
            )
            sublime.message_dialog(
                "Teradata Username and Password has set\nPlease close and reopen sublime to enable system variable"
            )


class MetaInit(sublime_plugin.WindowCommand):
    def run(self):
        def main_func(self):
            try:
                panel = self.window.create_output_panel("meta_init")
                panel.set_read_only(False)
                panel.settings().set("word_wrap", False)

                alias = {"alias": {}, "allowed_alias_num": 20}

                dot_sublime_completions = {
                    "scope": "source.sql",
                    "completions": [
                        "SELECT",
                        "UPDATE $0\nSET  =  \nWhere  =  ;",
                        "DELETE",
                        "INSERT INTO $0 VALUES();",
                        "FROM",
                        "WHERE",
                        "GROUP BY",
                        "ORDER BY",
                        "HAVING",
                        "INNER JOIN",
                        "LEFT JOIN",
                        "RIGHT JOIN",
                        "LIMIT",
                        "DISTINCT",
                        "MAX",
                        "MIN",
                        "WITH",
                        "SAMPLE",
                        "WITH cte AS (\n$0\n);",
                        "WITH cte AS (\nSELECT DISTINCT $0 FROM \n)\nSELECT COUNT(*) FROM CTE;",
                        "COUNT",
                        "Count(*)",
                        "Count(DISTINCT $0)",
                        "CREATE MULTISET VOLATILE TABLE #temp_tbl AS (\n$0\n)\nWITH DATA PRIMARY INDEX( ) ON COMMIT PRESERVE ROWS;",
                        "CREATE MULTISET TABLE AS (\n$0\n)\nWITH DATA PRIMARY INDEX( );",
                        "CASE WHEN  $0 THEN  ELSE  END",
                        "CAST($0 as date)",
                        "PARTITION BY",
                        "EXTRACT(YEAR FROM $0)",
                        "EXTRACT(MONTH FROM $0)",
                        "DROP TABLE $0;",
                        "PIVOT \n(\n$0 \nFOR IN (\n 'VAL1' AS VAL1 \n) \n) TMP",
                        "OVER (PARTITION BY $0)",
                    ],
                }

                with open(
                    metastore_path + "\\EDW_SQLAlias.custom-completions", "w"
                ) as f:
                    file = json.dumps(alias)
                    f.write(file)

                with open(plugin_path + "\\EDW_SQL.sublime-completions", "w") as f:
                    file = json.dumps(dot_sublime_completions)
                    f.write(file)
                with open(connection_group_list_path, "w") as f:
                    f.write("")

                deleted = []
                for file in os.listdir(metastore_path):
                    if file in ("all.connection-group", "all.drop-down"):
                        deleted.append(file)
                        os.remove(metastore_path + f"\\{file}")
                if len(deleted) > 0:
                    panel.run_command(
                        "append",
                        {"characters": f"\nDeleted Files: {' , '.join(deleted)}\n"},
                    )
                conn = teradata_connect()
                conn.get_all_accessible_meta()
                print("Done")
                panel.run_command(
                    "append",
                    {
                        "characters": f"Created\nEDW_SQL.sublime-completions in {plugin_path}\nEDW_SQLAlias.custom-completions in {metastore_path}\n\nRetrieving all the accessible columns ({conn.cursor.rowcount}) from EDW, this should take around 3 min..."
                    },
                )
                self.window.run_command("show_panel", {"panel": "output.meta_init"})

                completions, all_lst = conn.parse_all_accessible_meta()

                with open(metastore_path + "\\all.connection-group", "w") as f:
                    f.write(json.dumps(completions))
                with open(metastore_path + "\\all.drop-down", "w") as f:
                    f.write("\n".join(all_lst))
                with open(metastore_path + "\\EDW_SQL.connection-group-list", "a") as f:
                    f.write("all\n")
                auto_complete = {
                    "enable": True,
                    "fileExtensions": ["sql"],
                    "separator": ".",
                    "completions": {},
                    "current_selection": "all",
                }
                auto_complete.update(completions)
                with open(metastore_path + "\\EDW_SQL.custom-completions", "w") as f:
                    file = json.dumps(auto_complete)
                    f.write(file)

                panel.run_command(
                    "append",
                    {
                        "characters": f"\nFinish loading {conn.cursor.rowcount} columns in automcomplete\nCreated connection group as `all` for all accessible tables"
                    },
                )
                panel.set_read_only(True)
                self.window.run_command("show_panel", {"panel": "output.meta_init"})
                self.window.run_command("meta_select_connection")

                sublime.message_dialog(
                    f"Successfully load {len(all_lst)} columns in autocomplete!!!"
                )
            finally:
                pass

        def print_status_msg(self, t1, timeout=360):
            duration = 0
            while t1.is_alive() and duration < timeout:
                time.sleep(1)
                sublime.status_message(
                    f"Building autocomplete metadata for {duration} seconds..."
                )
                duration += 1
            if duration >= timeout:
                stop_thread(t1)
                # sleep to wait until thread_active show as all stopped
                panel = self.window.create_output_panel("timeout")
                panel.set_read_only(False)
                panel.settings().set("word_wrap", False)
                # why this wierd threading._active.items() mark finished thread as unfinished?
                # All threads: {list(threading._active.items())}
                panel.run_command(
                    "insert",
                    {
                        "characters": f"Execution timeout after {timeout} seconds, thread_number {t1.native_id}.\nCheck VPN or increase timeout in key binding args for run_sql_cmd"
                    },
                )
                panel.set_read_only(True)
                self.window.run_command("show_panel", {"panel": "output.timeout"})

        if credential_set(show_msg=False) is False:
            # sublime.message_dialog(
            #     "Teradata username or password not setup\n use ctrl+e,ctrl+p to setup"
            # )
            # assert False
            self.window.run_command("meta_password")

        t1 = threading.Thread(
            target=main_func,
            args=[self],
            name="meta_init",
        )
        t2 = threading.Thread(
            target=print_status_msg,
            args=[self, t1],
            name=f"meta_timeout",
        )
        t1.start()
        t2.start()


class MetaAdd(sublime_plugin.WindowCommand):
    def run(self, load_dtype):
        if credential_set(show_msg=False) is False:
            sublime.message_dialog(
                "Teradata username or password not setup\n use ctrl+e,ctrl+p to setup"
            )
            assert False

        self.load_dtype = load_dtype
        input_panel = self.window.show_input_panel(
            "Table to add for autocomplete (In case multiple,split by comma): ",
            "e.g. db1.tbl,db2.tbl2,db.tbl3",
            self.on_done,
            None,
            None,
        )

    def on_done(self, tbl_to_pull):
        def main_func(self, tbl_to_pull):
            def on_execute(user_input):
                connection_path = metastore_path + f"\\{user_input}.connection-group"
                try:
                    with open(connection_path, "r") as f:
                        file = f.read()
                    auto_complete = json.loads(file)
                    completions = auto_complete["completions"]
                    for db, tbl_col in new_final.items():
                        if completions.get(db) is None:
                            completions.update(new_final)
                        else:
                            completions[db].update(tbl_col)
                    auto_complete["completions"] = completions
                except:
                    auto_complete = {"completions": new_final}

                with open(connection_path, "w") as f:
                    f.write(json.dumps(auto_complete))

                with open(connection_group_list_path, "a") as f:
                    f.write(user_input + "\n")
                self.window.run_command("meta_select_connection")

            try:
                conn = teradata_connect()
                panel = self.window.create_output_panel("meta_add")
                panel.set_read_only(False)
                panel.settings().set("word_wrap", False)
                pannel_text = ""
                if "," in tbl_to_pull:
                    tbl_to_pull = tbl_to_pull.split(",")
                else:
                    tbl_to_pull = [tbl_to_pull]
                tbl_to_pull = [
                    tbl.lower()
                    for tbl in tbl_to_pull
                    if tbl not in ["", " ", "\n", "\t"]
                ]

                final = {}
                for tbl in tbl_to_pull:
                    db, tbl_name = tbl.split(".")
                    final[db] = {}

                for tbl in tbl_to_pull:
                    db, tbl_name = tbl.split(".")
                    if self.load_dtype:
                        meta = conn.get_tbl_meta(tbl, simplify=True)
                    else:
                        meta = conn.get_tbl_meta_cols_only(tbl)
                    if meta is None:
                        panel.run_command(
                            "append", {"characters": f"{db}.{tbl_name} not found\n"}
                        )
                        pannel_text += f"{db}.{tbl_name} not found\n"
                        self.window.run_command(
                            "show_panel", {"panel": "output.meta_add"}
                        )
                    else:
                        final[db].update({tbl_name: meta})
                        panel.run_command(
                            "append",
                            {
                                "characters": f"finish add {db}.{tbl_name} to autocomplete list\n"
                            },
                        )

                        self.window.run_command(
                            "show_panel", {"panel": "output.meta_add"}
                        )
                        pannel_text += (
                            f"finish add {db}.{tbl_name} to autocomplete list\n"
                        )
                # prune
                sublime.set_clipboard(pannel_text)
                new_final = {}
                for db in final:
                    if final[db] == {}:
                        pass
                    else:
                        new_final[db] = final[db]

                panel.set_read_only(True)

                with open(metastore_path + "\\EDW_SQL.custom-completions") as f:
                    js = json.loads(f.read())

                cur_conn = js["current_selection"]
                input_panel = self.window.show_input_panel(
                    "Enter Connection Group Name (Default is current conn group)",
                    cur_conn,
                    on_execute,
                    None,
                    None,
                )
                sublime.set_clipboard(pannel_text)
            finally:
                pass

        def print_status_msg(self, t1, timeout=180):
            duration = 0
            while t1.is_alive() and duration < timeout:
                time.sleep(1)
                sublime.status_message(
                    f"Building autocomplete metadata for {duration} seconds..."
                )
                duration += 1
            if duration >= timeout:
                stop_thread(t1)
                # sleep to wait until thread_active show as all stopped
                panel = self.window.create_output_panel("timeout")
                panel.set_read_only(False)
                panel.settings().set("word_wrap", False)
                # why this wierd threading._active.items() mark finished thread as unfinished?
                # All threads: {list(threading._active.items())}
                panel.run_command(
                    "insert",
                    {
                        "characters": f"Execution timeout after {timeout} seconds, thread_number {t1.native_id}.\nCheck VPN or increase timeout in key binding args for run_sql_cmd"
                    },
                )
                panel.set_read_only(True)
                self.window.run_command("show_panel", {"panel": "output.timeout"})

        t1 = threading.Thread(
            target=main_func,
            args=[self, tbl_to_pull],
            name="meta_add",
        )
        t2 = threading.Thread(
            target=print_status_msg,
            args=[self, t1],
            name=f"meta_timeout",
        )
        t1.start()
        t2.start()


class MetaSelectConnection(sublime_plugin.WindowCommand):
    def run(
        self,
        msg="Please Select following Connection Group for auto-complete",
        msg_out=None,
    ):
        with open(connection_group_list_path, "r") as f:
            file = f.read()
        conn_lst = file.split("\n")
        conn_lst = list(set(conn_lst))
        print(conn_lst)
        to_return = []
        to_show = []
        for conn in conn_lst:
            if conn not in ["", ",", " ", "\t"]:
                path = metastore_path + f"\\{conn}.connection-group"
                with open(path, "r") as f:
                    js = json.loads(f.read())
                completions = js["completions"]
                tbls = ",".join(
                    f"{db}({ ','.join(list(tbl)[:3])}...)"
                    for db, tbl in completions.items()
                )
                to_show.append([conn, tbls])
                to_return.append(conn)

        self.conn_lst = to_return
        self.msg_out = msg_out
        print(conn_lst)
        self.window.show_quick_panel(
            to_show,
            self.on_done,
            0,
            0,
            placeholder=msg,
        )

    def on_done(self, index):
        if index == -1:
            return

        select = self.conn_lst[index]
        path = metastore_path + f"\\{select}.connection-group"

        with open(metastore_path + "\\EDW_SQL.custom-completions", "r") as f:
            original = json.loads(f.read())

        with open(path, "r") as f:
            to_add = json.loads(f.read())

        original.update(to_add)
        original["current_selection"] = select

        with open(metastore_path + "\\EDW_SQL.custom-completions", "w") as f:
            f.write(json.dumps(original))
        # self.window.run_command("meta_open_current_connection")
        if self.msg_out is not None:
            sublime.message_dialog(self.msg_out)


class MetaUpdateConnection(MetaSelectConnection):
    def on_done(self, index):
        if index == -1:
            return
        select = self.conn_lst[index]
        path = metastore_path + f"\\{select}.connection-group"

        with open(path) as f:
            js = json.loads(f.read())
        auto_complete = js["completions"]

        all_tbls = []
        for db, tbls in auto_complete.items():
            for tbl in tbls:
                all_tbls.append(f"{db}.{tbl}")
        print(all_tbls)

        def main_func(self, tbl_to_pull):
            conn = teradata_connect()
            panel = self.window.create_output_panel("meta_add")
            panel.set_read_only(False)
            panel.settings().set("word_wrap", False)

            final = {}
            for tbl in tbl_to_pull:
                db, tbl_name = tbl.split(".")
                final[db] = {}

            for tbl in tbl_to_pull:
                db, tbl_name = tbl.split(".")
                meta = conn.get_tbl_meta(tbl, simplify=True)
                if meta is None:
                    panel.run_command(
                        "append", {"characters": f"{db}.{tbl_name} not found\n"}
                    )
                    self.window.run_command("show_panel", {"panel": "output.meta_add"})
                else:
                    final[db].update({tbl_name: meta})
                    panel.run_command(
                        "append",
                        {
                            "characters": f"finish add {db}.{tbl_name} to autocomplete list\n"
                        },
                    )

                    self.window.run_command("show_panel", {"panel": "output.meta_add"})
            panel.set_read_only(True)
            final = {"completions": final}
            with open(path, "w") as f:
                f.write(json.dumps(final))
            self.window.run_command("meta_select_connection")

        def print_status_msg(self, t1, timeout=180):
            duration = 0
            while t1.is_alive() and duration < timeout:
                time.sleep(1)
                sublime.status_message(
                    f"Building autocomplete metadata for {duration} seconds..."
                )
                duration += 1
            if duration >= timeout:
                stop_thread(t1)
                # sleep to wait until thread_active show as all stopped
                panel = self.window.create_output_panel("timeout")
                panel.set_read_only(False)
                panel.settings().set("word_wrap", False)
                # why this wierd threading._active.items() mark finished thread as unfinished?
                # All threads: {list(threading._active.items())}
                panel.run_command(
                    "insert",
                    {
                        "characters": f"Execution timeout after {timeout} seconds, thread_number {t1.native_id}.\nCheck VPN or increase timeout in key binding args for run_sql_cmd"
                    },
                )
                panel.set_read_only(True)
                self.window.run_command("show_panel", {"panel": "output.timeout"})

        t1 = threading.Thread(
            target=main_func,
            args=[self, all_tbls],
            name="meta_refresh",
        )
        t2 = threading.Thread(
            target=print_status_msg,
            args=[self, t1],
            name=f"meta_timeout",
        )
        t1.start()
        t2.start()


class MetaDeleteConnection(MetaSelectConnection):
    def on_done(self, index):
        if index == -1:
            return

        select = self.conn_lst[index]

        with open(metastore_path + "\\EDW_SQL.connection-group-list", "r") as f:
            file = f.read()

        file = file.replace(select, "")
        with open(metastore_path + "\\EDW_SQL.connection-group-list", "w") as f:
            f.write(file)

        os.remove(metastore_path + f"\\{select}.connection-group")

        with open(metastore_path + "\\EDW_SQL.custom-completions", "r") as f:
            original = json.loads(f.read())
        if original["current_selection"] == select:
            original["completions"] = {}
            original["current_selection"] = ""
            with open(metastore_path + "\\EDW_SQL.custom-completions", "w") as f:
                f.write(json.dumps(original))
            # self.window.run_command("meta_open_current_connection")

            sublime.message_dialog(
                f"Removed connection {select}!\n And it is current selection\nPlease use ctrl+m, ctrl+s to reselect current connection"
            )
        else:
            sublime.message_dialog(f"Removed connection {select}!")


class MetaOpenCurrentConnection(
    sublime_plugin.TextCommand, sublime_plugin.EventListener
):
    def __init__(self, view=None):
        self.view = view
        self.__path = metastore_path + "\\EDW_SQL.custom-completions"

    def run(self, edit):
        self.view.window().open_file(self.__path)

    def on_load_async(self, view):
        print("triggered")
        if view.file_name() == self.__path:
            view.assign_syntax("Packages/JSON/JSON.sublime-syntax")
            view.window().run_command("js_format")
            view.window().run_command("save", args={"async": True})


class MetaBrowseConnection(sublime_plugin.TextCommand):
    def run(self, edit, current):
        if current:
            with open(metastore_path + "\\EDW_SQL.custom-completions", "r") as f:
                js = json.loads(f.read())

            js = js["completions"]
            col_lst = []
            for db, tbls in js.items():
                for tbl, cols in tbls.items():
                    for col in cols:
                        col_lst.append(f"{db}.{tbl}.{col}")
            col_lst = sorted(col_lst)
        else:
            with open(metastore_path + "\\all.drop-down", "r") as f:
                file = f.read()
            col_lst = file.split("\n")
            col_lst = sorted(col_lst)

        self.col_lst = col_lst
        self.view.window().show_quick_panel(self.col_lst, self.on_done, 0, 0)

    def on_done(self, index):
        if index == -1:
            return
        select = self.col_lst[index]
        db, tbl, col = select.split(".")
        with open(metastore_path + "\\EDW_SQLAlias.custom-completions", "r") as f:
            file = f.read()

        js = json.loads(file)
        js["alias"].update({"a": f"{db}.{tbl}"})
        with open(metastore_path + "\\EDW_SQLAlias.custom-completions", "w") as f:
            f.write(json.dumps(js))

        txt = f"select a.{col}  from {db}.{tbl} as a;"
        cur = self.view.sel()[0].begin() + 10 + len(col)
        self.view.run_command("insert", {"characters": txt})
        self.view.sel().clear()
        self.view.sel().add(cur)


class MetaImportLocalConnection(sublime_plugin.WindowCommand):
    def run(self):
        sublime.open_dialog(self.print_path)

    def print_path(self, path):
        self.path = path
        input_panel = self.window.show_input_panel(
            "Enter Connection Group Name: ",
            "",
            self.on_done,
            None,
            None,
        )

    def on_done(self, user_input):
        imported_conn = f"{user_input}.connection-group"
        assert imported_conn not in os.listdir(
            metastore_path
        ), f"Connection group {user_input} is exist, choose another one"
        write_path = os.path.join(metastore_path, imported_conn)

        conn_group_lst_path = os.path.join(
            metastore_path, "EDW_SQL.connection-group-list"
        )

        read_path = self.path
        with open(read_path, "r") as f:
            file = f.read()
        with open(write_path, "w") as f:
            f.write(file)
        with open(conn_group_lst_path, "a") as f:
            f.write(f"\n{user_input}\n")
        sublime.message_dialog(
            f"Successfully imported connection group `{user_input}` !!!"
        )


class MetaRemoveTableInConnGroup(MetaSelectConnection):
    def on_done(self, index):
        if index == -1:
            return

        select = self.conn_lst[index]
        path = metastore_path + f"\\{select}.connection-group"

        with open(path, "r") as f:
            conn_group = json.loads(f.read())

        completions = conn_group["completions"]

        to_show = []
        for db in completions:
            tbls = completions[db]
            for tbl in tbls:
                to_show.append(f"{db}.{tbl}")

        self.tbls = to_show
        self.conn_group = conn_group
        self.path = path
        self.select = select

        self.window.show_quick_panel(
            to_show,
            self.on_done2,
            0,
            0,
            placeholder=f"Please Select Table You want to remove from `{select}`",
        )

    def on_done2(self, index):
        if index == -1:
            return

        remove = self.tbls[index]
        db, tbl = remove.split(".")
        self.conn_group["completions"][db].pop(tbl)
        with open(self.path, "w") as f:
            json.dump(self.conn_group, f)

        self.window.run_command(
            "meta_select_connection",
            args={
                "msg": "Please Re-select Conn Group for updating auto-complete",
                "msg_out": f"Table `{remove}` has been removed from Conn-Group `{self.select}` for auto-complete",
            },
        )

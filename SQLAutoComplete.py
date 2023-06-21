import sublime_plugin
import sublime
import os
import json
import sys
import sqlparse

type_mapping = {
    "i": "Int",
    "f": "Float",
    "t": "Timestamp",
    "d": "Date",
    "s": "String",
    "b": "Boolean",
    "None": "None",
    "*": "*",
}


class color:
    """
    print(f"{color.BOLD} HAHAH {color.END} dasda")
    """

    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


# do we need to lower the completion column?


def load_alias():
    resource = sublime.find_resources("EDW_SQLAlias.custom-completions")
    assert len(resource) == 1, "Only take one EDW_SQL.custom-completions"
    file = resource[0]
    jsonString = sublime.load_resource(file)
    jsonValues = sublime.decode_value(jsonString)
    return jsonValues, file


def write_to_alias(alias_dict):
    os.chdir(sublime.installed_packages_path())
    os.chdir("..")

    jsonValues, file = load_alias()
    if jsonValues["allowed_alias_num"] < len(jsonValues["alias"]):
        jsonValues["alias"] = {}

    jsonValues["alias"].update(alias_dict)

    path = os.path.join(os.getcwd(), file).replace("/", "\\")
    to_write = json.dumps(jsonValues)
    with open(path, "w") as f:
        f.write(to_write)


class EventListener(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        # find table as a pattern IN
        def is_alias(view, cursor, all_tables):
            # load setting for word sep, uncheck space then bring it back
            # find preceding 3 word
            a = view.lines(cursor)[0].a
            b = view.lines(cursor)[0].b
            if a > b:
                a, b = b, a
            current_line_str = view.substr(sublime.Region(a, b))
            current_line_lst = current_line_str.split(" ")
            intersection = list(set(current_line_lst) & set(all_tables))
            if len(intersection) == 0:
                return
            else:
                for tbl in intersection:
                    idx = current_line_lst.index(tbl)
                    if current_line_lst[idx + 1].lower() == "as" and idx + 2 < len(
                        current_line_lst
                    ):
                        alias = current_line_lst[idx + 2]
                        if alias in (";", ",", ".", "", " "):
                            return
                        alias = alias.replace(";", "").replace(",", "")
                        alias_dict = {alias: tbl}
                        current_aliases = write_to_alias(alias_dict)
                        # final.update(alias_dict)
            print("Line start {}, end {}, string is {}".format(a, b, current_line_str))

        #  Get JSON Data  #

        # settings.set("word_separators", "/\\()\"'-:,;<>~!@#$%^&*|+=[]{}`~?")
        # sublime.save_settings("Preferences.sublime-settings")

        # customCompletion_Files = sublime.find_resources("EDW_SQL.custom-completions")
        # file = customCompletion_Files[0]
        # jsonString = sublime.load_resource(file)
        # jsonValues = sublime.decode_value(jsonString)

        # ws1 = view.settings().get("word_separators")
        # if "." in ws1:
        #     ws2 = ws1.replace(".", "")
        #     view.settings().set("word_separators", ws2)

        with open(f"{metastore_path}\\EDW_SQL.custom-completions", "r") as f:
            jsonValues = json.loads(f.read())
        fileExtensions = jsonValues["fileExtensions"]
        completionSeparator = jsonValues["separator"]
        jsonCompletions = jsonValues["completions"]
        all_tables = [
            "{}.{}".format(db, tbl_key)
            for db, tbl in jsonCompletions.items()
            for tbl_key, cols in tbl.items()
        ]
        enable = jsonValues["enable"]
        # alias = jsonValues["alias"]

        if enable is not True:
            return

        if len(fileExtensions) == 0:
            fileExtension_Verification_Enabled = False
        else:
            fileExtension_Verification_Enabled = True

        #  Verify File Extension  #

        # print(fileExtensions,completionSeparator,jsonCompletions,customCompletion_Files)
        # print(sublime.file_name)
        syntax = view.settings().get("syntax")
        syntax = syntax.split("/")[1].lower()

        fileExtension_Match_Found = False
        for extension in fileExtensions:
            if extension.lower() == syntax:
                fileExtension_Match_Found = True

        # print(syntax,extension)

        if (
            fileExtension_Verification_Enabled == True
            and fileExtension_Match_Found == False
        ):
            return []

        settings = sublime.load_settings("Preferences.sublime-settings")
        sep = settings.get("word_separators")

        if sep == "./\\()\"'-:,.;<>~!@#$%^&*|+=[]{}`~?":
            # user not update user setting, default value will be loaded
            settings.set("word_separators", "/\\()\"'-:,;<>~!@#$%^&*|+=[]{}`~?")
            settings.set("auto_complete_commit_on_tab", True)
            sublime.save_settings("Preferences.sublime-settings")

        elif sep == "./\\()\"'-:,;<>~!@#$%^&*|+=[]{}`~?":
            # user use ctrl+e+. to add dot
            # logic loop with sa_add_dot_in_word_sep
            # sep = sep.replace(".", "")
            # settings.set("word_separators", sep)
            # sublime.save_settings("Preferences.sublime-settings")
            sublime.message_dialog(
                f"To enable autocomplete correctly\nPlease got to CAFTeradata => Miscellaneous => Add/Remove Dot\nor\nRun ctrl+e,ctrl+. (press `ctrl`, `e`, `.` in sequence) to remove the dot in word_separtor"
            )
        elif "." in sep:
            # user has preset the word_sep with a different value
            sublime.error_message(
                f"Detect dot(.) in word_separtor:\n\n      {sep}      \n\nPlease manually delete dot"
            )
            return
        # print("testings2", view.settings().get("word_separators"))
        input_cursor_word = []
        for cursor in view.sel():
            alias_dict = is_alias(view, cursor, all_tables)
            input_cursor_word.append(view.substr(view.word(cursor)))

        print("current cursor word", input_cursor_word)

        #  Populate Completions  #
        completions = []
        preload = False
        for word in input_cursor_word:
            ct = word.count(completionSeparator)
            if ct == 0:
                for db in jsonCompletions:
                    txt_show = db + f"\tdatabase"
                    completions.append((txt_show, db))
            if ct == 1:
                db, temp = word.split(completionSeparator)
                if db in jsonCompletions:
                    tbl_lst = list(jsonCompletions[db].keys())
                    print(tbl_lst)
                    for tbl in tbl_lst:
                        txt = db + completionSeparator + tbl
                        txt_show = txt + "\ttable"
                        completions.append((txt_show, txt))

            if ct == 2:
                db, tbl, temp = word.split(completionSeparator)
                if db in jsonCompletions:
                    tbl_lst = list(jsonCompletions[db].keys())
                    if tbl in tbl_lst:
                        cols = jsonCompletions[db][tbl]
                        expand = ",".join([f"a.{i}" for i in cols])

                        if isinstance(cols, dict):
                            has_dtype = True
                            cols.update({"*": "*"})
                            cols.update({"-": "expand"})
                        else:
                            has_dtype = False
                            cols.insert(0, "-")
                            cols.insert(0, "*")
                        for col in cols:
                            if col == "-":
                                txt_show = f"{db}.{tbl}.-\texpand"
                                txt_auto_complete = (
                                    f"SELECT $0{expand} FROM {db}.{tbl} as a;"
                                )
                            else:
                                txt = (
                                    db
                                    + completionSeparator
                                    + tbl
                                    + completionSeparator
                                    + col
                                )

                                if has_dtype:
                                    dtype = type_mapping[cols[col]]
                                    txt_show = txt + f"\t{dtype}"
                                else:
                                    txt_show = txt + "\t col"

                                txt_auto_complete = (
                                    f"SELECT a.{col}$0 FROM {db}.{tbl} as a ;"
                                )
                            preload = True
                            completions.append((txt_show, txt_auto_complete))

        alias_dict, file = load_alias()
        alias_dict = alias_dict["alias"]
        if preload:
            alias_dict.update({"a": f"{db}.{tbl}"})
            write_to_alias(alias_dict)
            print("preload alias dict", alias_dict)

        for word in input_cursor_word:
            ct = word.count(completionSeparator)
            if ct == 1:
                alias, temp = word.split(completionSeparator)
                if alias in alias_dict:
                    tbl = alias_dict[alias]
                    db, tbl_temp = tbl.split(".")
                    cols = jsonCompletions[db][tbl_temp]
                    if isinstance(cols, dict):
                        has_dtype = True
                        cols.update({"*": "*"})
                    else:
                        has_dtype = False
                        cols.insert(0, "*")
                    for col in cols:
                        txt = alias + completionSeparator + col
                        if has_dtype:
                            dtype = type_mapping[cols[col]]
                            txt_show = txt + f"\t{dtype}"
                        else:
                            txt_show = txt + "\t col"
                        completions.append((txt_show, txt))

        # settings = sublime.load_settings("Preferences.sublime-settings")
        # settings.set("word_separators", "./\\()\"'-:,.;<>~!@#$%^&*|+=[]{}`~?")
        # sublime.save_settings("Preferences.sublime-settings")
        # view.settings().set("word_separators", ws1)
        # print(ws1)
        return (completions, sublime.INHIBIT_WORD_COMPLETIONS)


class SaFormat(sublime_plugin.TextCommand):
    def run(self, edit):
        selectionRegions = self.getSelectionRegions()
        format_style = {
            "keyword_case": "upper",
            "identifier_case": None,
            "strip_comments": False,
            "indent_tabs": False,
            "indent_width": 4,
            "reindent": True,
        }
        for region in selectionRegions:
            textToFormat = self.view.substr(region)
            self.view.replace(edit, region, self.formatSql(textToFormat, format_style))

    def getSelectionRegions(self):
        expandedRegions = []
        if not self.view.sel():
            print("return None")
            return None

        expandTo = "file"

        for region in self.view.sel():
            # if user did not select anything - expand selection,
            # otherwise use the currently selected region
            if region.empty():
                if expandTo in ["file", "view"]:
                    region = sublime.Region(0, self.view.size())
                    # no point in further iterating over selections, just use entire file
                    return [region]

                else:
                    # expand to line
                    region = self.view.line(region)

            # even if we could not expand, avoid adding empty regions
            if not region.empty():
                expandedRegions.append(region)

        return expandedRegions

    def formatSql(self, raw, settings):
        try:
            result = sqlparse.format(raw, **settings)
            return result
        except Exception:
            return None

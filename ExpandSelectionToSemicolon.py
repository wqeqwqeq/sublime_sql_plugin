import sublime, sublime_plugin
from datetime import datetime


class ExpandSelectionToSemicolon(sublime_plugin.TextCommand):
    def run(self, edit, mode, endstart=None):
        def replace_region(start, end, mode, endstart):

            self.view.sel().clear()
            self.view.sel().add(sublime.Region(start, end))
            for sel in self.view.sel():
                content = self.view.substr(sel)
                if "Done" in content:
                    content = content.replace("Done", " " * len("Done"), 1)
                if "Not     " in content:
                    print("Not here")
                    content = content.replace("Not     ", " " * len("Not Done"), 1)

                print(content, len(content))
                content = list(content)
                num_lst = list(range(start, end))
                # find first non space and non

                for first_non_space_index, word in zip(num_lst, content):
                    if word not in ["\n", " ", " "]:
                        break

            self.view.sel().clear()
            self.view.sel().add(sublime.Region(first_non_space_index, end))
            sel = self.view.sel()[0]
            if mode != "select":
                new_content = self.view.substr(sel)

                spacebtw = endstart - len(new_content) - len(mode) - 1
                spaces = " " * spacebtw

                final = spaces + mode
                print(final)
                self.view.insert(edit, end + 1, final)

                # charlen = len(mode)
                # new_mode = " "*(endstart-charlen)+mode
                # self.view.insert(edit,end+1,new_mode)
                # new_end_point = end+1+len(new_mode)
                # self.view.sel().clear()
                # print(first_non_space_index, end+1,mode)
                self.view.sel().clear()
                self.view.sel().add(first_non_space_index)

        def process_func(cursors, mode, endstart):
            for sel in cursors:
                semicolon = list(map(lambda x: x.begin(), self.view.find_all(";")))
                # print(semicolon, sel, sel.begin(), sel.end())
                # no semicolon in file
                if len(semicolon) == 0:
                    return
                # only one semicolon in entire file
                elif len(semicolon) == 1:
                    replace_region(0, semicolon[0], mode, endstart)
                # currently only support single cursor, not selection cursor with region
                elif len(semicolon) >= 1:
                    print("multiple semi")
                    cursor_begin = sel.begin()
                    cursor_end = sel.end()

                    # only has one cursor
                    # must be on the left side of the semicolon
                    if cursor_begin == cursor_end and cursor_begin + 1 not in semicolon:
                        print(cursor_begin, cursor_end, semicolon)

                        lst = sorted(semicolon + [cursor_begin])
                        idx = lst.index(cursor_begin)
                        # in case cursor begin is the first index, which means there is no semicolon before current cursor
                        if lst[0] == cursor_begin:
                            start = 0
                            end = lst[idx + 1]
                            replace_region(start, end, mode, endstart)
                        # in case btw two ;, start+1 get the right of ;, all the way till the left of second ;
                        else:
                            start = lst[idx - 1]
                            end = lst[idx + 1]
                            replace_region(start + 1, end, mode, endstart)

                return

        # assert mode in ["select","Done","Not Done"],"not exist"
        cursors = self.view.sel()
        process_func(cursors, mode, endstart)


class InsertTodayDate(sublime_plugin.TextCommand):
    def run(self, edit):
        for cur in self.view.sel():
            assert cur.begin() == cur.end(), "Selection region mode not available"
            now = datetime.now().date()
            year = str(now.year)
            month = now.month
            month = "0" + str(month) if month < 10 else str(month)
            day = now.day
            day = "0" + str(day) if day < 10 else str(day)

            final = month + "/" + day + "/" + year

            self.view.insert(edit, cur.begin(), final + ": ;\n")


class ExpandSelectionToQuotesCommand(sublime_plugin.TextCommand):
    def run(self, edit):

        double_quotes = list(map(lambda x: x.begin(), self.view.find_all('"')))
        single_quotes = list(map(lambda x: x.begin(), self.view.find_all("'")))
        backtick_quotes = list(map(lambda x: x.begin(), self.view.find_all("`")))
        print(double_quotes, self.view.find_all('"'))

        def search_for_quotes(q_type, quotes):
            q_size, before, after = False, False, False

            if len(quotes) - self.view.substr(sel).count('"') >= 2:
                print(self.view.substr(sel))
                print(quotes, q_size, before, after, sel.begin(), sel.end())
                all_before = list(filter(lambda x: x < sel.begin(), quotes))
                all_after = list(filter(lambda x: x >= sel.end(), quotes))

                if all_before:
                    before = all_before[-1]
                if all_after:
                    after = all_after[0]

                if all_before and all_after:
                    q_size = after - before
            return q_size, before, after

        def replace_region(start, end):
            if sel.size() < end - start - 2:
                start += 1
                end -= 1
            self.view.sel().subtract(sel)
            self.view.sel().add(sublime.Region(start, end))

        for sel in self.view.sel():

            d_size, d_before, d_after = search_for_quotes('"', double_quotes)
            s_size, s_before, s_after = search_for_quotes("'", single_quotes)
            b_size, b_before, b_after = search_for_quotes("`", backtick_quotes)
            print(d_size, d_before, d_after)
            if (
                d_size
                and (not s_size or d_size < s_size)
                and (not b_size or d_size < b_size)
            ):
                replace_region(d_before, d_after + 1)
            elif (
                s_size
                and (not d_size or s_size < d_size)
                and (not b_size or s_size < b_size)
            ):
                replace_region(s_before, s_after + 1)
            elif (
                b_size
                and (not d_size or b_size < d_size)
                and (not s_size or b_size < s_size)
            ):
                replace_region(b_before, b_after + 1)

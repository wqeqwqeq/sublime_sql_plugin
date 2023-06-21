import sublime
import sublime_plugin


class ToggleReadOnlyCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        view = sublime.active_window().active_view()
        view.set_read_only(not view.is_read_only())

    def is_checked(self):
        view = sublime.active_window().active_view()
        if view and view.is_read_only():
            return True

        return False

    def is_enabled(self):
        return sublime.active_window().active_view() is not None

import sublime_plugin
import sublime
import os
import subprocess as sb
from subprocess import PIPE
import shutil
import stat
import time
import threading
import ctypes


def rmtree(top):
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(top)


def check_git_exist():
    cmd = sb.run(
        args="git",
        stdout=sb.PIPE,
        stderr=sb.PIPE,
        universal_newlines=True,
        shell=True,
    )
    if cmd.returncode == 1 and cmd.stderr == "":
        print("Git detected")
        return
    else:
        sublime.set_clipboard(
            "https://carmax.service-now.com/css?id=sc_cat_item&sys_id=eae8eb5edb115d10de4bc139139619c9"
        )
        err = (
            cmd.stderr
            + "\n"
            + "Please download Git at https://carmax.service-now.com/css?id=sc_cat_item&sys_id=eae8eb5edb115d10de4bc139139619c9"
            + "\n"
            + "(The link has copied to your clipboard, please paste in your browser)"
        )
        sublime.error_message(err)


def run_cmd(msg):
    cmd = sb.run(
        args=msg, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True
    )
    if cmd.returncode == 0:
        print(cmd.stdout)
        return True
    else:
        print(cmd.stderr)
        return False


class SetTools(sublime_plugin.WindowCommand):
    def run(self):
        t1 = threading.Thread(
            target=self.main_func,
            name="setup",
        )
        t2 = threading.Thread(
            target=self.time_out_func,
            args=[t1, 60],
            name=f"timeout",
        )
        t1.start()
        t2.start()

    def time_out_func(self, t1, timeout):
        duration = 0
        while t1.is_alive() and duration < timeout:
            time.sleep(1)
            duration += 1
        if duration >= timeout:
            thread_id = t1.native_id
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                thread_id, ctypes.py_object(SystemExit)
            )
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                print("Exception raise failure")
            print(f"Successfull stop thread {thread_id}")
            sublime.message_dialog(f"Update timeout in {t1} seconds")

    def main_func(self):
        check_git_exist()
        print("running")
        os.chdir(package_path)
        os.startfile(user_path)
        is_confirm = self.confirm_msg()
        if is_confirm:
            keybind = run_cmd(
                "git clone https://github.carmax.com/CarMax/sublime_stanley-s_setting.git"
            )

            self.replace_file_in_user("Default (Windows).sublime-keymap")
            self.replace_file_in_user("Preferences.sublime-settings")
            pc = sublime.load_settings("Package Control.sublime-settings")
            pc.set("ignore_vcs_packages", True)
            sublime.save_settings("Package Control.sublime-settings")

            rmtree("sublime_stanley-s_setting")

            if keybind:
                sublime.message_dialog(
                    f"""
Successfully overwrite:  

    Default (Windows).sublime-keymap
    Preferences.sublime-settings

at {user_path}

"""
                )

            else:
                sublime.error_message("Installation failed")
                return
            self.window.run_command("meta_password")

        else:
            return

    def replace_file_in_user(self, file_name):
        read_path = os.path.join(package_path, "sublime_stanley-s_setting", file_name)
        write_path = os.path.join(user_path, file_name)

        with open(read_path, "r") as f:
            file = f.read()

        with open(write_path, "w") as f:
            f.write(file)

    def confirm_msg(self):
        msg = f"""Welcome to CAF Sublime Tools keybind/setting Setup :) 
Please confirm below message before click OK!!!

Will overwrite your existing user
    Keybindings
    Sublime settings 
    Package Control Setting

Please copy below files (if exists) under
{user_path}
to other location (skip if you prefer to match Stanley's version)
    Default (Windows).sublime-keymap
    Preferences.sublime-settings
    Package Control.sublime-settings

Finally manual merge your existing user keybindings and settings (if any) to new one

Path has been automatically open

Hit Cancel to Quit the Setup Process
        """
        return sublime.ok_cancel_dialog(
            msg=msg, title="CAF Sublime Tools KeyBind Setup"
        )


class ZenMode(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings("Preferences.sublime-settings")
        temp = settings.to_dict()
        if self.window.is_minimap_visible():
            settings.set("line_numbers", False)
            self.window.set_minimap_visible(False)
        else:
            settings.set("line_numbers", True)
            self.window.set_minimap_visible(True)
        settings = sublime.save_settings("Preferences.sublime-settings")
        self.window.run_command("toggle_menu")
        self.window.run_command("toggle_full_screen")

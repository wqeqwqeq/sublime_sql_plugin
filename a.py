import sublime
import os
import sys

# this file will load first
# path hub and name hub


plugin_name = "sublime_sql_tool"
package_path = sublime.installed_packages_path()
plugin_path = f"{package_path}\\{plugin_name}"

sys_path = f"{package_path}\\{plugin_name}\\lib"
sys_path2 = f"{package_path}\\{plugin_name}"
lib_path = f"{package_path}\\{plugin_name}\\lib"

if sys_path not in sys.path:
    sys.path.append(sys_path)
    sys.path.append(sys_path2)

if lib_path not in sys.path:
    sys.path.append(lib_path)
if plugin_path not in sys.path:
    sys.path.append(plugin_path)


metastore_path = f"{plugin_path}\\metastore"
connection_group_list_path = f"{metastore_path}\\EDW_SQL.connection-group-list"
cache_path = os.path.join(package_path, plugin_name, "metastore", "cache_query.json")
user_path = os.path.join(package_path, "User")

print(sys.path, "\n\n")

print(metastore_path)
print(connection_group_list_path)
print(cache_path)
print(user_path)


print(plugin_name)
print(package_path)
print(plugin_path)
print(sys_path)
print(sys_path2)
print(lib_path)

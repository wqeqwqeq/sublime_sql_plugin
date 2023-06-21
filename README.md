# Sublime_Teradata_Plugin
Local Teradata friend with Query run and auto complete. An in-house solution to replace Teradata SQL Assistant

Major benefit compare to Teradata SQL Assistant
1. Comprehensive autocomplete in keyword and metadata in EDW
2. Metadata completion granularity reaches to column level in EDW, data type also included; completion can also be triggered from an alias 
3. Able to run query directly from sublime, and show result in a read-only Postgre-sql stype output panel, which is easy to navigate and share
4. Can store query result into cache, show result from same query without another round of execution (user can tweak #cache query)
5. Automatically add keyword SAMPLE in the end for easier data exploration (user can define number of rows and overwrite by explicitly type sample)
6. Show exact query execution time and option to stop query 
7. Short cut to select current query and format current query (where cursor stop)
8. Can also be extended if onboarding with snowflake, EDL (As long as we can use python to query from local)
9. Never need to login and autosave query, no need to worry when close file 
10. User can set a timeout to stop query takes super long, or if VPN is not on 

And more...
## Before install 
If you haven't checkout [Sublime 101](https://github.carmax.com/CarMax/sublime_101), please take a look at the Basic part to understand the definition of command pallet, keybinding, setting and where is sublime package path. 


## Install
### Step 1:
Install 

  * [Sublime](https://www.sublimetext.com/download) (Choose Windows)    
  * [Git](https://carmax.service-now.com/css?id=search&spa=1&q=git) (Select Git and follow instructions to download in Software Center)

### Step 2:
Open Sublime, in top menu, find `Preferences => Browse Packages` to open package folder 
![image](https://github.carmax.com/storage/user/2400/files/de271e45-505a-4c33-827d-9da356fb74d9)

Navigate to Net Drive Folder 
```
\\cafdisk2\fs_risk\CAF Decision Sciences\Resources-Techniques\Sublime Tools
```

And copy **Sublime_Teradata_Plugin**  to sublime's package folder
![image](https://github.carmax.com/storage/user/2400/files/0452885c-dca4-442c-b8fb-55624e569929)

### Step 3:
Click `Clone Settings` in top menu, read carefully about the prompt. This process will clone Stanley's Keymap, Sublime Setting and Package Control Setting to your Sublime user folder

Finally, enter your Teradata Username and Password as one-time login to connect with EDW

![image](https://github.carmax.com/storage/user/2400/files/cfa1ca8b-a208-42e6-b1d0-eb3cee8b9cc0)

*Relaunch Sublime when you finished Step 3*

### Step 4:
Click `CAFTeradata => Load all Metadata`. Once complete, all the accessible columns in EDW will be stored in auto-complete; for mine, it takes around 3 min to load over 350k columns

Then click `CAFTeradata => Connection-Group => Select Connection Group`, select connection group named `all` to activate the Auto-complete
to grab all the columns into metadata autocomplete in EDW that you have select access.

## Use
### Elmemtary use
#### Setup sublime syntax
Hit `["ctrl+shift+p]` to open command pallet, and type sql, choose _Set syntax: SQL_ and press enter

Alternatively, choose syntax at left bottom, left click and then select SQL. 

**This plugin will only be functional when the syntax is SQL**

![image](https://github.carmax.com/storage/user/2400/files/0d385165-04fd-4812-a4b0-49b221bbcbb6)

#### Trigger autocomplete 
There multiple way to trigger autocomplete
1. Hit `["ctrl+space"]` to check all possible autocomplete item, use arrow key to navigate, and hit `tab` to autocomplete. In case a _database_ or _column_ autocomplete, enter `.` to trigger autocomplete in next level 
2. Type word and if the input match some part of the autocomplete, you will see the autocomplete pallet while you are typing
3. Click `CAFTeradata => Browse Metadata` to show all the columns under current connection group, use arrow key to navigate and hit enter for column you are interested 
4.  Alias auto complete. **Method 1 and 3** can create autocomplete with table's alias automatically. But if you manual type query, you have to type `as` between table and alias in order to update alias-table mapping on the backend 
![image](https://github.carmax.com/storage/user/2400/files/8a3c4f5f-ccc0-40bc-8100-9f7acae961aa)
In case alias overwrite by other query, manually retype `as alias` after the table you want to point to reassign alias to a given table 

#### Run query
1. **Remember to put a semicolon (`;`) at the end of each query!** Semicolon is the separator between queries.
2. You can select your _current query_ (where your current cursor stops) by hit `["ctrl+q"]` or `CAFTeradata => Select Current Query`. It will won't work as expected if `;` missed at the end of the query
3. Hit `["ctrl+e","ctrl+e"]` or `CAFTeradata => Run Query` to run selected query. Currently only supported run one query at a time (Working on running multiple queries)

#### Debug & troubleshooting
For most of time, if you don't see sublime return anything back, a relaunch will fix the problem.

If still sublime does not return anything back, open _teradata sql assistant_ and run the same query, see if it doesn't return anything as well. If it doesn't, try to restart vpn. And if you see result return from `teradata SQL assistant`, but not from `Sublime` after relaunch and restart vpn, re-download this repo by following the installing session, maybe the bug is fixed in newest version. 

If relaunch, restart, redownload all failed, congratulation, you spot a new bug! Contact [Stanley](mailto:stanley_yuan@carmax.com?subject=[Sublime_Teradata_Plugin]%20%20Bug%20Report%20)!

### Advanced Use
For advanced use like 
* add/remove connection group
* interrup query, manage cache/timeout/# rows return
* customizing output pannel
* setup your own keyword autocomplete snippet
* setup your connection point to other edw instance like tdprod2
* restart connection 
* contributing this plugin
* future functionality like connect to snowflake or EDL...

Contact [Stanley](mailto:stanley_yuan@carmax.com?subject=[Sublime_Teradata_Plugin]%20%20Collab%20)! Collab, bugs and suggestions are welcomed:)



## Appedix for Keymap 

Keybind explain (More Keymap/Command is added under `CAFTeradata`. Sometimes this doc is lagged...)

1. Query execution Keymap 
  * `["ctrl+e", "ctrl+e"]` execute the query 
    * `limit:` stands for number of rows to be returned (in this case, means automatically add sample 100 in the end), can be overwrite if pass sample explicitly
    * `number_of_cache_query:` number of cache query stored. More cache and larger data stored in cache may slow down the plugin
    * `timeout:` query will automatically timeout after 30 seconds
    
    ![image](https://github.carmax.com/storage/user/2400/files/0be013f0-ceb0-464d-9b15-a5139b129d95)
 
 * `["ctrl+q"]` select current query (how it works is select query btw two ";", where cursor stops. Except for the first ";" )
 * `["ctrl+e", "ctrl+b"]` format select query
 * `["ctrl+e", "ctrl+i"]` interrupt running query
 * `["ctrl+e", "ctrl+c"]` clean cached query result
2. Metadata/autocomplete management Keymap
 * `["ctrl+m", "ctrl+p"]` setup teradata username and password
 * `["ctrl+m", "ctrl+i"]` init setup autocomplete, will grab **all** db,tbl,columns that user has *retrieve/select* access into a autocompletion connection group
 * `["ctrl+m", "ctrl+a"]` add a list of tables as a connection group to enable autocomplete 
 * `["ctrl+m", "ctrl+s"]` select specific autocomplete connection group
 * `["ctrl+m", "ctrl+d"]` remove specific autocomplete connection group
 * `["ctrl+m", "ctrl+o"]` open current using autocomplete connection group
 * `["ctrl+m", "ctrl+b"]` browse all the columns that user has *retrieve/select* access, and autocomplete as a query if hit enter
 * `["ctrl+m", "ctrl+r"]` restart connection

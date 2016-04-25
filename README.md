# tpm.py

A Python Module for the [TeamPasswordManager API](http://teampasswordmanager.com/docs/api/)

Requires: requests

## Install tpm.py

You can install the tpm module via pip

    pip install tpm

## How to Use

This is an example how you can use it in a python script
```python
#! /usr/bin/env python
import tpm
# create a object for the connection settings
URL = "https://mypasswordpanager.example.com"
USER = 'MyUser'
PASS = 'Secret'
tpmconn = tpm.TpmApiv4(URL, username=USER, password=PASS)

# get a dictionary for all password entries
data = tpmconn.list_passwords()
# show all names from the password entries
for item in data:
    print item.get('name')
```
You can also use Private/Public Key authentication
```python
#! /usr/bin/env python
import tpm
# create a object for the connection settings
URL = "https://mypasswordmanager.example.com"
pubkey = '3726d93f2a0e5f0fe2cc3a6e9e3ade964b43b07f897d579466c28b7f8ff51cd0'
privkey = '87324bedead51af96a45271d217b8ad5ef3f220da6c078a9bce4e4318729189c'
tpmconn = tpm.TpmApiv4(URL, private_key=privkey, public_key=pubkey)

# get a dictionary for all password entries
data = tpmconn.list_passwords()
# show all names from the password entries
for item in data:
    print item.get('name')
```

## Logging
Every function call leads to a at least a logging message.
If you want to log all your script does, you can do it like this:
```python
import logging

# set log file and log level
logfile = 'MyLogFile.log'
loglevel = logging.INFO
logformat = '%(asctime)s - %(levelname)s - %(message)s'

logging.basicConfig(filename=logfile, level=loglevel, format=logformat)
# If you don't want the requests and urllib3 module to log too much
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
```
## Functions explained
### All Functions are also explained at the API documentation
---
### [API Projects](http://teampasswordmanager.com/docs/api-projects)
#### [List Projects](http://teampasswordmanager.com/docs/api-projects/#list_projects)
list_projects()

list_projects_archived()

list_projects_favorite()

list_projects_search(searchstring)

#### (v4 Only) [List Subprojects](http://teampasswordmanager.com/docs/api-projects/#list_subprojects)
list_subprojects(ID)

list_subprojects_action(ID, action)

#### [Show Project](http://teampasswordmanager.com/docs/api-projects/#show_project)
show_project(ID)
#### [List Passwords of Project](http://teampasswordmanager.com/docs/api-projects/#list_pwds_prj)
list_passwords_of_project(ID)
#### [List User Access on Project](http://teampasswordmanager.com/docs/api-projects/#list_users_prj)
list_user_access_on_project(ID)
#### [Create Project](http://teampasswordmanager.com/docs/api-projects/#create_project)
create_project(data)
#### [Update Project](http://teampasswordmanager.com/docs/api-projects/#update_project)
update_project(ID, data)
#### [Change Parten of Project](http://teampasswordmanager.com/docs/api-projects/#change_parent)
change_parent_of_project(ID, NewParrentID)
#### [Update Security of Project](http://teampasswordmanager.com/docs/api-projects/#update_project_security)
update_security_of_project(ID, data)
#### [Archive Project](http://teampasswordmanager.com/docs/api-projects/#arch_unarch_project)
archive_project(ID)
#### [Unarchive Project](http://teampasswordmanager.com/docs/api-projects/#arch_unarch_project)
unarchive_project(ID)
#### [Delete Project](http://teampasswordmanager.com/docs/api-projects/#delete_project)
delete_project(ID)
### [API Passwords](http://teampasswordmanager.com/docs/api-passwords)
#### [List Passwords](http://teampasswordmanager.com/docs/api-passwords/#list_passwords)
list_passwords()

list_passwords_archived()

list_passwords_favorite()

list_passwords_search(searchstring)
#### [Show Password](http://teampasswordmanager.com/docs/api-passwords/#show_password)
show_password(ID)
#### [List User Access on Password](http://teampasswordmanager.com/docs/api-passwords/#list_users_pwd)
list_user_access_on_password(ID)
#### [Create Password](http://teampasswordmanager.com/docs/api-passwords/#create_password)
create_password(data)
#### [Update Password](http://teampasswordmanager.com/docs/api-passwords/#update_password)
update_password(ID, data)
#### [Update Security of Password](http://teampasswordmanager.com/docs/api-passwords/#update_security_password)
update_security_of_password(ID, data)
#### [Update Custom Fields of Password](http://teampasswordmanager.com/docs/api-passwords/#update_cf_password)
update_custom_fields_of_password(ID, data)
#### [Delete Password](http://teampasswordmanager.com/docs/api-passwords/#delete_password)
delete_password(ID)
#### [Lock Password](http://teampasswordmanager.com/docs/api-passwords/#lock_password)
lock_password(ID)
#### [Unlock Password](http://teampasswordmanager.com/docs/api-passwords/#unlock_password)
unlock_password(ID)
### [API MyPasswords](http://teampasswordmanager.com/docs/api-my-passwords)
#### [List MyPasswords](http://teampasswordmanager.com/docs/api-my-passwords/#list_passwords)
list_mypasswords()

list_mypasswords_search(searchstring)
#### [Show MyPassword](http://teampasswordmanager.com/docs/api-my-passwords/#show_password)
show_mypassword(ID)
#### [Create MyPassword](http://teampasswordmanager.com/docs/api-my-passwords/#create_password)
create_mypassword(data)
#### [Update MyPassword](http://teampasswordmanager.com/docs/api-my-passwords/#update_password)
update_mypassword(ID, data)
#### [Delete MyPassword](http://teampasswordmanager.com/docs/api-my-passwords/#delete_password)
delete_mypassword(ID)
### [API Favorites](http://teampasswordmanager.com/docs/api-favorites)
#### [Set Favorite Password](http://teampasswordmanager.com/docs/api-favorites/#set_fav)
set_favorite_password(ID)
#### [Unset Favorite Password](http://teampasswordmanager.com/docs/api-favorites/#del_fav)
unset_favorite_password(ID)
#### [Set Favorite Project](http://teampasswordmanager.com/docs/api-favorites/#set_fav)
set_favorite_project(ID)
#### [Unset Favorite Project](http://teampasswordmanager.com/docs/api-favorites/#del_fav)
unset_favorite_project(ID)
### [API Users](http://teampasswordmanager.com/docs/api-users)
#### [List Users](http://teampasswordmanager.com/docs/api-users/#list_users)
list_users()
#### [Show User](http://teampasswordmanager.com/docs/api-users/#show_user)
show_user(ID)
#### [Show Me/Who am I?](http://teampasswordmanager.com/docs/api-users/#show_me)
show_me()
who_am_i()
#### [Create User](http://teampasswordmanager.com/docs/api-users/#create_user)
create_user(data)
#### [Update User](http://teampasswordmanager.com/docs/api-users/#update_user)
update_user(ID, data)
#### [Change User Password](http://teampasswordmanager.com/docs/api-users/#change_password)
change_user_password(ID, data)
#### [Activate User](http://teampasswordmanager.com/docs/api-users/#activate_deactivate)
activate_user(ID)
#### [Deactivate User](http://teampasswordmanager.com/docs/api-users/#activate_deactivate)
deactivate_user(ID)
#### [Convert User to LDAP](http://teampasswordmanager.com/docs/api-users/#convert_to_ldap)
convert_user_to_ldap(ID, DN)
convert_ldap_user_to_normal(ID)
#### [Delete User](http://teampasswordmanager.com/docs/api-users/#delete_user)
delete_user(ID)
### [API Groups](http://teampasswordmanager.com/docs/api-groups)
#### [List groups](http://teampasswordmanager.com/docs/api-groups/#list_groups)
list_groups()
#### [Show Group](http://teampasswordmanager.com/docs/api-groups/#show_group)
show_group(ID)
#### [Create Group](http://teampasswordmanager.com/docs/api-groups/#create_group)
create_group(data)
#### [Update Group](http://teampasswordmanager.com/docs/api-groups/#update_group)
update_group(ID, data):
#### [Add User to Group](http://teampasswordmanager.com/docs/api-groups/#add_user)
add_user_to_group(GroupID, UserID)
#### [Delete User from Group](http://teampasswordmanager.com/docs/api-groups/#del_user)
delete_user_from_group(GroupID, UserID)
#### [Delete Group](http://teampasswordmanager.com/docs/api-groups/#delete_group)
delete_group(ID)
### [API Password Generator](http://teampasswordmanager.com/docs/api-passwords-generator/)
generate_password()
### [API Version](http://teampasswordmanager.com/docs/api-version/)
get_version()
get_latest_version()
up_to_date()

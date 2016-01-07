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
URL = "https://myPasswordManager.example.com"
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
URL = "https://myPasswordManager.example.com"
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
#### http://teampasswordmanager.com/docs/api-projects/#list_projects
list_projects()
list_projects_archived()
list_projects_favorite()
list_projects_search(searchstring)
#### (v4 Only) http://teampasswordmanager.com/docs/api-projects/#list_subprojects
list_subprojects(ID)
list_subprojects_action(ID, action)
#### http://teampasswordmanager.com/docs/api-projects/#show_project
show_project(ID)
#### http://teampasswordmanager.com/docs/api-projects/#list_pwds_prj
list_passwords_of_project(ID)
#### http://teampasswordmanager.com/docs/api-projects/#list_users_prj
list_user_access_on_project(ID)
#### http://teampasswordmanager.com/docs/api-projects/#create_project
create_project(data)
#### http://teampasswordmanager.com/docs/api-projects/#update_project
update_project(ID, data)
#### http://teampasswordmanager.com/docs/api-projects/#change_parent
change_parent_of_project(ID, NewParrentID)
#### http://teampasswordmanager.com/docs/api-projects/#update_project_security
update_security_of_project(ID, data)
#### http://teampasswordmanager.com/docs/api-projects/#arch_unarch_project
archive_project(ID)
#### http://teampasswordmanager.com/docs/api-projects/#arch_unarch_project
unarchive_project(ID)
#### http://teampasswordmanager.com/docs/api-projects/#delete_project
delete_project(ID)
### [API Passwords](http://teampasswordmanager.com/docs/api-passwords)
#### http://teampasswordmanager.com/docs/api-passwords/#list_passwords
list_passwords()
list_passwords_archived()
list_passwords_favorite()
list_passwords_search(searchstring)
#### http://teampasswordmanager.com/docs/api-passwords/#show_password
show_passwords(ID)
#### http://teampasswordmanager.com/docs/api-passwords/#list_users_pwd
list_user_access_on_password(ID)
#### http://teampasswordmanager.com/docs/api-passwords/#create_password
create_password(data)
#### http://teampasswordmanager.com/docs/api-passwords/#update_password
update_password(ID, data)
#### http://teampasswordmanager.com/docs/api-passwords/#update_security_password
update_security_of_password(ID, data)
#### http://teampasswordmanager.com/docs/api-passwords/#update_cf_password
update_custom_fields_of_password(ID, data)
#### http://teampasswordmanager.com/docs/api-passwords/#delete_password
delete_password(ID)
#### http://teampasswordmanager.com/docs/api-passwords/#lock_password
lock_password(ID)
#### http://teampasswordmanager.com/docs/api-passwords/#unlock_password
unlock_password(ID)
### [API MyPasswords](http://teampasswordmanager.com/docs/api-my-passwords)
#### http://teampasswordmanager.com/docs/api-my-passwords/#list_passwords
list_mypasswords()
#### http://teampasswordmanager.com/docs/api-my-passwords/#list_passwords
list_mypasswords_search(searchstring)
#### http://teampasswordmanager.com/docs/api-my-passwords/#show_password
show_mypasswords(ID)
#### http://teampasswordmanager.com/docs/api-my-passwords/#create_password
create_mypassword(data)
#### http://teampasswordmanager.com/docs/api-my-passwords/#update_password
update_mypassword(ID, data)
#### http://teampasswordmanager.com/docs/api-my-passwords/#delete_password
delete_mypassword(ID)
### [API Favorites](http://teampasswordmanager.com/docs/api-favorites)
#### http://teampasswordmanager.com/docs/api-favorites/#set_fav
set_favorite_password(ID)
#### http://teampasswordmanager.com/docs/api-favorites/#del_fav
unset_favorite_password(ID)
#### http://teampasswordmanager.com/docs/api-favorites/#set_fav
set_favorite_project(ID)
#### http://teampasswordmanager.com/docs/api-favorites/#del_fav
unset_favorite_project(ID)
### [API Users](http://teampasswordmanager.com/docs/api-users)
#### http://teampasswordmanager.com/docs/api-users/#list_users
list_users()
#### http://teampasswordmanager.com/docs/api-users/#show_user
show_user(ID)
#### http://teampasswordmanager.com/docs/api-users/#show_me
show_me()
who_am_i()
#### http://teampasswordmanager.com/docs/api-users/#create_user
create_user(data)
#### http://teampasswordmanager.com/docs/api-users/#update_user
update_user(ID, data)
#### http://teampasswordmanager.com/docs/api-users/#change_password
change_user_password(ID, data)
#### http://teampasswordmanager.com/docs/api-users/#activate_deactivate
activate_user(ID)
#### http://teampasswordmanager.com/docs/api-users/#activate_deactivate
deactivate_user(ID)
#### http://teampasswordmanager.com/docs/api-users/#convert_to_ldap
convert_user_to_ldap(ID, DN)
convert_ldap_user_to_normal(ID)
#### http://teampasswordmanager.com/docs/api-users/#delete_user
delete_user(ID)
### [API Groups](http://teampasswordmanager.com/docs/api-groups)
#### http://teampasswordmanager.com/docs/api-groups/#list_groups
list_groups()
#### http://teampasswordmanager.com/docs/api-groups/#show_group
show_group(ID)
#### http://teampasswordmanager.com/docs/api-groups/#create_group
create_group(data)
#### http://teampasswordmanager.com/docs/api-groups/#update_group
update_group(ID, data):
#### http://teampasswordmanager.com/docs/api-groups/#add_user
add_user_to_group(GroupID, UserID)
#### http://teampasswordmanager.com/docs/api-groups/#del_user
delete_user_from_group(GroupID, UserID)
#### http://teampasswordmanager.com/docs/api-groups/#delete_group
delete_group(ID)
### [API Password Generator](http://teampasswordmanager.com/docs/api-passwords-generator/)
generate_password()
### [API Version](http://teampasswordmanager.com/docs/api-version/)
get_version()
get_latest_version()
up_to_date()

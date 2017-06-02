#! /usr/bin/env python
import tpm
import json
import os
import errno

# Taken from https://stackoverflow.com/a/600612/119527
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def safe_open_w(path):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    path = 'resources/{}'.format(path)
    dirpath = os.path.dirname(path)
    if dirpath != '':
        mkdir_p(dirpath)
    return open(path, 'w')

# create a object for the connection settings
URL = "http://localhost:8080/teampasswordmanager"
USER = 'john'
PASS = 'demopassword'
tpmconn = tpm.TpmApiv4(URL, username=USER, password=PASS)

# Query values
passsearches = ['test', 'reddit', 'facebook', 'dns', 'backup', 'firewall']
mypassearches =['john', 'jonny', 'facebook', 'amazon', 'backup']
projsearches = ['internal', 'company', 'website']
usersearches = ['Alan', 'Frank', 'Brown', 'Black', 'externalorg', 'teampasswordmanager', 'boss']
groupsearches = ['test', 'web', 'work', 'users']

# All projects
AllProjects = tpmconn.list_projects()
AllProjectIDs = []
for project in AllProjects:
    AllProjectIDs.append(project.get('id'))
# All passwords
AllPasswords = tpmconn.list_passwords()
AllPasswordIDs = []
for password in AllPasswords:
    AllPasswordIDs.append(password.get('id'))
# All MyPasswords
AllMyPasswords = tpmconn.list_mypasswords()
AllMyPasswordIDs = []
for mypassword in AllMyPasswords:
    AllMyPasswordIDs.append(mypassword.get('id'))
# All users
AllUsers = tpmconn.list_users()
AllUserIDs = []
for user in AllUsers:
    AllUserIDs.append(user.get('id'))
# All Groups
AllGroups = tpmconn.list_groups()
AllGroupIDs = []
for group in AllGroups:
    AllGroupIDs.append(group.get('id'))

# List projects
data = tpmconn.list_projects()
with safe_open_w('projects.json') as outfile:
    json.dump(data, outfile)

data = tpmconn.list_projects_archived()
with safe_open_w('projects/archived.json') as outfile:
    json.dump(data, outfile)

data = tpmconn.list_projects_favorite()
with safe_open_w('projects/favorite.json') as outfile:
    json.dump(data, outfile)

for search in projsearches:
    data = tpmconn.list_projects_search(search)
    with safe_open_w('projects/search/{}.json'.format(search)) as outfile:
        json.dump(data, outfile)

# subprojects
for project_id in AllProjectIDs:
    data = tpmconn.list_subprojects(project_id)
    with safe_open_w('projects/{}/subprojects.json'.format(project_id)) as outfile:
        json.dump(data, outfile)

for project_id in AllProjectIDs:
    data = tpmconn.list_subprojects_action(project_id, 'new_pwd')
    with safe_open_w('projects/{}/subprojects/new_pwd.json'.format(project_id)) as outfile:
        json.dump(data, outfile)

# show project
for project_id in AllProjectIDs:
    data = tpmconn.show_project(project_id)
    with safe_open_w('projects/{}.json'.format(project_id)) as outfile:
        json.dump(data, outfile)

for project_id in AllProjectIDs:
    data = tpmconn.list_passwords_of_project(project_id)
    with safe_open_w('projects/{}/passwords.json'.format(project_id)) as outfile:
        json.dump(data, outfile)

for project_id in AllProjectIDs:
    data = tpmconn.list_user_access_on_project(project_id)
    with safe_open_w('projects/{}/security.json'.format(project_id)) as outfile:
        json.dump(data, outfile)

## special cases
## create_project(data) == return code 201 Created && created "id": 42
### update_project == return code 204 No content
### change_parent_of_project == return code 204 No content
### update_security_of_project == 204 No content
### archive_project == 204 No content
### unarchive_project == 204 No content
### delete_project == 204 No content

# List passwords
data = tpmconn.list_passwords()
with safe_open_w('passwords.json') as outfile:
    json.dump(data, outfile)

data = tpmconn.list_passwords_archived()
with safe_open_w('passwords/archived.json') as outfile:
    json.dump(data, outfile)

data = tpmconn.list_passwords_favorite()
with safe_open_w('passwords/favorite.json') as outfile:
    json.dump(data, outfile)

for search in passsearches:
    data = tpmconn.list_passwords_search(search)
    with safe_open_w('passwords/search/{}.json'.format(search)) as outfile:
        json.dump(data, outfile)

for password_id in AllPasswordIDs:
    data = tpmconn.show_password(password_id)
    with safe_open_w('passwords/{}.json'.format(password_id)) as outfile:
        json.dump(data, outfile)

for password_id in AllPasswordIDs:
    data = tpmconn.list_user_access_on_password(password_id)
    with safe_open_w('passwords/{}/security.json'.format(password_id)) as outfile:
        json.dump(data, outfile)

## special cases
## create_password(data) == return code 201 Created && created "id": 42
### update_password == return code 204 No content
### update_security_of_password == 204 No content
### update_custom_fields_of_password == 204 No content
### delete_password == 204 No content
### delete_password == 204 No content
### unlock_password == 204 No content


# List MyPasswords
data = tpmconn.list_mypasswords()
with safe_open_w('my_passwords.json') as outfile:
    json.dump(data, outfile)

for search in mypassearches:
    data = tpmconn.list_mypasswords_search(search)
    with safe_open_w('my_passwords/search/{}.json'.format(search)) as outfile:
        json.dump(data, outfile)

for mypassword_id in AllMyPasswordIDs:
    data = tpmconn.show_mypassword(mypassword_id)
    with safe_open_w('my_passwords/{}.json'.format(mypassword_id)) as outfile:
        json.dump(data, outfile)

## special cases
## create_mypassword(data) == return code 201 Created && created "id": 42
### update_mypassword == return code 204 No content
### delete_mypassword == 204 No content


# List Favorites

## special cases
## set_favorite_password(ID) == return 204 No content
### unset_favorite_password(ID) == return code 204 No content
## set_favorite_project(ID) == return 204 No content
### unset_favorite_project(ID) == return code 204 No content

# List Users
data = tpmconn.list_users()
with safe_open_w('users.json') as outfile:
    json.dump(data, outfile)

for user_id in AllUserIDs:
    data = tpmconn.show_user(user_id)
    with safe_open_w('users/{}.json'.format(user_id)) as outfile:
        json.dump(data, outfile)

data = tpmconn.show_me()
with safe_open_w('users/me.json') as outfile:
    json.dump(data, outfile)

## special cases
## create_user(data) == return code 201 Created && created "id": 42
### update_user(ID, data) == return code 204 No content
### change_user_password == 204 No content
### activate_user == 204 No content
### deactivate_user == 204 No content
### convert_user_to_ldap == 204 No content
### convert_ldap_user_to_normal == 204 No content
### delete_user == 204 No content

# List Groups
data = tpmconn.list_groups()
with safe_open_w('groups.json') as outfile:
    json.dump(data, outfile)

for group_id in AllGroupIDs:
    data = tpmconn.show_group(group_id)
    with safe_open_w('groups/{}.json'.format(group_id)) as outfile:
        json.dump(data, outfile)

data = tpmconn.show_me()
with safe_open_w('users/me.json') as outfile:
    json.dump(data, outfile)

## special cases
## create_group(data) == return code 201 Created && created "id": 42
### update_group(ID, data) == return code 204 No content
### add_user_to_group == 204 No content
### delete_user_from_group == 204 No content
### delete_group == 204 No content

# others
### generate_password == 204 No content
### get_version == 204 No content


data = tpmconn.generate_password()
with safe_open_w('generate_password.json'.format()) as outfile:
    json.dump(data, outfile)

data = tpmconn.get_version()
with safe_open_w('version.json'.format()) as outfile:
    json.dump(data, outfile)

data = tpmconn.get_latest_version()
with safe_open_w('version/check_latest.json'.format()) as outfile:
    json.dump(data, outfile)

## special cases
## up_to_date = True or False

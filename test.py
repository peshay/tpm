#! /usr/bin/env python
"""To Test all tpm functions"""
import tpm
import logging

# set log file and log level
logfile = 'test.log'
loglevel = logging.INFO
logformat = '%(asctime)s %(message)s'

logging.basicConfig(filename=logfile, level=loglevel, format=logformat)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# TPM url
URL = 'https://pass.int.censhare.com'
# Test with User/Pass
USER = 'TPM_API_User'
PASS = 'EPs-8hB-MUH-8hJ'
tpmconnCred = tpm.TpmApiv4(URL, username=USER, password=PASS)
# Test with Keys
pubkey = '4025e63673cbc075e2d21cef6bde4c591c263380beebe462df2fed1afad3e3f2'
privkey = '91d10cac8916cf3bc981a5ef9ba331a0389a95a141cf0dfb5c052fa9cdd6f017'
tpmconnKey = tpm.TpmApiv4(URL, private_key=privkey, public_key=pubkey)


"""Create test project."""
NewProj = {'name': 'TestProject',
           'parent_id': 0}
ProjID = tpmconnCred.create_project(NewProj)

"""Update Project."""
UpdData = {'notes': 'Some Testing'}
tpmconnCred.update_project(ProjID, UpdData)

"""Create test password in project."""
NewPass = {'name': 'TestPass', 'project_id': ProjID}
PassID = tpmconnCred.create_password(NewPass)

"""Update Password."""
tpmconnCred.update_password(PassID, UpdData)

"""Create test mypassword."""
NewMyPass = {'name': 'MyTestPass2'}
MyPassID = tpmconnCred.create_mypassword(NewMyPass)

"""Create test User."""
NewUser = {"username": "johnnotboss",
           "email_address": "john@test.com",
           "name": "John",
           "role": "normal user",
           "password": "testpassword"}
UserID = tpmconnCred.create_user(NewUser)

"""Create a group."""
NewGroup = {'name': 'TestGroup'}
GroupID = tpmconnCred.create_group(NewGroup)

"""List Projects."""
AllProjects = tpmconnCred.list_projects()
for Proj in AllProjects:
    if ProjID == Proj.get('id'):
        print ('Project ID found: %s' % ProjID)
        break

"""List Project Passwords."""
AllProjPass = tpmconnCred.list_passwords_of_project(ProjID)
for Pass in AllProjPass:
    if PassID == Pass.get('id'):
        print ('Password ID found: %s' % PassID)
        break

"""List Passwords."""
AllPasses = tpmconnCred.list_passwords()
for Pass in AllPasses:
    if PassID == Pass.get('id'):
        print ('Password ID found: %s' % PassID)
        break

"""Delete All Stuff."""
tpmconnCred.delete_group(GroupID)
tpmconnCred.delete_user(UserID)
tpmconnCred.delete_mypassword(MyPassID)
tpmconnCred.delete_password(PassID)
tpmconnCred.delete_project(ProjID)

print (tpmconnKey.who_am_i())
print (tpmconnKey.up_to_date())

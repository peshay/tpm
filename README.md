# tpm.py

A Python Module for the [TeamPasswordManager API](http://teampasswordmanager.com/docs/api/)

Requires: requests

## Install requests

You can install the requests library depending on your system either with

    sudo easy_install requests
or

    sudo pip install requests

## How to Use

This is an example how you can use it in a python script

    #! /usr/bin/env python
    import tpm
    # set a user and password to login
    USER = 'MyUser'
    PASS = 'Secret'
    # get a dictionary for all password entries
    data = tpm.getData('passwords', USER, PASS)
    # show all names from the password entries
    for item in data:
        print item.get('name')

## Functions explained
### getData(TYPE, USER, PASS, SEARCHSTRING='')

TYPE - Accepts 'passwords' or 'projects'.

USER and PASS - To Login with.

SEARCHSTRING - optional, will return only values that matchin the SEARCHSTRING.

### postData(TYPE, DATA, USER, PASS)

TYPE - Accepts 'passwords' or 'projects'.

DATA - Takes an dictionary, translate it to JSON and post it to the API, if fields are wrong, the API will complain.

USER and PASS - To Login with.


### deleteData(TYPE, ID, USER, PASS)

TYPE - Accepts 'passwords' or 'projects'.

ID - ID from the entry you want to delete.

USER and PASS - To Login with.


### putCustomFields(ID, DATA, USER, PASS)

ID - ID from the entry you want to delete.

DATA - A dictionary that defines the custom fields e.g.:

    customFieldsDefault = {'custom_label1': 'IP',
                           'custom_type1': 'text',
                           'custom_label2': 'CNAME',
                           'custom_type2': 'text',
                           'custom_label3': 'E-Mail',
                           'custom_type3': 'email'}

USER and PASS - To Login with.

### lockPassword(ID, USER, PASS)

ID - ID from the entry you want to lock.

USER and PASS - To Login with.


### unlockPassword(ID, USER, PASS)

ID - ID from the entry you want to unlock.

USER and PASS - To Login with.



## Examples

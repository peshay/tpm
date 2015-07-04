# tpm.py

A Python Module for the [TeamPasswordManager API](http://teampasswordmanager.com/docs/api/)

Requires: requests

## Install tpm.py

You can install the tpm module via pip

    pip install tpm

## How to Use

This is an example how you can use it in a python script

    #! /usr/bin/env python
    import tpm
    # set the address to your TeamPasswordManager
    tpm.TPMURL = "https://myPasswordManager.example.com"
    tpm.TPMAPI = "/index.php/api/v3/"
    # set a user and password to login
    tpm.USER = 'MyUser'
    tpm.PASS = 'Secret'
    
    # get a dictionary for all password entries
    data = tpm.getData('passwords')
    # show all names from the password entries
    for item in data:
        print item.get('name')

## Functions explained
##### getData(TYPE, SEARCHSTRING='')

TYPE - Accepts 'passwords' or 'projects'.

SEARCHSTRING - optional, will return only values that are matching the SEARCHSTRING.

##### postData(TYPE, DATA)

TYPE - Accepts 'passwords' or 'projects'.

DATA - Takes an dictionary, translate it to JSON and post it to the API, if fields are wrong, the API will complain.

##### deleteData(TYPE, ID)

TYPE - Accepts 'passwords' or 'projects'.

ID - ID from the entry you want to delete.

##### putCustomFields(ID, DATA)

ID - ID from the entry you want to delete.

DATA - A dictionary that defines the custom fields e.g.:

    DATA = {'custom_label1': 'IP',
            'custom_type1': 'text',
            'custom_label2': 'CNAME',
            'custom_type2': 'text',
            'custom_label3': 'E-Mail',
            'custom_type3': 'email'}

##### lockPassword(ID)

ID - ID from the entry you want to lock.

##### unlockPassword(ID)

ID - ID from the entry you want to unlock.

## Examples

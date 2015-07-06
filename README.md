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
```
## Functions explained
#### Functions that get data from TeamPasswordManager
##### getData(TYPE, SEARCHSTRING='')

*Connect to TPM and returns found Entries in a dictionary.*

**TYPE** - Accepts 'passwords' or 'projects'.

**SEARCHSTRING** - optional, will return only values that are matching the SEARCHSTRING.

##### getArchived(TYPE)

*Return all archived entries from 'passwords' or 'projects'*

**TYPE** - Accepts 'passwords' or 'projects'.

##### getFavorite(TYPE)

*Return all favorite entries from 'passwords' or 'projects'*

**TYPE** - Accepts 'passwords' or 'projects'.

##### getSecurity(TYPE, ID)

*List Users that have Access to a specific entry by ID.*

**TYPE** - Accepts 'passwords' or 'projects'.

**ID** - ID from the Entry you want to get the Users that have Access.

#### Functions that create data to TeamPasswordManager
##### postData(TYPE, DATA)

*Create a new entry in TeamPasswordManager.*

**TYPE** - Accepts 'passwords' or 'projects'.

**DATA** - Takes an dictionary, translate it to JSON and post it to the API, if fields are wrong, the API will complain.

#### Functions that update data to TeamPasswordManager
##### putData(TYPE, ID, DATA)

*Update an entry in TPM.*

**TYPE** - Accepts 'passwords' or 'projects'.

**ID** - ID from the Entry you want to update.

**DATA** - Takes an dictionary, translate it to JSON and post it to the API, if fields are wrong, the API will complain.

##### putSecurity(TYPE, ID, DATA)

*Update Security Access for an entry.*

**TYPE** - Accepts 'passwords' or 'projects'.

**ID** - ID from the Entry you want to update.

**DATA** - Takes an dictionary, translate it to JSON and post it to the API, if fields are wrong, the API will complain.

##### putCustomFields(ID, DATA)

*Update custom field labels for an entry.*

**ID** - ID from the entry you want to delete.

**DATA** - A dictionary that defines the custom fields e.g.:
```python
DATA = {'custom_label1': 'IP',
        'custom_type1': 'text',
        'custom_label2': 'CNAME',
        'custom_type2': 'text',
        'custom_label3': 'E-Mail',
        'custom_type3': 'email'}
```
##### lockPassword(ID)

**ID** - ID from the entry you want to lock.

##### unlockPassword(ID)

**ID** - ID from the entry you want to unlock.

**REASON** - The Reason why you want to unlock.

#### Functions that delete data from TeamPasswordManager
##### deleteData(TYPE, ID)

**TYPE** - Accepts 'passwords' or 'projects'.

**ID** - ID from the entry you want to delete.

## Examples

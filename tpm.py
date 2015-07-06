#! /usr/bin/env python
"""This is a common script for API connection with Team Password Manager.

see http://teampasswordmanager.com/docs/api/
for use, please install requests library: pip install requests
created by Andreas Hubert, censhare AG
"""

__version__ = '1.5'

import json
import requests
import sys


class bcolors:

    """Some colors."""

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# disable unsecure SSL warning
requests.packages.urllib3.disable_warnings()

# set TPM URL and API version
TPMURL = ""
TPMAPI = ""

# set login to TPM
USER = ""
PASS = ""

# set header as team password manager wants them
header = {'content-type': 'application/json; charset=utf-8'}

# create new empty data object to fill
global data


def HandleRequestsException(e):
    """Handle Exception from request."""
    print(bcolors.FAIL + e[0][0])
    print(e[0][1])
    print(bcolors.ENDC)
    sys.exit()


def HandleAPIErrors(r):
    """To handle Errors from TPM API."""
    # Handle API Errors
    if r.status_code != 200 and r.status_code != 201 and r.status_code != 204:
        content = json.load(r.raw)
        print(bcolors.FAIL + 'Error:    ' + str(r.status_code))
        print('Type:     ' + content['type'])
        print('Message:  ' + content['message'])
        print('With URL: ' + r.url + bcolors.ENDC)
        sys.exit()


def checkType(TYPE):
    """Test if given type is correct."""
    # check if a valid type was added
    if TYPE is not 'passwords' and TYPE is not 'projects':
        print(bcolors.WARNING + "connect type is neither " +
              "'passwords' nor 'projects'" + bcolors.ENDC)
        sys.exit()


def get(URL):
    """Return all results pagewise in a single dictionary."""
    data = []
    # get search results
    while URL:
        # try to connect and handle errors
        try:
            r = requests.get(URL, auth=(USER, PASS),
                             headers=(header), stream=True, verify=False)
            # Handle API Errors
            HandleAPIErrors(r)
            # check for rel next link
            if 'link' in r.headers:
                RELNEXT = r.links['next']
                URL = RELNEXT['url']
            else:
                URL = ''
        except requests.exceptions.RequestException as e:
            HandleRequestsException(e)
        # add data pagewise
        data.extend(json.load(r.raw))
    return data


def put(URL, DATA):
    """Update data in TPM."""
    # convert DATA to JSON
    JSON = json.dumps(DATA)
    # try to connect and handle errors
    try:
        r = requests.put(URL, data=JSON, auth=(USER, PASS),
                         headers=(header), stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)


def post(URL, DATA):
    """Post data to TPM."""
    # convert DATA to JSON
    JSON = json.dumps(DATA)
    # try to connect and handle errors
    try:
        r = requests.post(URL, data=JSON, auth=(USER, PASS),
                          headers=(header), stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)
    # return ID that has beend created
    return json.load(r.raw)


def getData(TYPE, SEARCHSTRING=''):
    """Connect to TPM and returns found Entries in a dictionary."""
    # check if type is password or projects
    checkType(TYPE)
    # Search or All
    if SEARCHSTRING:
        URL = TPMURL + TPMAPI + TYPE + "/search/" + SEARCHSTRING + ".json"
    else:
        URL = TPMURL + TPMAPI + TYPE + ".json"
    # return data dictionary
    return get(URL)


def getArchived(TYPE):
    """Connect to TPM and returns Data Object."""
    # check if type is password or projects
    checkType(TYPE)
    URL = TPMURL + TPMAPI + TYPE + "/archived.json"
    # return data dictionary
    return get(URL)


def getFavorite(TYPE):
    """Connect to TPM and returns Data Object."""
    # check if type is password or projects
    checkType(TYPE)
    # build URL
    URL = TPMURL + TPMAPI + TYPE + "/favorite.json"
    # return data dictionary
    return get(URL)


def getSecurity(TYPE, ID):
    """List Users that have Access to a specific entry by ID."""
    # check if type is password or projects
    checkType(TYPE)
    # build URL
    URL = TPMURL + TPMAPI + TYPE + '/' + ID + "/security.json"
    # return data dictionary
    return get(URL)


def putSecurity(TYPE, ID, DATA):
    """Update Security Access for an entry."""
    # check if type is password or projects
    checkType(TYPE)
    # build URL
    URL = TPMURL + TPMAPI + TYPE + "/" + ID + "/" + "/security.json"
    put(URL, DATA)


def putCustomFields(ID, DATA):
    """Update the Custom Fields in TPM."""
    # build URL
    URL = TPMURL + TPMAPI + "passwords" + "/" + ID + "/" + "custom_fields.json"
    put(URL, DATA)


def putData(TYPE, ID, DATA):
    """Update an entry in TPM."""
    # check if type is password or projects
    checkType(TYPE)
    # build URL
    URL = TPMURL + TPMAPI + TYPE + "/" + ID + ".json"
    # update to TPM
    put(URL, DATA)


def lockPassword(ID):
    """To Lock an entry."""
    # build URL
    URL = TPMURL + TPMAPI + "passwords" + "/" + str(ID) + "/" + "lock.json"
    # try to connect and handle errors
    try:
        r = requests.put(URL, auth=(USER, PASS),
                         headers=(header), stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)


def unlockPassword(ID, REASON):
    """To Unlock an entry."""
    # build URL
    URL = TPMURL + TPMAPI + "passwords" + "/" + str(ID) + "/" + "unlock.json"
    # add Unlock Reason to header
    header['X-Unlock-Reason'] = REASON
    # try to connect and handle errors
    try:
        r = requests.put(URL, auth=(USER, PASS),
                         headers=(header), stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)


def postData(TYPE, DATA):
    """Connect to TPM and create an entry."""
    # check if type is password or projects
    checkType(TYPE)
    # build URL
    URL = TPMURL + TPMAPI + TYPE + ".json"
    # create entry and return created ID
    return post(URL, DATA)


def deleteData(TYPE, ID):
    """Connect to TPM and delete an entry."""
    # check if type is password or projects
    checkType(TYPE)
    # create URL to delete entry
    URL = TPMURL + TPMAPI + TYPE + "/" + str(ID) + ".json"

    # try to connect and handle errors
    try:
        r = requests.delete(URL, auth=(USER, PASS), headers=(header),
                            stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)

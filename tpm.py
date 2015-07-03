#! /usr/bin/env python
"""This is a common script for API connection with Team Password Manager.

see http://teampasswordmanager.com/docs/api/
for use, please install requests library: sudo easy_install requests
created by Andreas Hubert, censhare AG
"""
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
data = []


def HandleRequestsException(e):
    """Handle Exception from request."""
    print bcolors.FAIL + e[0][0]
    print e[0][1]
    print bcolors.ENDC
    sys.exit()


def HandleAPIErrors(r):
    """To handle Errors from TPM API."""
    # Handle API Errors
    if r.status_code != 200 and r.status_code != 201 and r.status_code != 204:
        content = json.load(r.raw)
        print bcolors.FAIL + 'Error:    ' + str(r.status_code)
        print 'Type:     ' + content['type']
        print 'Message:  ' + content['message']
        print 'With URL: ' + r.url + bcolors.ENDC
        sys.exit()


def checkType(TYPE):
    """Test if given type is correct."""
    # check if a valid type was added
    if TYPE is not 'passwords' and TYPE is not 'projects':
        print bcolors.WARNING + "connect type is neither " + \
            "'passwords' nor 'projects'" + bcolors.ENDC
        sys.exit()


def getData(TYPE, SEARCHSTRING=''):
    """Connect to TPM and returns Data Object."""
    # check if type is password or projects
    checkType(TYPE)
    # Search or All
    if SEARCHSTRING:
        NEXTURL = TPMURL + TPMAPI + TYPE + "/search/" + SEARCHSTRING + ".json"
    else:
        NEXTURL = TPMURL + TPMAPI + TYPE + ".json"

    # get search results
    while NEXTURL:
        # try to connect and handle errors
        try:
            r = requests.get(NEXTURL, auth=(USER, PASS),
                             headers=(header), stream=True, verify=False)
            # Handle API Errors
            HandleAPIErrors(r)
            # check for rel next link
            if 'link' in r.headers:
                RELNEXT = r.links['next']
                NEXTURL = RELNEXT['url']
            else:
                NEXTURL = ''
        except requests.exceptions.RequestException as e:
            HandleRequestsException(e)
        # add data pagewise
        data.extend(json.load(r.raw))

    # return data object
    return data


def postData(TYPE, DATA):
    """Connect to TPM and post Data Object."""
    # check if type is password or projects
    checkType(TYPE)
    # build URL
    URL = TPMURL + TPMAPI + TYPE + ".json"
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


def putCustomFields(ID, DATA):
    """Update the Custom Fields in TPM."""
    # build URL
    URL = TPMURL + TPMAPI + "passwords" + "/" + ID + "/" + "custom_fields.json"
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


def unlockPassword(ID):
    """To Unlock an entry."""
    # build URL
    URL = TPMURL + TPMAPI + "passwords" + "/" + str(ID) + "/" + "unlock.json"
    # try to connect and handle errors
    try:
        r = requests.put(URL, auth=(USER, PASS),
                         headers=(header), stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)


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

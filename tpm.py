#! /usr/bin/env python
"""This is a common script for API connection with Team Password Manager.

see http://teampasswordmanager.com/docs/api/
for use, please install requests library: pip install requests
created by Andreas Hubert, censhare AG
"""

__version__ = '2.1'

import json
import requests
import sys
import re


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


class Connection:

    """Settings needed for the connection to Team Password Manager."""

    def __init__(self, api, url, user, password):
        """init thing."""
        AllowedAPI = ['v3', 'v4']
        REGEXurl = "^" \
                   "(?:(?:https?)://)" \
                   "(?:\\S+(?::\\S*)?@)?" \
                   "(?:" \
                   "(?:[1-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])" \
                   "(?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}" \
                   "(?:\\.(?:[1-9]\\d?|1\\d\\d|2[0-4]\\d|25[0-4]))" \
                   "|" \
                   "(?:(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)" \
                   "(?:\\.(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)*" \
                   "(?:\\.(?:[a-z\\u00a1-\\uffff]{2,}))?" \
                   ".?" \
                   ")" \
                   "(?::\\d{2,5})?" \
                   "(?:[/?#]\\S*)?" \
                   "$"
        if api in AllowedAPI:
            apiurl = '/index.php/api/' + api + '/'
        else:
            print(bcolors.FAIL + 'API Version not known: ' + api)
            print(bcolors.ENDC)
            sys.exit()
        self.api = apiurl
        if re.match(REGEXurl, url):
            self.url = url
        else:
            print(bcolors.FAIL + 'Invalid URL: ' + url)
            print(bcolors.ENDC)
            sys.exit()
        self.user = user
        self.password = password


# disable unsecure SSL warning
requests.packages.urllib3.disable_warnings()

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
    if TYPE is not 'passwords' \
       and TYPE is not 'projects' \
       and TYPE is not 'users' \
       and TYPE is not 'groups':
        print(bcolors.WARNING + "connect type is neither " +
              "'passwords', 'projects', 'users' or 'groups'" + bcolors.ENDC)
        sys.exit()


def checkTypeEntry(TYPE):
    """Test if given type is correct."""
    # check if a valid type was added
    if TYPE is not 'passwords' \
       and TYPE is not 'projects':
        print(bcolors.WARNING + "connect type is neither " +
              "'passwords' or 'projects'" + bcolors.ENDC)
        sys.exit()


def get(conn, URL):
    """Return all results pagewise in list of dictionaries."""
    data = []
    # get search results
    while URL:
        # try to connect and handle errors
        try:
            r = requests.get(URL, auth=(conn.user, conn.password),
                             headers=(header), stream=True, verify=False)
            # Handle API Errors
            HandleAPIErrors(r)
            # get results
            result = json.load(r.raw)
            # check for rel next link
            if 'link' in r.headers:
                RELNEXT = r.links['next']
                URL = RELNEXT['url']
            else:
                URL = ''
        except requests.exceptions.RequestException as e:
            HandleRequestsException(e)
        # add data pagewise
        data.extend(result)
    return data


def getSingle(conn, URL):
    """Return the single results in dictionary."""
    data = {}
    # get search results
    # try to connect and handle errors
    try:
        r = requests.get(URL, auth=(conn.user, conn.password),
                         headers=(header), stream=True, verify=False)
        # Handle API Errors
        HandleAPIErrors(r)
        # get results
        data.update(json.load(r.raw))
        # check for rel next link
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)
    return data


def generatePass(conn):
    """Generate a random password."""
    # build URL
    URL = conn.url + conn.api + "generate_password.json"
    # try to connect and handle errors
    try:
        r = requests.get(URL, auth=(conn.user, conn.password),
                         headers=(header), stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
        return json.load(r.raw).get('password')
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)


def put(conn, URL, DATA):
    """Update data in TPM."""
    # convert DATA to JSON
    JSON = json.dumps(DATA)
    # try to connect and handle errors
    try:
        r = requests.put(URL, data=JSON, auth=(conn.user, conn.password),
                         headers=(header), stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)


def post(conn, URL, DATA):
    """Post data to TPM."""
    # convert DATA to JSON
    JSON = json.dumps(DATA)
    # try to connect and handle errors
    try:
        r = requests.post(URL, data=JSON, auth=(conn.user, conn.password),
                          headers=(header), stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)
    # return ID that has beend created
    return json.load(r.raw)


def getData(conn, TYPE, SEARCHSTRING=''):
    """Connect to TPM and returns found Entries in a dictionary."""
    # check if type is password or projects
    checkType(TYPE)
    # Search or All
    if SEARCHSTRING:
        URL = conn.url + conn.api + TYPE + "/search/" + SEARCHSTRING + ".json"
    else:
        URL = conn.url + conn.api + TYPE + ".json"
    # return data dictionary
    return get(conn, URL)


def getSubProjects(conn, ID):
    """Get projcets that are subprojects of 'ID'."""
    if conn.api == '/index.php/api/v4/':
        URL = conn.url + conn.api + '/projects/' + str(ID) + \
            '/subprojects.json'
        # return data dictionary
        return get(conn, URL)
    else:
        print(bcolors.FAIL + 'This functions only works with v4 API.'
                           + bcolors.ENDC)
        sys.exit()


def getSubProjectsNewPwd(conn, ID):
    """Get projcets that are subprojects of 'ID' and shows disabled=true
    if the Users permissions does not allow to create a new Password in that
    subproject."""
    if conn.api == '/index.php/api/v4/':
        URL = conn.url + conn.api + '/projects/' + str(ID) + \
            '/subprojects/new_pwd.json'
        # return data dictionary
        return get(conn, URL)
    else:
        print(bcolors.FAIL + 'This functions only works with v4 API.'
                           + bcolors.ENDC)
        sys.exit()


def changeParent(conn, ID, ParentID):
    """Change the Parent Project of a Project."""
    if conn.api == '/index.php/api/v4/':
        URL = conn.url + conn.api + '/projects/' + str(ID) + \
            '/change_parent.json'
        DATA = {"parent_id": ParentID}
        # return data dictionary
        return put(conn, URL, DATA)
    else:
        print(bcolors.FAIL + 'This functions only works with v4 API.'
                           + bcolors.ENDC)
        sys.exit()


def getDetailData(conn, TYPE, ID):
    """Get more Details from an Entry."""
    # check if type is password or projects
    checkType(TYPE)
    URL = conn.url + conn.api + TYPE + "/" + str(ID) + ".json"
    # return data dictionary
    return getSingle(conn, URL)


def getProjectPasswords(conn, ID):
    """Get the password entries from a project."""
    # Build URL
    URL = conn.url + conn.api + 'projects/' + str(ID) + '/passwords.json'
    # return data dictionary
    return get(conn, URL)


def getProjectPasswordsCount(conn, ID):
    """Return the number of password entries from a project."""
    # Build URL
    URL = conn.url + conn.api + 'projects/' + str(ID) + '/passwords/count.json'
    # return data dictionary
    return getSingle(conn, URL)


def getArchived(conn, TYPE):
    """Connect to TPM and returns Data Object."""
    # check if type is password or projects
    checkTypeEntry(TYPE)
    URL = conn.url + conn.api + TYPE + "/archived.json"
    # return data dictionary
    return get(conn, URL)


def getFavorite(conn, TYPE):
    """Connect to TPM and returns Data Object."""
    # check if type is password or projects
    checkTypeEntry(TYPE)
    # build URL
    URL = conn.url + conn.api + TYPE + "/favorite.json"
    # return data dictionary
    return get(conn, URL)


def getSecurity(conn, TYPE, ID):
    """List Users that have Access to a specific entry by ID."""
    # check if type is password or projects
    checkTypeEntry(TYPE)
    # build URL
    URL = conn.url + conn.api + TYPE + '/' + ID + "/security.json"
    # return data dictionary
    return get(conn, URL)


def putSecurity(conn, TYPE, ID, DATA):
    """Update Security Access for an entry."""
    # check if type is password or projects
    checkTypeEntry(TYPE)
    # build URL
    URL = conn.url + conn.api + TYPE + "/" + ID + "/" + "/security.json"
    put(conn, URL, DATA)


def putCustomFields(conn, ID, DATA):
    """Update the Custom Fields in TPM."""
    # build URL
    URL = conn.url + conn.api + "passwords" + "/" + ID + "/" + \
                                                         "custom_fields.json"
    put(conn, URL, DATA)


def putData(conn, TYPE, ID, DATA):
    """Update an entry in TPM."""
    # check if type is password or projects
    checkType(TYPE)
    # build URL
    URL = conn.url + conn.api + TYPE + "/" + ID + ".json"
    # update to TPM
    put(conn, URL, DATA)


def lockPassword(conn, ID):
    """To Lock an entry."""
    # build URL
    URL = conn.url + conn.api + "passwords" + "/" + str(ID) + "/" + "lock.json"
    # try to connect and handle errors
    try:
        r = requests.put(URL, auth=(conn.user, conn.password),
                         headers=(header), stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)


def unlockPassword(conn, ID, REASON):
    """To Unlock an entry."""
    # build URL
    URL = conn.url + conn.api + "passwords" + "/" + str(ID) + "/" + \
                                                              "unlock.json"
    # add Unlock Reason to header
    header['X-Unlock-Reason'] = REASON
    # try to connect and handle errors
    try:
        r = requests.put(URL, auth=(conn.user, conn.password),
                         headers=(header), stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)


def postData(conn, TYPE, DATA):
    """Connect to TPM and create an entry."""
    # check if type is password or projects
    checkType(TYPE)
    # build URL
    URL = conn.url + conn.api + TYPE + ".json"
    # create entry and return created ID
    return post(conn, URL, DATA)


def deleteData(conn, TYPE, ID):
    """Connect to TPM and delete an entry."""
    # check if type is password or projects
    checkType(TYPE)
    # create URL to delete entry
    URL = conn.url + conn.api + TYPE + "/" + str(ID) + ".json"

    # try to connect and handle errors
    try:
        r = requests.delete(URL, auth=(conn.user, conn.password),
                            headers=(header), stream=True, verify=False)
        # Handle request Errors
        HandleAPIErrors(r)
    except requests.exceptions.RequestException as e:
        HandleRequestsException(e)

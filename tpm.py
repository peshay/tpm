#! /usr/bin/env python
"""Team Password Manager API

To simplify usage of Team Password Manager API.

You can authenticate with username and password
    >>> import tpm
    >>> URL = "https://mypasswordmanager.example.com"
    >>> USER = 'MyUser'
    >>> PASS = 'Secret'
    >>> tpmconn = tpm.TpmApiv5(URL, username=USER, password=PASS)

Or with Private/Public Key
    >>> pubkey = '3726d93f2a0e5f0fe2cc3a6e9e3ade964b43b07f897d579466c28b7f8ff51cd0'
    >>> privkey = '87324bedead51af96a45271d217b8ad5ef3f220da6c078a9bce4e4318729189c'
    >>> tpmconn = tpm.TpmApiv5(URL, private_key=privkey, public_key=pubkey)

With the connection object you can use all TPM functions, like list all passwords:
    >>> tpmconn.list_passwords()

All API functions from Team Password Manager are included.
see http://teampasswordmanager.com/docs/api/

:copyright: (c) 2022 by Andreas Hubert.
:license: The MIT License (MIT), see LICENSE for more details.
"""

__version__ = '4.2'

import hmac
import hashlib
import time
import requests
import re
import json
import logging
import base64
import os.path

from urllib.parse import quote_plus

# set logger
log = logging.getLogger(__name__)
# disable unsecure SSL warning
requests.packages.urllib3.disable_warnings()


class TPMException(Exception):
    pass


class TpmApi(object):
    """Settings needed for the connection to Team Password Manager."""
    class ConfigError(Exception):
        """To throw Exception based on wrong Settings."""
        def __init__(self, value):
            self.value = value
            log.critical(value)

        def __str__(self):
            return repr(self.value)

    def __init__(self, api, base_url, kwargs):
        """init thing."""
        # Check if API version is not bullshit
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
        self.apiurl = 'api/' + api + '/'
        log.debug('Set as apiurl: {}'.format(self.apiurl))
        self.api = self.apiurl
        # Check if URL is not bullshit
        if re.match(REGEXurl, base_url):
            self.base_url = base_url + '/index.php/'
            log.debug('Set Base URL to {}'.format(self.base_url))
            self.url = self.base_url + self.apiurl
            log.debug('Set URL to {}'.format(self.url))
        else:
            raise self.ConfigError('Invalid URL: {}'.format(base_url))
        # set headers
        self.headers = {'Content-Type': 'application/json; charset=utf-8',
                        'User-Agent': 'tpm.py/' + __version__
                        }
        log.debug('Set header to {}'.format(self.headers))
        # check kwargs for either keys or user credentials
        self.private_key = False
        self.public_key = False
        self.username = False
        self.password = False
        self.unlock_reason = False
        for key in kwargs:
            if key == 'private_key':
                self.private_key = kwargs[key]
            elif key == 'public_key':
                self.public_key = kwargs[key]
            elif key == 'username':
                self.username = kwargs[key]
            elif key == 'password':
                self.password = kwargs[key]
            elif key == 'unlock_reason':
                self.unlock_reason = kwargs[key]
        if self.private_key is not False and self.public_key is not False and\
                self.username is False and self.password is False:
            log.debug('Using Private/Public Key authentication.')
        elif self.username is not False and self.password is not False and\
                self.private_key is False and self.public_key is False:
            log.debug('Using Basic authentication.')
        else:
            raise self.ConfigError('No authentication specified'
                                   ' (user/password or private/public key)')


    def request(self, path, action, data=''):
        """To make a request to the API."""
        # Check if the path includes URL or not.
        head = self.base_url
        if path.startswith(head):
            path = path[len(head):]
            path = quote_plus(path, safe='/')
        if not path.startswith(self.api):
            path = self.api + path
        log.debug('Using path {}'.format(path))

        # If we have data, convert to JSON
        if data:
            data = json.dumps(data)
            log.debug('Data to sent: {}'.format(data))
        # In case of key authentication
        if self.private_key and self.public_key:
            timestamp = str(int(time.time()))
            log.debug('Using timestamp: {}'.format(timestamp))
            unhashed = path + timestamp + str(data)
            log.debug('Using message: {}'.format(unhashed))
            self.hash = hmac.new(str.encode(self.private_key),
                                 msg=unhashed.encode('utf-8'),
                                 digestmod=hashlib.sha256).hexdigest()
            log.debug('Authenticating with hash: {}'.format(self.hash))
            self.headers['X-Public-Key'] = self.public_key
            self.headers['X-Request-Hash'] = self.hash
            self.headers['X-Request-Timestamp'] = timestamp
            auth = False
        # In case of user credentials authentication
        elif self.username and self.password:
            auth = requests.auth.HTTPBasicAuth(self.username, self.password)
        # Set unlock reason
        if self.unlock_reason:
            self.headers['X-Unlock-Reason'] = self.unlock_reason
            log.info('Unlock Reason: {}'.format(self.unlock_reason))
        url = head + path
        # Try API request and handle Exceptions
        try:
            if action == 'get':
                log.debug('GET request {}'.format(url))
                self.req = requests.get(url, headers=self.headers, auth=auth,
                                        verify=False)
            elif action == 'post':
                log.debug('POST request {}'.format(url))
                self.req = requests.post(url, headers=self.headers, auth=auth,
                                         verify=False, data=data)
            elif action == 'put':
                log.debug('PUT request {}'.format(url))
                self.req = requests.put(url, headers=self.headers,
                                        auth=auth, verify=False,
                                        data=data)
            elif action == 'delete':
                log.debug('DELETE request {}'.format(url))
                self.req = requests.delete(url, headers=self.headers,
                                           verify=False, auth=auth)

            if self.req.content == b'':
                result = None
                log.debug('No result returned.')
            else:
                result = self.req.json()
                if 'error' in result and result['error']:
                    raise TPMException(result['message'])

        except requests.exceptions.RequestException as e:
            log.critical("Connection error for " + str(e))
            raise TPMException("Connection error for " + str(e))

        except ValueError as e:
            if self.req.status_code == 403:
                log.warning(url + " forbidden")
                raise TPMException(url + " forbidden")
            elif self.req.status_code == 404:
                log.warning(url + " forbidden")
                raise TPMException(url + " not found")
            else:
                message = ('{}: {} {}'.format(e, self.req.url, self.req.text))
                log.debug(message)
                raise ValueError(message)

        return result

    def post(self, path, data=''):
        """For post based requests."""
        return self.request(path, 'post', data)

    def get(self, path):
        """For get based requests."""
        return self.request(path, 'get')

    def put(self, path, data=''):
        """For put based requests."""
        return self.request(path, 'put', data)

    def delete(self, path):
        """For delete based requests."""
        self.request(path, 'delete')

    def get_collection(self, path):
        """To get pagewise data."""
        while True:
            items = self.get(path)
            req = self.req
            for item in items:
                yield item
            if req.links and req.links['next'] and\
                    req.links['next']['rel'] == 'next':
                path = req.links['next']['url']
            else:
                break

    def collection(self, path):
        """To return all items generated by get collection."""
        data = []
        for item in self.get_collection(path):
            data.append(item)
        return data

    # From now on, Functions that work that way in all API Versions.

    # http://teampasswordmanager.com/docs/api-projects/#list_projects
    def list_projects(self):
        """List projects."""
        log.debug('List all projects.')
        return self.collection('projects.json')

    def list_projects_archived(self):
        """List archived projects."""
        log.debug('List all archived projects.')
        return self.collection('projects/archived.json')

    def list_projects_favorite(self):
        """List favorite projects."""
        log.debug('List all favorite projects.')
        return self.collection('projects/favorite.json')

    def list_projects_search(self, searchstring):
        """List projects with searchstring."""
        log.debug('List all projects with: {}'.format(searchstring))
        return self.collection('projects/search/{}.json'.format(quote_plus(searchstring)))

    def show_project(self, ID):
        """Show a project."""
        # http://teampasswordmanager.com/docs/api-projects/#show_project
        log.debug('Show project info: {}'.format(ID))
        return self.get('projects/{}.json'.format(ID))

    def list_passwords_of_project(self, ID):
        """List passwords of project."""
        # http://teampasswordmanager.com/docs/api-projects/#list_pwds_prj
        log.debug('List passwords of project: {}'.format(ID))
        return self.collection('projects/{}/passwords.json'.format(ID))

    def list_user_access_on_project(self, ID):
        """List users who can access a project."""
        # http://teampasswordmanager.com/docs/api-projects/#list_users_prj
        log.debug('List User access on project: {}'.format(ID))
        return self.collection('projects/{}/security.json'.format(ID))

    def create_project(self, data):
        """Create a project."""
        # http://teampasswordmanager.com/docs/api-projects/#create_project
        log.info('Create project: {}'.format(data))
        NewID = self.post('projects.json', data).get('id')
        log.info('Project has been created with ID {}'.format(NewID))
        return NewID

    def update_project(self, ID, data):
        """Update a project."""
        # http://teampasswordmanager.com/docs/api-projects/#update_project
        log.info('Update project {} with {}'.format(ID, data))
        self.put('projects/{}.json'.format(ID), data)

    def change_parent_of_project(self, ID, NewParentID):
        """Change parent of project."""
        # http://teampasswordmanager.com/docs/api-projects/#change_parent
        log.info('Change parrent for project {} to {}'.format(ID, NewParentID))
        data = {'parent_id': NewParentID}
        self.put('projects/{}/change_parent.json'.format(ID), data)

    def update_security_of_project(self, ID, data):
        """Update security of project."""
        # http://teampasswordmanager.com/docs/api-projects/#update_project_security
        log.info('Update project {} security {}'.format(ID, data))
        self.put('projects/{}/security.json'.format(ID), data)

    def archive_project(self, ID):
        """Archive a project."""
        # http://teampasswordmanager.com/docs/api-projects/#arch_unarch_project
        log.info('Archive project {}'.format(ID))
        self.put('projects/{}/archive.json'.format(ID))

    def unarchive_project(self, ID):
        """Un-Archive a project."""
        # http://teampasswordmanager.com/docs/api-projects/#arch_unarch_project
        log.info('Unarchive project {}'.format(ID))
        self.put('projects/{}/unarchive.json'.format(ID))

    def delete_project(self, ID):
        """Delete a project."""
        # http://teampasswordmanager.com/docs/api-projects/#delete_project
        log.info('Delete project {}'.format(ID))
        self.delete('projects/{}.json'.format(ID))

    # http://teampasswordmanager.com/docs/api-passwords/#list_passwords
    def list_passwords(self):
        """List passwords."""
        log.debug('List all passwords.')
        return self.collection('passwords.json')

    def list_passwords_archived(self):
        """List archived passwords."""
        log.debug('List archived passwords.')
        return self.collection('passwords/archived.json')

    def list_passwords_favorite(self):
        """List favorite passwords."""
        log.debug('List favorite spasswords.')
        return self.collection('passwords/favorite.json')

    def list_passwords_search(self, searchstring):
        """List passwords with searchstring."""
        log.debug('List all passwords with: {}'.format(searchstring))
        return self.collection('passwords/search/{}.json'.format(quote_plus(searchstring)))

    def show_password(self, ID):
        """Show password."""
        # http://teampasswordmanager.com/docs/api-passwords/#show_password
        log.info('Show password info: {}'.format(ID))
        return self.get('passwords/{}.json'.format(ID))

    def list_user_access_on_password(self, ID):
        """List users who can access a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#list_users_pwd
        log.debug('List user access on password {}'.format(ID))
        return self.collection('passwords/{}/security.json'.format(ID))

    def create_password(self, data):
        """Create a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#create_password
        log.info('Create new password {}'.format(data))
        NewID = self.post('passwords.json', data).get('id')
        log.info('Password has been created with ID {}'.format(NewID))
        return NewID

    def update_password(self, ID, data):
        """Update a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#update_password
        log.info('Update Password {} with {}'.format(ID, data))
        self.put('passwords/{}.json'.format(ID), data)

    def update_security_of_password(self, ID, data):
        """Update security of a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#update_security_password
        log.info('Update security of password {} with {}'.format(ID, data))
        self.put('passwords/{}/security.json'.format(ID), data)

    def update_custom_fields_of_password(self, ID, data):
        """Update custom fields definitions of a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#update_cf_password
        log.info('Update custom fields of password {} with {}'.format(ID, data))
        self.put('passwords/{}/custom_fields.json'.format(ID), data)

    def delete_password(self, ID):
        """Delete a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#delete_password
        log.info('Delete password {}'.format(ID))
        self.delete('passwords/{}.json'.format(ID))

    def lock_password(self, ID):
        """Lock a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#lock_password
        log.info('Lock password {}'.format(ID))
        self.put('passwords/{}/lock.json'.format(ID))

    def unlock_password(self, ID, reason):
        """Unlock a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#unlock_password
        log.info('Unlock password {}, Reason: {}'.format(ID, reason))
        self.unlock_reason = reason
        self.put('passwords/{}/unlock.json'.format(ID))

    def list_mypasswords(self):
        """List my passwords."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#list_passwords
        log.debug('List MyPasswords')
        return self.collection('my_passwords.json')

    def list_mypasswords_search(self, searchstring):
        """List my passwords with searchstring."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#list_passwords
        log.debug('List MyPasswords with {}'.format(searchstring))
        return self.collection('my_passwords/search/{}.json'.format(quote_plus(searchstring)))

    def show_mypassword(self, ID):
        """Show my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#show_password
        log.debug('Show MyPassword {}'.format(ID))
        return self.get('my_passwords/{}.json'.format(ID))

    def create_mypassword(self, data):
        """Create my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#create_password
        log.info('Create MyPassword with {}'.format(data))
        NewID = self.post('my_passwords.json', data).get('id')
        log.info('MyPassword has been created with {}'.format(NewID))
        return NewID

    def update_mypassword(self, ID, data):
        """Update my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#update_password
        log.info('Update MyPassword {} with {}'.format(ID, data))
        self.put('my_passwords/{}.json'.format(ID), data)

    def delete_mypassword(self, ID):
        """Delete my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#delete_password
        log.info('Delete password {}'.format(ID))
        self.delete('my_passwords/{}.json'.format(ID))

    def set_favorite_password(self, ID):
        """Set a password as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#set_fav
        log.info('Set password {} as favorite'.format(ID))
        self.post('favorite_passwords/{}.json'.format(ID))

    def unset_favorite_password(self, ID):
        """Unet a password as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#del_fav
        log.info('Unset password {} as favorite'.format(ID))
        self.delete('favorite_passwords/{}.json'.format(ID))

    def set_favorite_project(self, ID):
        """Set a project as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#set_fav
        log.info('Set project {} as favorite'.format(ID))
        self.post('favorite_project/{}.json'.format(ID))

    def unset_favorite_project(self, ID):
        """Unet a project as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#del_fav
        log.info('Unset project {} as favorite'.format(ID))
        self.delete('favorite_project/{}.json'.format(ID))

    def list_users(self):
        """List users."""
        # http://teampasswordmanager.com/docs/api-users/#list_users
        log.debug('List users')
        return self.collection('users.json')

    def show_user(self, ID):
        """Show a user."""
        # http://teampasswordmanager.com/docs/api-users/#show_user
        log.debug('Show user {}'.format(ID))
        return self.get('users/{}.json'.format(ID))

    def show_me(self):
        """Show me."""
        # http://teampasswordmanager.com/docs/api-users/#show_me
        log.debug('Show Info about own user')
        return self.get('users/me.json')

    def who_am_i(self):
        """Who am I."""
        return self.show_me()

    def create_user(self, data):
        """Create a User."""
        # http://teampasswordmanager.com/docs/api-users/#create_user
        log.info('Create user with {}'.format(data))
        NewID = self.post('users.json', data).get('id')
        log.info('User has been created with ID {}'.format(NewID))
        return NewID

    def update_user(self, ID, data):
        """Update a User."""
        # http://teampasswordmanager.com/docs/api-users/#update_user
        log.info('Update user {} with {}'.format(ID, data))
        self.put('users/{}.json'.format(ID), data)

    def change_user_password(self, ID, data):
        """Change password of a User."""
        # http://teampasswordmanager.com/docs/api-users/#change_password
        log.info('Change user {} password'.format(ID))
        self.put('users/{}/change_password.json'.format(ID), data)

    def activate_user(self, ID):
        """Activate a User."""
        # http://teampasswordmanager.com/docs/api-users/#activate_deactivate
        log.info('Activate user {}'.format(ID))
        self.put('users/{}/activate.json'.format(ID))

    def deactivate_user(self, ID):
        """Dectivate a User."""
        # http://teampasswordmanager.com/docs/api-users/#activate_deactivate
        log.info('Deactivate user {}'.format(ID))
        self.put('users/{}/deactivate.json'.format(ID))

    def convert_user_to_ldap(self, ID, DN):
        """Convert a normal user to a LDAP user."""
        # http://teampasswordmanager.com/docs/api-users/#convert_to_ldap
        data = {'login_dn': DN}
        log.info('Convert User {} to LDAP DN {}'.format(ID, DN))
        self.put('users/{}/convert_to_ldap.json'.format(ID), data)

    def convert_ldap_user_to_normal(self, ID):
        """Convert a LDAP user to a normal user."""
        log.info('Convert User {} from LDAP to normal user'.format(ID))
        self.put('users/{}/convert_to_normal.json'.format(ID))

    def delete_user(self, ID):
        """Delete a user."""
        # http://teampasswordmanager.com/docs/api-users/#delete_user
        log.info('Delete user {}'.format(ID))
        self.delete('users/{}.json'.format(ID))

    def list_groups(self):
        """List Groups."""
        # http://teampasswordmanager.com/docs/api-groups/#list_groups
        log.debug('List groups')
        return self.collection('groups.json')

    def show_group(self, ID):
        """Show a Group."""
        # http://teampasswordmanager.com/docs/api-groups/#show_group
        log.debug('Show group {}'.format(ID))
        return self.get('groups/{}.json'.format(ID))

    def create_group(self, data):
        """Create a Group."""
        # http://teampasswordmanager.com/docs/api-groups/#create_group
        log.info('Create group with {}'.format(data))
        NewID = self.post('groups.json', data).get('id')
        log.info('Group has been created with ID {}'.format(NewID))
        return NewID

    def update_group(self, ID, data):
        """Update a Group."""
        # http://teampasswordmanager.com/docs/api-groups/#update_group
        log.info('Update group {} with {}'.format(ID, data))
        self.put('groups/{}.json'.format(ID), data)

    def add_user_to_group(self, GroupID, UserID):
        """Add a user to a group."""
        # http://teampasswordmanager.com/docs/api-groups/#add_user
        log.info('Add User {} to Group {}'.format(UserID, GroupID))
        self.put('groups/{}/add_user/{}.json'.format(GroupID, UserID))

    def delete_user_from_group(self, GroupID, UserID):
        """Delete a user from a group."""
        # http://teampasswordmanager.com/docs/api-groups/#del_user
        log.info('Delete user {} from group {}'.format(UserID, GroupID))
        self.put('groups/{}/delete_user/{}.json'.format(GroupID, UserID))

    def delete_group(self, ID):
        """Delete a group."""
        # http://teampasswordmanager.com/docs/api-groups/#delete_group
        log.info('Delete group {}'.format(ID))
        self.delete('groups/{}.json'.format(ID))

    def generate_password(self):
        """Generate a new random password."""
        # http://teampasswordmanager.com/docs/api-passwords-generator/
        log.debug('Generate new password')
        return self.get('generate_password.json')

    def get_version(self):
        """Get Version Information."""
        # http://teampasswordmanager.com/docs/api-version/
        log.debug('Get version information')
        return self.get('version.json')

    def get_latest_version(self):
        """Check for latest version."""
        # http://teampasswordmanager.com/docs/api-version/
        log.debug('Get latest version')
        return self.get('version/check_latest.json')

    def up_to_date(self):
        """Check if Team Password Manager is up to date."""
        VersionInfo = self.get_latest_version()
        CurrentVersion = VersionInfo.get('version')
        LatestVersion = VersionInfo.get('latest_version')
        if  CurrentVersion == LatestVersion:
            log.info('TeamPasswordManager is up-to-date!')
            log.debug('Current Version: {} Latest Version: {}'.format(LatestVersion, LatestVersion))
            return True
        else:
            log.warning('TeamPasswordManager is not up-to-date!')
            log.debug('Current Version: {} Latest Version: {}'.format(LatestVersion, LatestVersion))
            return False


class TpmApiv3(TpmApi):
    """API v3 based class."""
    def __init__(self, url, **kwargs):
        super(TpmApiv3, self).__init__('v3', url, kwargs)
    """From now on, Functions that only work with API v3."""


class TpmApiv4(TpmApi):
    """API v4 based class."""
    def __init__(self, url, **kwargs):
        super(TpmApiv4, self).__init__('v4', url, kwargs)
    """From now on, Functions that only work with API v4."""

    def list_subprojects(self, ID):
        """List subprojects."""
        # http://teampasswordmanager.com/docs/api-projects/#list_subprojects
        log.debug('List subprojects of {}'.format(ID))
        return self.collection('projects/{}/subprojects.json'.format(ID))

    def list_subprojects_action(self, ID, action):
        """List subprojects with allowed action."""
        log.debug('List subprojects of {} with action: {}'.format(ID, action))
        return self.collection('projects/{}/subprojects/{}.json'.format(ID, action))

class TpmApiv5(TpmApiv4):
    """API v5 based class."""
    def __init__(self, url, **kwargs):
        super(TpmApiv4, self).__init__('v5', url, kwargs)
    """From now on, Functions that only work with API v5."""

    def list_project_files(self, ID):
        """List files of a project."""
        return self.collection('projects/{}/files.json'.format(ID))

    def upload_project_file(self, ID, file, **kwargs):
        """Upload a file to a project."""
        if os.path.isfile(file):
            file_data = open(file, "rb")
            encoded = base64.b64encode(file_data.read())
            data = { "file_data_base64": encoded.decode('ascii'),
                     "file_name": os.path.basename(file)
            }
            if 'notes' in kwargs:
                data['notes'] = kwargs['notes']
            NewID = self.post('projects/{}/upload.json'.format(ID), data).get('id')
            log.info('File has been uploaded with ID {}'.format(NewID))
            return NewID
        else:
            raise Exception("File not found: {}".format(file))

    def archive_password(self, ID):
        """Archive a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#arch_unarch_password
        log.info('Archive password {}'.format(ID))
        self.put('passwords/{}/archive.json'.format(ID))

    def unarchive_password(self, ID):
        """Un-Archive a project."""
        # http://teampasswordmanager.com/docs/api-passwords/#arch_unarch_password
        log.info('Unarchive password {}'.format(ID))
        self.put('passwords/{}/unarchive.json'.format(ID))

    def move_password(self, ID, PROJECT_ID):
        """Move a password to another project."""
        # http://teampasswordmanager.com/docs/api-passwords/#move_password
        log.info('Move password {} to Project {}'.format(ID, PROJECT_ID))
        self.put('passwords/{}/move.json'.format(ID), data={ "project_id": PROJECT_ID })

    def list_password_files(self, ID):
        """List files of a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#list_files
        log.info('List files of password: {}'.format(ID))
        return self.collection('passwords/{}/files.json'.format(ID))

    def upload_password_file(self, ID, file, **kwargs):
        """Upload a file to a password."""
        if os.path.isfile(file):
            file_data = open(file, "rb")
            encoded = base64.b64encode(file_data.read())
            data = { "file_data_base64": encoded.decode('ascii'),
                     "file_name": os.path.basename(file)
            }
            if 'notes' in kwargs:
                data['notes'] = kwargs['notes']
            NewID = self.post('passwords/{}/upload.json'.format(ID), data).get('id')
            log.info('File has been uploaded with ID {}'.format(NewID))
            return NewID
        else:
            raise Exception("File not found: {}".format(file))

    def move_mypassword(self, ID, PROJECT_ID):
        """Move a mypassword to another project."""
        # https://teampasswordmanager.com/docs/api-my-passwords/#move_password
        log.info('Move my_password {} to Project {}'.format(ID, PROJECT_ID))
        return self.put('my_passwords/{}/move.json'.format(ID), data={ "project_id": PROJECT_ID }).get('id')

    def show_file_info(self, ID):
        """Show info of a file."""
        # https://teampasswordmanager.com/docs/api-files/#show_file
        log.info('Show info of file with ID: {}'.format(ID))
        return self.get('files/{}.json'.format(ID))

    def update_file_notes(self, ID, NOTES):
        """Update the notes on a file."""
        # https://teampasswordmanager.com/docs/api-files/#update_file
        log.info('Update notes on file {} to: {}'.format(ID, NOTES))
        self.put('files/{}.json'.format(ID), data={ "notes": NOTES })

    def max_upload_file_size(self):
        """Show max upload file size."""
        # https://teampasswordmanager.com/docs/api-files/#max_upload_file_size
        log.info('Show max_upload_file_size')
        return self.get('files/max_upload_file_size.json')

    def uploads_folder_info(self):
        """Show uploads folder info."""
        # https://teampasswordmanager.com/docs/api-files/#uploads_folder
        log.info('Show uploads_folder_info')
        return self.get('files/uploads_folder_info.json')

    def download_file(self, ID):
        """Get the content of a file."""
        # https://teampasswordmanager.com/docs/api-files/#download_file
        log.info('Download file with ID: {}'.format(ID))
        return self.get('files/download/{}.json'.format(ID))

    def delete_file(self, ID):
        """Delete a file."""
        # https://teampasswordmanager.com/docs/api-files/#delete_file
        log.info('Delete file {}'.format(ID))
        self.delete('files/{}.json'.format(ID))

    def create_user_ldap(self, data):
        """Create a LDAP User."""
        # http://teampasswordmanager.com/docs/api-users/#create_user_ldap
        log.info('Create LDAP user with {}'.format(data))
        NewID = self.post('users_ldap.json', data).get('id')
        log.info('LDAP User has been created with ID {}'.format(NewID))
        return NewID

    def create_user_saml(self, data):
        """Create a SAML User."""
        # http://teampasswordmanager.com/docs/api-users/#create_user_saml
        log.info('Create SAML user with {}'.format(data))
        NewID = self.post('users_saml.json', data).get('id')
        log.info('SAML User has been created with ID {}'.format(NewID))
        return NewID

    def convert_user_to_ldap(self, ID, DN, SERVER_ID):
        """Convert a normal user to a LDAP user."""
        # http://teampasswordmanager.com/docs/api-users/#convert_to_ldap
        data = {'login_dn': DN, "ldap_server_id": SERVER_ID}
        log.info('Convert User {} to LDAP DN {} at Server {}'.format(ID, DN, SERVER_ID))
        self.put('users/{}/convert_to_ldap.json'.format(ID), data)

    def convert_user_to_saml(self, ID):
        """Convert a normal user to a SAML user."""
        # http://teampasswordmanager.com/docs/api-users/#convert_to_saml
        log.info('Convert User {} to SAML'.format(ID))
        self.put('users/{}/convert_to_saml.json'.format(ID))

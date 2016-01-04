#! /usr/bin/env python
"""This is a common script for API connection with Team Password Manager.

see http://teampasswordmanager.com/docs/api/
for use, please install requests library: pip install requests
created by Andreas Hubert, censhare AG
"""

__version__ = '3.0'

import hmac
import hashlib
import time
import requests
import re
import json
import logging

log = logging.getLogger(__name__)


class TPMException(Exception):
    log.warning('Error in communicating with API.')


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
            self.apiurl = '/index.php/api/' + api + '/'
        else:
            raise ConfigError('API Version not known: %s' % api)
        self.api = self.apiurl
        # Check if URL is not bullshit
        if re.match(REGEXurl, base_url):
            self.url = base_url + self.apiurl
            self.base_url = base_url
        else:
            raise ConfigError('Invalid URL: %s' % url)
        # set headers
        self.headers = {'Content-Type': 'application/json; charset=utf-8',
                        'User-Agent': 'tpm.py/' + __version__
                        }
        # check kwargs for either keys or user credentials
        auth1 = False
        auth2 = False
        self.private_key = False
        self.public_key = False
        self.username = False
        self.password = False
        self.unlock_reason = False
        for key in kwargs:
            if key == 'private_key':
                self.private_key = kwargs[key]
                auth1 = True
            elif key == 'public_key':
                self.public_key = kwargs[key]
                auth2 = True
            elif key == 'username':
                self.username = kwargs[key]
                auth1 = True
            elif key == 'password':
                self.password = kwargs[key]
                auth2 = True
        if auth1 is False or auth2 is False:
            raise ConfigError('No authentication specified'
                              ' (user/password or private/public key)')

    def request(self, path, action, data=''):
        """To make a request to the API."""
        # Check if the path includes URL or not.
        head = self.base_url
        if path.startswith(head):
            path = path[len(head):]
        if not path.startswith(self.api):
            path = self.api + path
        # If we have data, convert to JSON
        if data:
            data = json.dumps(data)
        # In case of key authentication
        if self.private_key and self.public_key:
            timestamp = str(int(time.time()))
            unhashed = path + timestamp + data
            hash = hmac.new(str.encode(self.private_key),
                            msg=unhashed.encode('utf-8'),
                            digestmod=hashlib.sha256).hexdigest()
            self.headers['X-Public-Key'] = self.public_key
            self.headers['X-Request-Hash'] = hash
            self.headers['X-Request-Timestamp'] = timestamp
        # In case of user credentials authentication
        elif self.username and self.password:
            auth = requests.auth.HTTPBasicAuth(self.username, self.password)
        # Set unlock reason
        if self.unlock_reason:
            self.headers['X-Unlock-Reason'] = self.unlock_reason

        url = head + path
        # Try API request and handle Exceptions
        try:
            if action == 'get':
                self.req = requests.get(url, headers=self.headers, auth=auth,
                                        verify=False)
            elif action == 'post':
                self.req = requests.post(url, headers=self.headers, auth=auth,
                                         verify=False, data=data)
            elif action == 'put':
                self.req = requests.put(url, headers=self.headers, auth=auth,
                                        verify=False, data=data)
            elif action == 'delete':
                self.req = requests.delete(url, headers=self.headers,
                                           verify=False, auth=auth)

            result = self.req.json()
            if 'error' in result and result['error']:
                raise TPMException(result['message'])

        except requests.exceptions.RequestException as e:
            raise TPMException("Connection error for " + str(e))

        except ValueError as e:
            if self.req.status_code == 403:
                raise TPMException(url + " forbidden")
            elif self.req.status_code == 404:
                raise TPMException(url + " not found")
            else:
                raise TPMException(self.req.text)

        return result

    def post(self, path, data):
        """For post based requests."""
        return self.request(path, 'post', data)

    def get(self, path):
        """For get based requests."""
        return self.request(path, 'get')

    def put(self, path, data):
        """For put based requests."""
        return self.request(path, 'put', data)

    def delete(self, path):
        """For delete based requests."""
        return self.request(path, 'delete')

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
        return collection('projects.json')

    def list_projects_archived(self):
        """List archived projects."""
        return collection('projects/archived.json')

    def list_projects_favorite(self):
        """List favorite projects."""
        return collection('projects/favorite.json')

    def list_projects_search(self, searchstring):
        """List projects with searchstring."""
        return collection('projects/search/%s.json' % searchstring)

    def show_project(self, ID):
        """Show a project."""
        # http://teampasswordmanager.com/docs/api-projects/#show_project
        return get('projects/%s.json' % ID)

    def list_passwords_of_project(self, ID):
        """List passwords of project."""
        # http://teampasswordmanager.com/docs/api-projects/#list_pwds_prj
        return collection('projects/%s/passwords.json' % ID)

    def list_user_access_on_project(self, ID):
        """List users who can access a project."""
        # http://teampasswordmanager.com/docs/api-projects/#list_users_prj
        return collection('projects/%s/security.json' % ID)

    def create_project(self, data):
        """Create a project."""
        # http://teampasswordmanager.com/docs/api-projects/#create_project
        return post('projects.json', data)

    def update_project(self, ID, data):
        """Update a project."""
        # http://teampasswordmanager.com/docs/api-projects/#update_project
        put('projects/%s.json' % ID, data)

    def change_parent_of_project(self, ID, NewParrentID):
        """Change parent of project."""
        # http://teampasswordmanager.com/docs/api-projects/#change_parent
        data = {'parent_id': NewParrentID}
        put('projects/%s/change_parent.json' % ID, data)

    def update_security_of_project(self, ID, data):
        """Update security of project."""
        # http://teampasswordmanager.com/docs/api-projects/#update_project_security
        put('projects/%s/security.json' % ID, data)

    def archive_project(self, ID):
        """Archive a project."""
        # http://teampasswordmanager.com/docs/api-projects/#arch_unarch_project
        put('projects/%s/archive.json' % ID)

    def unarchive_project(self, ID):
        """Un-Archive a project."""
        # http://teampasswordmanager.com/docs/api-projects/#arch_unarch_project
        put('projects/%s/unarchive.json' % ID)

    def delete_project(self, ID):
        """Delete a project."""
        # http://teampasswordmanager.com/docs/api-projects/#delete_project
        delete('projects/%s.json' % ID)

    # http://teampasswordmanager.com/docs/api-passwords/#list_passwords
    def list_passwords(self):
        """"List passwords."""
        return collection('passwords.json')

    def list_passwords_archived(self):
        """"List archived passwords."""
        return collection('passwords/archived.json')

    def list_passwords_favorite(self):
        """"List favorite passwords."""
        return collection('passwords/favorite.json')

    def list_passwords_search(self, searchstring):
        """"List passwords with searchstring."""
        return collection('passwords/%s.json' % searchstring)

    def show_passwords(self, ID):
        """Show passwords."""
        # http://teampasswordmanager.com/docs/api-passwords/#show_password
        return get('passwords/%s.json' % ID)

    def list_user_access_on_password(self, ID):
        """List users who can access a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#list_users_pwd
        return collection('passwords/%s/security.json' % ID)

    def create_password(self, data):
        """Create a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#create_password
        return post('passwords.json', data)

    def update_password(self, ID, data):
        """Update a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#update_password
        put('passwords/%s.json', ID, data)

    def update_security_of_password(self, ID, data):
        """Update security of a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#update_security_password
        put('passwords/%s/security.json' % ID, data)

    def update_custom_fields_of_password(self, ID, data):
        """Update custom fields definitions of a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#update_cf_password
        put('passwords/%s/custom_fields.json' % ID, data)

    def delete_password(self, ID):
        """Delete a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#delete_password
        delete('passwords/%s.json' % ID)

    def lock_password(self, ID):
        """Lock a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#lock_password
        put('passwords/%s/lock.json' % ID)

    def unlock_password(self, ID):
        """Unlock a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#unlock_password
        put('passwords/%s/unlock.json' % ID)

    def list_mypasswords(self):
        """List my passwords."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#list_passwords
        return collection('my_passwords.json')

    def list_mypasswords_search(self, searchstring):
        """List my passwords with searchstring."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#list_passwords
        return collection('my_passwords/search/%s.json', searchstring)

    def show_mypasswords(self, ID):
        """Show my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#show_password
        return get('my_passwords/%s.json' % ID)

    def create_mypassword(self, data):
        """Create my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#create_password
        return post('my_passwords.json', data)

    def update_mypassword(self, ID, data):
        """Update my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#update_password
        put('my_passwords/%s.json' % ID, data)

    def delete_mypassword(self, ID):
        """Delete my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#delete_password
        delete('my_passwords/%s.json' % ID)

    def set_favorite_password(self, ID):
        """Set a password as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#set_fav
        post('favorite_passwords/%s.json' % ID)

    def unset_favorite_password(self, ID):
        """Unet a password as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#del_fav
        delete('favorite_passwords/%s.json' % ID)

    def set_favorite_project(self, ID):
        """Set a project as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#set_fav
        post('favorite_project/%s.json' % ID)

    def unset_favorite_project(self, ID):
        """Unet a project as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#del_fav
        delete('favorite_project/%s.json' % ID)

    def list_users(self):
        """List users."""
        # http://teampasswordmanager.com/docs/api-users/#list_users
        return collection('users.json')

    def show_user(self, ID):
        """Show a user."""
        # http://teampasswordmanager.com/docs/api-users/#show_user
        return get('users/%s.json') % ID

    def show_me(self):
        """Show me."""
        # http://teampasswordmanager.com/docs/api-users/#show_me
        return get('users/me.json')

    def who_am_i(self):
        """Who am I."""
        return show_me()

    def create_user(self, data):
        """Create a User."""
        # http://teampasswordmanager.com/docs/api-users/#create_user
        return post('users.json', data)

    def update_user(self, ID, data):
        """Update a User.""""
        # http://teampasswordmanager.com/docs/api-users/#update_user
        put('users/%s.json' % ID, data)

    def change_user_password(self, ID, data):
        """Change password of a User."""
        # http://teampasswordmanager.com/docs/api-users/#change_password
        put('users/%s/change_password.json' % ID, data)

    def activate_user(self, ID):
        """Activate a User."""
        # http://teampasswordmanager.com/docs/api-users/#activate_deactivate
        put('users/%s/activate.json' % ID)

    def deactivate_user(self, ID):
        """Dectivate a User."""
        # http://teampasswordmanager.com/docs/api-users/#activate_deactivate
        put('users/%s/deactivate.json' % ID)

    def convert_user_to_ldap(self, ID, DN):
        """Convert a normal user to a LDAP user."""
        # http://teampasswordmanager.com/docs/api-users/#convert_to_ldap
        data = {'login_dn': DN}
        put('users/%s/convert_to_ldap.json' % ID, data)

    def convert_ldap_user_to_normal(self, ID):
        """Convert a LDAP user to a normal user."""
        put('users/%s/convert_to_normal.json' % ID)

    def delete_user(self, ID):
        """Delete a user."""
        # http://teampasswordmanager.com/docs/api-users/#delete_user
        delete('users/%s.json' % ID)

    def list_groups(self):
        """List Groups."""
        # http://teampasswordmanager.com/docs/api-groups/#list_groups
        return collection('groups.json')

    def show_group(self, ID):
        """Show a Group."""
        # http://teampasswordmanager.com/docs/api-groups/#show_group
        return get('groups/%s.json' % ID)

    def create_group(self, data):
        """Create a Group."""
        # http://teampasswordmanager.com/docs/api-groups/#create_group
        return post('groups.json')

    def update_group(self, ID, data):
        """Update a Group.""""
        # http://teampasswordmanager.com/docs/api-groups/#update_group
        put('groups/%s.json' % ID, data)

    def add_user_to_group(self, GroupID, UserID):
        """Add a user to a group."""
        # http://teampasswordmanager.com/docs/api-groups/#add_user
        put('groups/%s/add_user/%s.json' % (GroupID, UserID))

    def delete_user_from_group(self, GroupID, UserID):
        """Delete a user from a group."""
        # http://teampasswordmanager.com/docs/api-groups/#del_user
        put('groups/%s/delete_user/%s.json' % (GroupID, UserID))

    def delete_group(self, ID):
        """Delete a group."""
        # http://teampasswordmanager.com/docs/api-groups/#delete_group
        delete('groups/%s.json' % ID)

    def generate_password(self):
        """Generate a new random password."""
        # http://teampasswordmanager.com/docs/api-passwords-generator/
        get('generate_password.json')

    def get_version(self):
        """Get Version Information."""
        # http://teampasswordmanager.com/docs/api-version/
        get('version.json')

    def get_latest_version(self):
        """Check for latest version."""
        # http://teampasswordmanager.com/docs/api-version/
        get('version/check_latest.json')

    def up_to_date(self):
        """Check if Team Password Manager is up to date."""
        VersionInfo = self.get_latest_version()
        if VersionInfo.get('version') == VersionInfo.get('latest_version'):
            return True
        else:
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
        return collection('projects/%s/subprojects.json' % ID)

    def list_subprojects_action(self, ID, action):
        """List subprojects with allowed action."""
        return collection('projects/%s/subprojects/%s.json' %
                          (ID, action))

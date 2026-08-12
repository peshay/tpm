"""Team Password Manager API

To simplify usage of Team Password Manager API.

You can authenticate with username and password
    >>> import tpm
    >>> URL = "https://mypasswordmanager.example.com"
    >>> USER = 'example-user'
    >>> PASS = 'EXAMPLE_PASSWORD'
    >>> tpmconn = tpm.TpmApiv5(URL, username=USER, password=PASS)

Or with Private/Public Key
    >>> pubkey = 'EXAMPLE_PUBLIC_KEY'
    >>> privkey = 'EXAMPLE_PRIVATE_KEY'
    >>> tpmconn = tpm.TpmApiv5(URL, private_key=privkey, public_key=pubkey)

With the connection object you can use all TPM functions, like list all passwords:
    >>> tpmconn.list_passwords()

All API functions from Team Password Manager are included.
see http://teampasswordmanager.com/docs/api/

:copyright: (c) 2022 by Andreas Hubert.
:license: The MIT License (MIT), see LICENSE for more details.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import re
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import requests

__version__ = '5.0.1'

# set logger
log = logging.getLogger(__name__)
# disable unsecure SSL warning
requests.packages.urllib3.disable_warnings()

# HTTP status codes handled explicitly in error handling.
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
# Allowed range for the X-Page-Size header (API v6).
MIN_PAGE_SIZE = 5
MAX_PAGE_SIZE = 1000

# Validate the base URL passed to the API client.
REGEX_URL = re.compile(
    "^"
    "(?:(?:https?)://)"
    "(?:\\S+(?::\\S*)?@)?"
    "(?:"
    "(?:[1-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])"
    "(?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}"
    "(?:\\.(?:[1-9]\\d?|1\\d\\d|2[0-4]\\d|25[0-4]))"
    "|"
    "(?:(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)"
    "(?:\\.(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)*"
    "(?:\\.(?:[a-z\\u00a1-\\uffff]{2,}))?"
    ".?"
    ")"
    "(?::\\d{2,5})?"
    "(?:[/?#]\\S*)?"
    "$"
)


class TPMException(Exception):
    pass


class TpmApi:
    """Settings needed for the connection to Team Password Manager."""

    class ConfigError(Exception):
        """To throw Exception based on wrong Settings."""

        def __init__(self, value: str):
            self.value = value
            log.critical(value)

        def __str__(self) -> str:
            return repr(self.value)

    def __init__(self, api: str, base_url: str, kwargs: dict):
        """init thing."""
        self.apiurl = f'api/{api}/'
        log.debug(f'Set as apiurl: {self.apiurl}')
        self.api = self.apiurl
        # Check if URL is not bullshit
        if REGEX_URL.match(base_url):
            self.base_url = base_url + '/index.php/'
            log.debug(f'Set Base URL to {self.base_url}')
            self.url = self.base_url + self.apiurl
            log.debug(f'Set URL to {self.url}')
        else:
            raise self.ConfigError(f'Invalid URL: {base_url}')
        # set headers
        self.headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'User-Agent': f'tpm.py/{__version__}',
        }
        log.debug(f'Set header to {self.headers}')
        # check kwargs for either keys or user credentials
        self.private_key = kwargs.get('private_key', False)
        self.public_key = kwargs.get('public_key', False)
        self.username = kwargs.get('username', False)
        self.password = kwargs.get('password', False)
        self.unlock_reason = kwargs.get('unlock_reason', False)
        # TLS certificate verification. Defaults to True; pass verify=False
        # (or a CA bundle path) to override.
        self.verify = kwargs.get('verify', True)
        # Optional page size (X-Page-Size header, API v6). Must be an integer
        # between 5 and 1000 if set.
        self.page_size = kwargs.get('page_size', False)
        if self.page_size is not False and (
                isinstance(self.page_size, bool)
                or not isinstance(self.page_size, int)
                or not MIN_PAGE_SIZE <= self.page_size <= MAX_PAGE_SIZE):
            raise self.ConfigError(
                'page_size must be an integer between 5 and 1000')
        # Reuse a single session for connection pooling.
        self.session = requests.Session()
        if self.private_key is not False and self.public_key is not False and\
                self.username is False and self.password is False:
            log.debug('Using Private/Public Key authentication.')
        elif self.username is not False and self.password is not False and\
                self.private_key is False and self.public_key is False:
            log.debug('Using Basic authentication.')
        else:
            raise self.ConfigError('No authentication specified'
                                   ' (user/password or private/public key)')

    def _build_auth(self, path: str, data: Any) -> Any:
        """Set auth/unlock/page-size headers and return the request auth."""
        auth = None
        # In case of key authentication
        if self.private_key and self.public_key:
            timestamp = str(int(time.time()))
            log.debug(f'Using timestamp: {timestamp}')
            unhashed = path + timestamp + str(data)
            log.debug(f'Using message: {unhashed}')
            self.hash = hmac.new(str.encode(self.private_key),
                                 msg=unhashed.encode('utf-8'),
                                 digestmod=hashlib.sha256).hexdigest()
            log.debug(f'Authenticating with hash: {self.hash}')
            self.headers['X-Public-Key'] = self.public_key
            self.headers['X-Request-Hash'] = self.hash
            self.headers['X-Request-Timestamp'] = timestamp
        # In case of user credentials authentication
        elif self.username and self.password:
            auth = requests.auth.HTTPBasicAuth(self.username, self.password)
        # Set unlock reason
        if self.unlock_reason:
            self.headers['X-Unlock-Reason'] = self.unlock_reason
            log.info(f'Unlock Reason: {self.unlock_reason}')
        # Set page size (API v6)
        if self.page_size:
            self.headers['X-Page-Size'] = str(self.page_size)
            log.debug(f'Page size: {self.page_size}')
        return auth

    def request(self, path: str, action: str, data: Any = '') -> Any:
        """To make a request to the API."""
        # Check if the path includes URL or not.
        head = self.base_url
        if path.startswith(head):
            path = path[len(head):]
            path = quote_plus(path, safe='/')
        if not path.startswith(self.api):
            path = self.api + path
        log.debug(f'Using path {path}')

        # If we have data, convert to JSON
        if data:
            data = json.dumps(data)
            log.debug(f'Data to sent: {data}')
        auth = self._build_auth(path, data)
        url = head + path
        # Try API request and handle Exceptions
        try:
            log.debug(f'{action.upper()} request {url}')
            self.req = self.session.request(action, url, headers=self.headers,
                                            auth=auth, verify=self.verify,
                                            data=data or None)

            if self.req.content == b'':
                result = None
                log.debug('No result returned.')
            else:
                result = self.req.json()
                # Collection endpoints return a list, so guard on the type
                # before treating the payload as an error object.
                if isinstance(result, dict) and result.get('error'):
                    raise TPMException(result['message'])

        # ValueError must be handled before RequestException: in modern
        # requests, response.json() raises requests.exceptions.JSONDecodeError,
        # which subclasses both ValueError and RequestException.
        except ValueError as e:
            if self.req.status_code == HTTP_FORBIDDEN:
                log.warning(f'{url} forbidden')
                raise TPMException(f'{url} forbidden') from e
            if self.req.status_code == HTTP_NOT_FOUND:
                log.warning(f'{url} not found')
                raise TPMException(f'{url} not found') from e
            message = f'{e}: {self.req.url} {self.req.text}'
            log.debug(message)
            raise ValueError(message) from e

        except requests.exceptions.RequestException as e:
            log.critical(f'Connection error for {e}')
            raise TPMException(f'Connection error for {e}') from e

        return result

    def post(self, path: str, data: Any = '') -> Any:
        """For post based requests."""
        return self.request(path, 'post', data)

    def get(self, path: str) -> Any:
        """For get based requests."""
        return self.request(path, 'get')

    def put(self, path: str, data: Any = '') -> Any:
        """For put based requests."""
        return self.request(path, 'put', data)

    def delete(self, path: str) -> None:
        """For delete based requests."""
        self.request(path, 'delete')

    def get_collection(self, path: str) -> Iterator[Any]:
        """To get pagewise data."""
        while True:
            items = self.get(path)
            req = self.req
            yield from items
            if req.links and req.links['next'] and\
                    req.links['next']['rel'] == 'next':
                path = req.links['next']['url']
            else:
                break

    def collection(self, path: str) -> list:
        """To return all items generated by get collection."""
        return list(self.get_collection(path))

    # From now on, Functions that work that way in all API Versions.

    # http://teampasswordmanager.com/docs/api-projects/#list_projects
    def list_projects(self) -> list:
        """List projects."""
        log.debug('List all projects.')
        return self.collection('projects.json')

    def list_projects_archived(self) -> list:
        """List archived projects."""
        log.debug('List all archived projects.')
        return self.collection('projects/archived.json')

    def list_projects_favorite(self) -> list:
        """List favorite projects."""
        log.debug('List all favorite projects.')
        return self.collection('projects/favorite.json')

    def list_projects_search(self, searchstring: str) -> list:
        """List projects with searchstring."""
        log.debug(f'List all projects with: {searchstring}')
        return self.collection(f'projects/search/{quote_plus(searchstring)}.json')

    def show_project(self, ID: int) -> Any:
        """Show a project."""
        # http://teampasswordmanager.com/docs/api-projects/#show_project
        log.debug(f'Show project info: {ID}')
        return self.get(f'projects/{ID}.json')

    def list_passwords_of_project(self, ID: int) -> list:
        """List passwords of project."""
        # http://teampasswordmanager.com/docs/api-projects/#list_pwds_prj
        log.debug(f'List passwords of project: {ID}')
        return self.collection(f'projects/{ID}/passwords.json')

    def list_user_access_on_project(self, ID: int) -> list:
        """List users who can access a project."""
        # http://teampasswordmanager.com/docs/api-projects/#list_users_prj
        log.debug(f'List User access on project: {ID}')
        return self.collection(f'projects/{ID}/security.json')

    def create_project(self, data: dict) -> Any:
        """Create a project."""
        # http://teampasswordmanager.com/docs/api-projects/#create_project
        log.info(f'Create project: {data}')
        new_id = self.post('projects.json', data).get('id')
        log.info(f'Project has been created with ID {new_id}')
        return new_id

    def update_project(self, ID: int, data: dict) -> None:
        """Update a project."""
        # http://teampasswordmanager.com/docs/api-projects/#update_project
        log.info(f'Update project {ID} with {data}')
        self.put(f'projects/{ID}.json', data)

    def change_parent_of_project(self, ID: int, NewParentID: int) -> None:
        """Change parent of project."""
        # http://teampasswordmanager.com/docs/api-projects/#change_parent
        log.info(f'Change parrent for project {ID} to {NewParentID}')
        data = {'parent_id': NewParentID}
        self.put(f'projects/{ID}/change_parent.json', data)

    def update_security_of_project(self, ID: int, data: dict) -> None:
        """Update security of project."""
        # http://teampasswordmanager.com/docs/api-projects/#update_project_security
        log.info(f'Update project {ID} security {data}')
        self.put(f'projects/{ID}/security.json', data)

    def archive_project(self, ID: int) -> None:
        """Archive a project."""
        # http://teampasswordmanager.com/docs/api-projects/#arch_unarch_project
        log.info(f'Archive project {ID}')
        self.put(f'projects/{ID}/archive.json')

    def unarchive_project(self, ID: int) -> None:
        """Un-Archive a project."""
        # http://teampasswordmanager.com/docs/api-projects/#arch_unarch_project
        log.info(f'Unarchive project {ID}')
        self.put(f'projects/{ID}/unarchive.json')

    def delete_project(self, ID: int) -> None:
        """Delete a project."""
        # http://teampasswordmanager.com/docs/api-projects/#delete_project
        log.info(f'Delete project {ID}')
        self.delete(f'projects/{ID}.json')

    # http://teampasswordmanager.com/docs/api-passwords/#list_passwords
    def list_passwords(self) -> list:
        """List passwords."""
        log.debug('List all passwords.')
        return self.collection('passwords.json')

    def list_passwords_archived(self) -> list:
        """List archived passwords."""
        log.debug('List archived passwords.')
        return self.collection('passwords/archived.json')

    def list_passwords_favorite(self) -> list:
        """List favorite passwords."""
        log.debug('List favorite spasswords.')
        return self.collection('passwords/favorite.json')

    def list_passwords_search(self, searchstring: str) -> list:
        """List passwords with searchstring."""
        log.debug(f'List all passwords with: {searchstring}')
        return self.collection(f'passwords/search/{quote_plus(searchstring)}.json')

    def show_password(self, ID: int) -> Any:
        """Show password."""
        # http://teampasswordmanager.com/docs/api-passwords/#show_password
        log.info(f'Show password info: {ID}')
        return self.get(f'passwords/{ID}.json')

    def list_user_access_on_password(self, ID: int) -> list:
        """List users who can access a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#list_users_pwd
        log.debug(f'List user access on password {ID}')
        return self.collection(f'passwords/{ID}/security.json')

    def create_password(self, data: dict) -> Any:
        """Create a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#create_password
        log.info(f'Create new password {data}')
        new_id = self.post('passwords.json', data).get('id')
        log.info(f'Password has been created with ID {new_id}')
        return new_id

    def update_password(self, ID: int, data: dict) -> None:
        """Update a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#update_password
        log.info(f'Update Password {ID} with {data}')
        self.put(f'passwords/{ID}.json', data)

    def update_security_of_password(self, ID: int, data: dict) -> None:
        """Update security of a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#update_security_password
        log.info(f'Update security of password {ID} with {data}')
        self.put(f'passwords/{ID}/security.json', data)

    def update_custom_fields_of_password(self, ID: int, data: dict) -> None:
        """Update custom fields definitions of a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#update_cf_password
        log.info(f'Update custom fields of password {ID} with {data}')
        self.put(f'passwords/{ID}/custom_fields.json', data)

    def delete_password(self, ID: int) -> None:
        """Delete a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#delete_password
        log.info(f'Delete password {ID}')
        self.delete(f'passwords/{ID}.json')

    def lock_password(self, ID: int) -> None:
        """Lock a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#lock_password
        log.info(f'Lock password {ID}')
        self.put(f'passwords/{ID}/lock.json')

    def unlock_password(self, ID: int, reason: str) -> None:
        """Unlock a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#unlock_password
        log.info(f'Unlock password {ID}, Reason: {reason}')
        self.unlock_reason = reason
        self.put(f'passwords/{ID}/unlock.json')

    def list_mypasswords(self) -> list:
        """List my passwords."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#list_passwords
        log.debug('List MyPasswords')
        return self.collection('my_passwords.json')

    def list_mypasswords_search(self, searchstring: str) -> list:
        """List my passwords with searchstring."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#list_passwords
        log.debug(f'List MyPasswords with {searchstring}')
        return self.collection(f'my_passwords/search/{quote_plus(searchstring)}.json')

    def show_mypassword(self, ID: int) -> Any:
        """Show my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#show_password
        log.debug(f'Show MyPassword {ID}')
        return self.get(f'my_passwords/{ID}.json')

    def create_mypassword(self, data: dict) -> Any:
        """Create my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#create_password
        log.info(f'Create MyPassword with {data}')
        new_id = self.post('my_passwords.json', data).get('id')
        log.info(f'MyPassword has been created with {new_id}')
        return new_id

    def update_mypassword(self, ID: int, data: dict) -> None:
        """Update my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#update_password
        log.info(f'Update MyPassword {ID} with {data}')
        self.put(f'my_passwords/{ID}.json', data)

    def delete_mypassword(self, ID: int) -> None:
        """Delete my password."""
        # http://teampasswordmanager.com/docs/api-my-passwords/#delete_password
        log.info(f'Delete password {ID}')
        self.delete(f'my_passwords/{ID}.json')

    def set_favorite_password(self, ID: int) -> None:
        """Set a password as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#set_fav
        log.info(f'Set password {ID} as favorite')
        self.post(f'favorite_passwords/{ID}.json')

    def unset_favorite_password(self, ID: int) -> None:
        """Unet a password as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#del_fav
        log.info(f'Unset password {ID} as favorite')
        self.delete(f'favorite_passwords/{ID}.json')

    def set_favorite_project(self, ID: int) -> None:
        """Set a project as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#set_fav
        log.info(f'Set project {ID} as favorite')
        self.post(f'favorite_project/{ID}.json')

    def unset_favorite_project(self, ID: int) -> None:
        """Unet a project as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#del_fav
        log.info(f'Unset project {ID} as favorite')
        self.delete(f'favorite_project/{ID}.json')

    def list_users(self) -> list:
        """List users."""
        # http://teampasswordmanager.com/docs/api-users/#list_users
        log.debug('List users')
        return self.collection('users.json')

    def show_user(self, ID: int) -> Any:
        """Show a user."""
        # http://teampasswordmanager.com/docs/api-users/#show_user
        log.debug(f'Show user {ID}')
        return self.get(f'users/{ID}.json')

    def show_me(self) -> Any:
        """Show me."""
        # http://teampasswordmanager.com/docs/api-users/#show_me
        log.debug('Show Info about own user')
        return self.get('users/me.json')

    def who_am_i(self) -> Any:
        """Who am I."""
        return self.show_me()

    def create_user(self, data: dict) -> Any:
        """Create a User."""
        # http://teampasswordmanager.com/docs/api-users/#create_user
        log.info(f'Create user with {data}')
        new_id = self.post('users.json', data).get('id')
        log.info(f'User has been created with ID {new_id}')
        return new_id

    def update_user(self, ID: int, data: dict) -> None:
        """Update a User."""
        # http://teampasswordmanager.com/docs/api-users/#update_user
        log.info(f'Update user {ID} with {data}')
        self.put(f'users/{ID}.json', data)

    def change_user_password(self, ID: int, data: dict) -> None:
        """Change password of a User."""
        # http://teampasswordmanager.com/docs/api-users/#change_password
        log.info(f'Change user {ID} password')
        self.put(f'users/{ID}/change_password.json', data)

    def activate_user(self, ID: int) -> None:
        """Activate a User."""
        # http://teampasswordmanager.com/docs/api-users/#activate_deactivate
        log.info(f'Activate user {ID}')
        self.put(f'users/{ID}/activate.json')

    def deactivate_user(self, ID: int) -> None:
        """Dectivate a User."""
        # http://teampasswordmanager.com/docs/api-users/#activate_deactivate
        log.info(f'Deactivate user {ID}')
        self.put(f'users/{ID}/deactivate.json')

    def convert_user_to_ldap(self, ID: int, DN: str) -> None:
        """Convert a normal user to a LDAP user."""
        # http://teampasswordmanager.com/docs/api-users/#convert_to_ldap
        data = {'login_dn': DN}
        log.info(f'Convert User {ID} to LDAP DN {DN}')
        self.put(f'users/{ID}/convert_to_ldap.json', data)

    def convert_ldap_user_to_normal(self, ID: int) -> None:
        """Convert a LDAP user to a normal user."""
        log.info(f'Convert User {ID} from LDAP to normal user')
        self.put(f'users/{ID}/convert_to_normal.json')

    def delete_user(self, ID: int) -> None:
        """Delete a user."""
        # http://teampasswordmanager.com/docs/api-users/#delete_user
        log.info(f'Delete user {ID}')
        self.delete(f'users/{ID}.json')

    def list_groups(self) -> list:
        """List Groups."""
        # http://teampasswordmanager.com/docs/api-groups/#list_groups
        log.debug('List groups')
        return self.collection('groups.json')

    def show_group(self, ID: int) -> Any:
        """Show a Group."""
        # http://teampasswordmanager.com/docs/api-groups/#show_group
        log.debug(f'Show group {ID}')
        return self.get(f'groups/{ID}.json')

    def create_group(self, data: dict) -> Any:
        """Create a Group."""
        # http://teampasswordmanager.com/docs/api-groups/#create_group
        log.info(f'Create group with {data}')
        new_id = self.post('groups.json', data).get('id')
        log.info(f'Group has been created with ID {new_id}')
        return new_id

    def update_group(self, ID: int, data: dict) -> None:
        """Update a Group."""
        # http://teampasswordmanager.com/docs/api-groups/#update_group
        log.info(f'Update group {ID} with {data}')
        self.put(f'groups/{ID}.json', data)

    def add_user_to_group(self, GroupID: int, UserID: int) -> None:
        """Add a user to a group."""
        # http://teampasswordmanager.com/docs/api-groups/#add_user
        log.info(f'Add User {UserID} to Group {GroupID}')
        self.put(f'groups/{GroupID}/add_user/{UserID}.json')

    def delete_user_from_group(self, GroupID: int, UserID: int) -> None:
        """Delete a user from a group."""
        # http://teampasswordmanager.com/docs/api-groups/#del_user
        log.info(f'Delete user {UserID} from group {GroupID}')
        self.put(f'groups/{GroupID}/delete_user/{UserID}.json')

    def delete_group(self, ID: int) -> None:
        """Delete a group."""
        # http://teampasswordmanager.com/docs/api-groups/#delete_group
        log.info(f'Delete group {ID}')
        self.delete(f'groups/{ID}.json')

    def generate_password(self) -> Any:
        """Generate a new random password."""
        # http://teampasswordmanager.com/docs/api-passwords-generator/
        log.debug('Generate new password')
        return self.get('generate_password.json')

    def get_version(self) -> Any:
        """Get Version Information."""
        # http://teampasswordmanager.com/docs/api-version/
        log.debug('Get version information')
        return self.get('version.json')

    def get_latest_version(self) -> Any:
        """Check for latest version."""
        # http://teampasswordmanager.com/docs/api-version/
        log.debug('Get latest version')
        return self.get('version/check_latest.json')

    def up_to_date(self) -> bool:
        """Check if Team Password Manager is up to date."""
        version_info = self.get_latest_version()
        current_version = version_info.get('version')
        latest_version = version_info.get('latest_version')
        if current_version == latest_version:
            log.info('TeamPasswordManager is up-to-date!')
            log.debug(f'Current Version: {latest_version} Latest Version: {latest_version}')
            return True
        log.warning('TeamPasswordManager is not up-to-date!')
        log.debug(f'Current Version: {latest_version} Latest Version: {latest_version}')
        return False


class TpmApiv3(TpmApi):
    """API v3 based class."""

    def __init__(self, url: str, **kwargs):
        super().__init__('v3', url, kwargs)
    """From now on, Functions that only work with API v3."""


class TpmApiv4(TpmApi):
    """API v4 based class."""

    def __init__(self, url: str, **kwargs):
        super().__init__('v4', url, kwargs)
    """From now on, Functions that only work with API v4."""

    def list_subprojects(self, ID: int) -> list:
        """List subprojects."""
        # http://teampasswordmanager.com/docs/api-projects/#list_subprojects
        log.debug(f'List subprojects of {ID}')
        return self.collection(f'projects/{ID}/subprojects.json')

    def list_subprojects_action(self, ID: int, action: str) -> list:
        """List subprojects with allowed action."""
        log.debug(f'List subprojects of {ID} with action: {action}')
        return self.collection(f'projects/{ID}/subprojects/{action}.json')


class TpmApiv5(TpmApiv4):
    """API v5 based class."""

    def __init__(self, url: str, **kwargs):
        # Deliberately skip TpmApiv4.__init__ to register as 'v5' on TpmApi.
        super(TpmApiv4, self).__init__('v5', url, kwargs)
    """From now on, Functions that only work with API v5."""

    def list_project_files(self, ID: int) -> list:
        """List files of a project."""
        return self.collection(f'projects/{ID}/files.json')

    def _upload_file(self, upload_path: str, file: str, **kwargs) -> Any:
        """Base64-encode a local file and upload it to the given API path."""
        path = Path(file)
        if not path.is_file():
            raise FileNotFoundError(f'File not found: {file}')
        encoded = base64.b64encode(path.read_bytes())
        data = {
            "file_data_base64": encoded.decode('ascii'),
            "file_name": path.name,
        }
        if 'notes' in kwargs:
            data['notes'] = kwargs['notes']
        new_id = self.post(upload_path, data).get('id')
        log.info(f'File has been uploaded with ID {new_id}')
        return new_id

    def upload_project_file(self, ID: int, file: str, **kwargs) -> Any:
        """Upload a file to a project."""
        return self._upload_file(f'projects/{ID}/upload.json', file, **kwargs)

    def archive_password(self, ID: int) -> None:
        """Archive a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#arch_unarch_password
        log.info(f'Archive password {ID}')
        self.put(f'passwords/{ID}/archive.json')

    def unarchive_password(self, ID: int) -> None:
        """Un-Archive a project."""
        # http://teampasswordmanager.com/docs/api-passwords/#arch_unarch_password
        log.info(f'Unarchive password {ID}')
        self.put(f'passwords/{ID}/unarchive.json')

    def move_password(self, ID: int, PROJECT_ID: int) -> None:
        """Move a password to another project."""
        # http://teampasswordmanager.com/docs/api-passwords/#move_password
        log.info(f'Move password {ID} to Project {PROJECT_ID}')
        self.put(f'passwords/{ID}/move.json', data={"project_id": PROJECT_ID})

    def list_password_files(self, ID: int) -> list:
        """List files of a password."""
        # http://teampasswordmanager.com/docs/api-passwords/#list_files
        log.info(f'List files of password: {ID}')
        return self.collection(f'passwords/{ID}/files.json')

    def upload_password_file(self, ID: int, file: str, **kwargs) -> Any:
        """Upload a file to a password."""
        return self._upload_file(f'passwords/{ID}/upload.json', file, **kwargs)

    def move_mypassword(self, ID: int, PROJECT_ID: int) -> Any:
        """Move a mypassword to another project."""
        # https://teampasswordmanager.com/docs/api-my-passwords/#move_password
        log.info(f'Move my_password {ID} to Project {PROJECT_ID}')
        return self.put(f'my_passwords/{ID}/move.json', data={"project_id": PROJECT_ID}).get('id')

    def show_file_info(self, ID: int) -> Any:
        """Show info of a file."""
        # https://teampasswordmanager.com/docs/api-files/#show_file
        log.info(f'Show info of file with ID: {ID}')
        return self.get(f'files/{ID}.json')

    def update_file_notes(self, ID: int, NOTES: str) -> None:
        """Update the notes on a file."""
        # https://teampasswordmanager.com/docs/api-files/#update_file
        log.info(f'Update notes on file {ID} to: {NOTES}')
        self.put(f'files/{ID}.json', data={"notes": NOTES})

    def max_upload_file_size(self) -> Any:
        """Show max upload file size."""
        # https://teampasswordmanager.com/docs/api-files/#max_upload_file_size
        log.info('Show max_upload_file_size')
        return self.get('files/max_upload_file_size.json')

    def uploads_folder_info(self) -> Any:
        """Show uploads folder info."""
        # https://teampasswordmanager.com/docs/api-files/#uploads_folder
        log.info('Show uploads_folder_info')
        return self.get('files/uploads_folder_info.json')

    def download_file(self, ID: int) -> Any:
        """Get the content of a file."""
        # https://teampasswordmanager.com/docs/api-files/#download_file
        log.info(f'Download file with ID: {ID}')
        return self.get(f'files/download/{ID}.json')

    def delete_file(self, ID: int) -> None:
        """Delete a file."""
        # https://teampasswordmanager.com/docs/api-files/#delete_file
        log.info(f'Delete file {ID}')
        self.delete(f'files/{ID}.json')

    def create_user_ldap(self, data: dict) -> Any:
        """Create a LDAP User."""
        # http://teampasswordmanager.com/docs/api-users/#create_user_ldap
        log.info(f'Create LDAP user with {data}')
        new_id = self.post('users_ldap.json', data).get('id')
        log.info(f'LDAP User has been created with ID {new_id}')
        return new_id

    def create_user_saml(self, data: dict) -> Any:
        """Create a SAML User."""
        # http://teampasswordmanager.com/docs/api-users/#create_user_saml
        log.info(f'Create SAML user with {data}')
        new_id = self.post('users_saml.json', data).get('id')
        log.info(f'SAML User has been created with ID {new_id}')
        return new_id

    def convert_user_to_ldap(self, ID: int, DN: str, SERVER_ID: int) -> None:
        """Convert a normal user to a LDAP user."""
        # http://teampasswordmanager.com/docs/api-users/#convert_to_ldap
        data = {'login_dn': DN, "ldap_server_id": SERVER_ID}
        log.info(f'Convert User {ID} to LDAP DN {DN} at Server {SERVER_ID}')
        self.put(f'users/{ID}/convert_to_ldap.json', data)

    def convert_user_to_saml(self, ID: int) -> None:
        """Convert a normal user to a SAML user."""
        # http://teampasswordmanager.com/docs/api-users/#convert_to_saml
        log.info(f'Convert User {ID} to SAML')
        self.put(f'users/{ID}/convert_to_saml.json')


class TpmApiv6(TpmApiv5):
    """API v6 based class."""

    def __init__(self, url: str, **kwargs):
        # Deliberately skip the intermediate __init__s to register as 'v6'
        # on TpmApi (super(TpmApiv4, self) resolves to TpmApi in the MRO).
        super(TpmApiv4, self).__init__('v6', url, kwargs)
    """From now on, Functions that only work with API v6."""

    def list_log(self) -> list:
        """List the log."""
        # https://teampasswordmanager.com/docs/api-log/
        log.debug('List log')
        return self.collection('log.json')

    def list_log_search(self, searchstring: str) -> list:
        """Search the log."""
        # https://teampasswordmanager.com/docs/api-log/
        log.debug(f'Search log with: {searchstring}')
        return self.collection(f'log/search/{quote_plus(searchstring)}.json')

    def list_user_passwords(self, ID: int) -> list:
        """List passwords a user can access (Admin only)."""
        # http://teampasswordmanager.com/docs/api-users/
        log.debug(f'List passwords accessible by user {ID}')
        return self.collection(f'users/{ID}/passwords.json')

    def list_user_projects(self, ID: int) -> list:
        """List projects a user can access (Admin only)."""
        # http://teampasswordmanager.com/docs/api-users/
        log.debug(f'List projects accessible by user {ID}')
        return self.collection(f'users/{ID}/projects.json')

    def list_mypasswords_archived(self) -> list:
        """List archived my passwords."""
        # http://teampasswordmanager.com/docs/api-my-passwords/
        log.debug('List archived MyPasswords')
        return self.collection('my_passwords/archived.json')

    def list_mypasswords_favorite(self) -> list:
        """List favorite my passwords."""
        # http://teampasswordmanager.com/docs/api-my-passwords/
        log.debug('List favorite MyPasswords')
        return self.collection('my_passwords/favorite.json')

    def set_favorite_mypassword(self, ID: int) -> None:
        """Set a my password as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#set_fav
        log.info(f'Set my_password {ID} as favorite')
        self.post(f'favorite_my_passwords/{ID}.json')

    def unset_favorite_mypassword(self, ID: int) -> None:
        """Unset a my password as favorite."""
        # http://teampasswordmanager.com/docs/api-favorites/#del_fav
        log.info(f'Unset my_password {ID} as favorite')
        self.delete(f'favorite_my_passwords/{ID}.json')

    def set_favorite_project(self, ID: int) -> None:
        """Set a project as favorite (v6 uses the plural endpoint)."""
        # http://teampasswordmanager.com/docs/api-favorites/#set_fav
        log.info(f'Set project {ID} as favorite')
        self.post(f'favorite_projects/{ID}.json')

    def unset_favorite_project(self, ID: int) -> None:
        """Unset a project as favorite (v6 uses the plural endpoint)."""
        # http://teampasswordmanager.com/docs/api-favorites/#del_fav
        log.info(f'Unset project {ID} as favorite')
        self.delete(f'favorite_projects/{ID}.json')

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


class TPMException(Exception):
    pass


class TpmApi(object):
    """Settings needed for the connection to Team Password Manager."""
    class ConfigError(Exception):
        """To throw Exception based on wrong Settings."""
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)

    def __init__(self, api, base_url, kwargs):
        """init thing."""

        # Check if API version and URL is not bullshit
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
        if re.match(REGEXurl, base_url):
            self.url = base_url + self.apiurl
            self.base_url = base_url
        else:
            raise ConfigError('Invalid URL: %s' % url)
        # set header
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
        head = self.base_url
        if path.startswith(head):
            path = path[len(head):]
        if not path.startswith(self.api):
            path = self.api + path
        if data:
            data = json.dumps(data)
        if self.private_key and self.public_key:
            timestamp = str(int(time.time()))
            unhashed = path + timestamp + data
            hash = hmac.new(str.encode(self.private_key),
                            msg=unhashed.encode('utf-8'),
                            digestmod=hashlib.sha256).hexdigest()
            self.headers['X-Public-Key'] = self.public_key
            self.headers['X-Request-Hash'] = hash
            self.headers['X-Request-Timestamp'] = timestamp
        elif self.username and self.password:
            auth = requests.auth.HTTPBasicAuth(self.username, self.password)

        if self.unlock_reason:
            self.headers['X-Unlock-Reason'] = self.unlock_reason

        url = head + path
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
        return self.request(path, 'post', data)

    def get(self, path):
        return self.request(path, 'get')

    def get_collection(self, path):
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

    def listPasswords(self):
        data = []
        for item in self.get_collection('passwords.json'):
            data.append(item)
        return data


class TpmApiv3(TpmApi):
    def __init__(self, url, **kwargs):
        super(TpmApiv3, self).__init__('v3', url, kwargs)


class TpmApiv4(TpmApi):
    def __init__(self, url, **kwargs):
        super(TpmApiv4, self).__init__('v4', url, kwargs)

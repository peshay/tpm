import requests
import requests_mock
import unittest
import os.path
import tpm
import json
import logging

log = logging.getLogger(__name__)

api_url = 'https://tpm.example.com/index.php/api/v4/'
local_path = 'tests/resources/'

item_limit = 20

def fake_data(url, m):
    """
    A stub urlopen() implementation that load json responses from
    the filesystem.
    """

    # Map path from url to a file
    path_parts = url.split('/')[6:]
    path = '/'.join(path_parts)
    resource_file = os.path.normpath('tests/resources/{}'.format(path))
    data_file = open(resource_file)
    data = json.load(data_file)

    # Must return a json-like object
    count = 0
    header = {}
    while True:
        count += 1
        if len(data) > item_limit:
            returndata = data[:item_limit]
            data = data[item_limit:]
            pageingurl = url.replace('.json', '/page/{}.json'.format(count))
            log.debug("Registering URL: {}".format(pageingurl))
            log.debug("Registering data: {}".format(returndata))
            log.debug("Data length: {}".format(len(returndata)))
            log.debug("Registering header: {}".format(header))
            m.get(pageingurl, json=returndata, headers=header.copy())
            header = { 'link': '{}; rel="next"'.format(pageingurl)}
        else:
            log.debug("Registering URL: {}".format(url))
            log.debug("Registering data: {}".format(data))
            log.debug("Registering header: {}".format(header))
            log.debug("Data length: {}".format(len(data)))
            m.get(url, json=data, headers=header.copy())
            header.clear()
            break

class ClientTestCase(unittest.TestCase):
    """Test case for the client methods."""
    def setUp(self):
        self.client = tpm.TpmApiv4('https://tpm.example.com', username='USER', password='PASS')

    def test_user_auth_method(self):
        """Test user based authentication method."""
        pass

    def test_paging(self):
        """Test paging, if number of items is same as from original data source."""
        path_to_mock = 'passwords.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        data_file = open(resource_file)
        data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_passwords()
        # number of passwords as from original json file.
        source_items = len(data)
        response_items = len(response)
        log.debug("Source Items: {}; Response Items: {}".format(source_items, response_items))
        self.assertEqual(source_items, response_items)

    def test_logging(self):
        """Test Logging."""
        pass

class ExceptionTestCase(unittest.TestCase):
    """Test case for all kind of Exceptions."""
    def test_wrong_auth_exception(self):
        """Exception if wrong authentication mehtod."""
        with self.assertRaises(tpm.TpmApi.ConfigError) as context:
            tpm.TpmApiv4('https://tpm.example.com', username='USER', private_key='PASS')
        log.debug("context exception: {}".format(context.exception))
        self.assertEqual("'No authentication specified (user/password or private/public key)'", str(context.exception))

    def test_wrong_url_exception(self):
        """Exception if URL does not match REGEXurl."""
        wrong_url = 'ftp://tpm.example.com'
        with self.assertRaises(tpm.TpmApiv4.ConfigError) as context:
            tpm.TpmApiv4(wrong_url, username='USER', password='PASS')
        log.debug("context exception: {}".format(context.exception))
        self.assertEqual("'Invalid URL: {}'".format(wrong_url), str(context.exception))

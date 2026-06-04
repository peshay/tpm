import requests_mock
import unittest
import os.path
import tpm
import json
import logging

log = logging.getLogger(__name__)

api_url = 'https://tpm.example.com/index.php/api/v6/'
local_path = 'tests/resources/'

item_limit = 20


def fake_data(url, m, altpath=False):
    """
    A stub urlopen() implementation that load json responses from
    the filesystem.
    """
    # Map path from url to a file
    path_parts = url.split('/')[6:]
    if not altpath:
        path = '/'.join(path_parts)
    else:
        path = altpath
    resource_file = os.path.normpath('tests/resources/{}'.format(path))
    with open(resource_file, 'r') as data_file:
        data_txt = data_file.read()

    data = json.loads(data_txt)
    data_len = len(data)
    log.debug('Data length: {}'.format(data_len))

    # Must return a json-like object
    header = {}
    count = 0
    while True:
        count += 1
        if data_len > item_limit and isinstance(data, list):
            returndata = data[:item_limit]
            returndata_txt = json.dumps(returndata)
            data = data[item_limit:]
            data_txt = json.dumps(data)
            pageingurl = url.replace('.json', '/page/{}.json'.format(count))
            m.get(pageingurl.replace(" ", "+"), text=returndata_txt, headers=header.copy())
            m.post(pageingurl.replace(" ", "+"), text=returndata_txt, headers=header.copy())
            m.put(pageingurl.replace(" ", "+"), text=returndata_txt, headers=header.copy())
            header = {'link': '{}; rel="next"'.format(pageingurl)}
            data_len = len(data)
        else:
            m.get(url.replace(" ", "+"), text=data_txt, headers=header.copy())
            m.post(url.replace(" ", "+"), text=data_txt, headers=header.copy())
            m.put(url.replace(" ", "+"), text=data_txt, headers=header.copy())
            header.clear()
            break


def load_fixture(path_to_mock):
    """Load the expected json fixture from disk."""
    resource_file = os.path.normpath(local_path + path_to_mock)
    with open(resource_file) as data_file:
        return json.load(data_file)


class ClientInitTestCase(unittest.TestCase):
    """Test cases for the v6 client setup."""

    def test_v6_api_version(self):
        """TpmApiv6 registers as api/v6/ and inherits v5 functions."""
        client = tpm.TpmApiv6('https://tpm.example.com', username='USER', password='PASS')
        self.assertEqual(client.api, 'api/v6/')
        self.assertTrue(client.url.endswith('/index.php/api/v6/'))
        # inherited from TpmApiv5 / TpmApi
        self.assertTrue(hasattr(client, 'list_password_files'))
        self.assertTrue(hasattr(client, 'list_passwords'))

    def test_v6_inherited_function(self):
        """An inherited function works through the v6 client."""
        client = tpm.TpmApiv6('https://tpm.example.com', username='USER', password='PASS')
        path_to_mock = 'passwords.json'
        request_url = api_url + path_to_mock
        data = sorted(load_fixture(path_to_mock), key=lambda k: k['id'])
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = sorted(client.list_passwords(), key=lambda k: k['id'])
        self.assertEqual(data, response)


class ClientLogTestCase(unittest.TestCase):
    """Test cases for the v6 log endpoints."""

    def setUp(self):
        self.client = tpm.TpmApiv6('https://tpm.example.com', username='USER', password='PASS')

    def test_function_list_log(self):
        """NEW v6: Test function list_log."""
        path_to_mock = 'log.json'
        request_url = api_url + path_to_mock
        data = load_fixture(path_to_mock)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_log()
        self.assertEqual(data, response)

    def test_function_list_log_search(self):
        """NEW v6: Test function list_log_search."""
        search = 'facebook'
        path_to_mock = 'log/search/{}.json'.format(search)
        request_url = api_url + path_to_mock
        data = load_fixture(path_to_mock)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_log_search(search)
        self.assertEqual(data, response)


class ClientUserAccessTestCase(unittest.TestCase):
    """Test cases for the v6 user access endpoints."""

    def setUp(self):
        self.client = tpm.TpmApiv6('https://tpm.example.com', username='USER', password='PASS')

    def test_function_list_user_passwords(self):
        """NEW v6: Test function list_user_passwords."""
        path_to_mock = 'users/4/passwords.json'
        request_url = api_url + path_to_mock
        data = load_fixture(path_to_mock)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_user_passwords('4')
        self.assertEqual(data, response)

    def test_function_list_user_projects(self):
        """NEW v6: Test function list_user_projects."""
        path_to_mock = 'users/4/projects.json'
        request_url = api_url + path_to_mock
        data = load_fixture(path_to_mock)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_user_projects('4')
        self.assertEqual(data, response)


class ClientMyPasswordFavoriteTestCase(unittest.TestCase):
    """Test cases for the v6 my password favorite/archived endpoints."""

    def setUp(self):
        self.client = tpm.TpmApiv6('https://tpm.example.com', username='USER', password='PASS')

    def test_function_list_mypasswords_archived(self):
        """NEW v6: Test function list_mypasswords_archived."""
        path_to_mock = 'my_passwords/archived.json'
        request_url = api_url + path_to_mock
        data = load_fixture(path_to_mock)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_mypasswords_archived()
        self.assertEqual(data, response)

    def test_function_list_mypasswords_favorite(self):
        """NEW v6: Test function list_mypasswords_favorite."""
        path_to_mock = 'my_passwords/favorite.json'
        request_url = api_url + path_to_mock
        data = load_fixture(path_to_mock)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_mypasswords_favorite()
        self.assertEqual(data, response)

    def test_function_set_favorite_mypassword(self):
        """NEW v6: Test function set_favorite_mypassword."""
        path_to_mock = 'favorite_my_passwords/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.post(request_url, status_code=204)
            response = self.client.set_favorite_mypassword('4')
        self.assertEqual(response, None)

    def test_function_unset_favorite_mypassword(self):
        """NEW v6: Test function unset_favorite_mypassword."""
        path_to_mock = 'favorite_my_passwords/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.delete(request_url, status_code=204)
            response = self.client.unset_favorite_mypassword('4')
        self.assertEqual(response, None)


if __name__ == '__main__':
    unittest.main()

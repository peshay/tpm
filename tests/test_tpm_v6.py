import json
import logging
import os.path
import unittest

import requests_mock

import tpm

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
    resource_file = os.path.normpath(f'tests/resources/{path}')
    with open(resource_file, 'r') as data_file:
        data_txt = data_file.read()

    try:
        data = json.loads(data_txt)
    except ValueError:
        # Issue #14: serve non-JSON content as-is so tpm raises the error
        # through its own request handling, instead of the test helper
        # choking on json.loads.
        clean_url = url.replace(" ", "+")
        m.get(clean_url, text=data_txt)
        m.post(clean_url, text=data_txt)
        m.put(clean_url, text=data_txt)
        return
    data_len = len(data)
    log.debug(f'Data length: {data_len}')

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
            pageingurl = url.replace('.json', f'/page/{count}.json')
            m.get(pageingurl.replace(" ", "+"), text=returndata_txt, headers=header.copy())
            m.post(pageingurl.replace(" ", "+"), text=returndata_txt, headers=header.copy())
            m.put(pageingurl.replace(" ", "+"), text=returndata_txt, headers=header.copy())
            header = {'link': f'{pageingurl}; rel="next"'}
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


class MockHelperTestCase(unittest.TestCase):
    """Issue #14: fake_data serves non-JSON content as-is and lets tpm raise
    the error through its own request handling, instead of the helper choking
    on json.loads."""

    def setUp(self):
        self.client = tpm.TpmApiv6('https://tpm.example.com', username='USER', password='PASS')

    def test_fake_data_non_json_response(self):
        """fake_data registers a non-JSON fixture without raising itself."""
        path_to_mock = 'plain.txt'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            # Must not raise here (previously json.loads blew up in the helper).
            fake_data(request_url, m)
            # tpm is what surfaces the invalid-JSON response as a ValueError.
            with self.assertRaises(ValueError):
                self.client.get(path_to_mock)


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
        path_to_mock = f'log/search/{search}.json'
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


class ClientProjectFavoriteTestCase(unittest.TestCase):
    """Test cases for the v6 project favorite override (plural endpoint)."""

    def setUp(self):
        self.client = tpm.TpmApiv6('https://tpm.example.com', username='USER', password='PASS')

    def test_function_set_favorite_project(self):
        """NEW v6: set_favorite_project uses the plural favorite_projects endpoint."""
        path_to_mock = 'favorite_projects/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.post(request_url, status_code=204)
            response = self.client.set_favorite_project('4')
            self.assertEqual('POST', m.last_request.method)
            self.assertTrue(m.last_request.url.endswith('/favorite_projects/4.json'))
        self.assertEqual(response, None)

    def test_function_unset_favorite_project(self):
        """NEW v6: unset_favorite_project uses the plural favorite_projects endpoint."""
        path_to_mock = 'favorite_projects/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.delete(request_url, status_code=204)
            response = self.client.unset_favorite_project('4')
            self.assertEqual('DELETE', m.last_request.method)
            self.assertTrue(m.last_request.url.endswith('/favorite_projects/4.json'))
        self.assertEqual(response, None)


class ClientPageSizeTestCase(unittest.TestCase):
    """Test cases for the v6 X-Page-Size header option."""

    def test_page_size_header_sent(self):
        """NEW v6: page_size sets the X-Page-Size header on requests."""
        client = tpm.TpmApiv6('https://tpm.example.com', username='USER',
                              password='PASS', page_size=50)
        path_to_mock = 'log.json'
        request_url = api_url + path_to_mock
        data = load_fixture(path_to_mock)
        with requests_mock.Mocker() as m:
            # request_headers acts as a matcher: the call only matches if the
            # X-Page-Size header is present with this value.
            m.get(request_url, text=json.dumps(data),
                  request_headers={'X-Page-Size': '50'})
            response = client.list_log()
            self.assertEqual('50', m.last_request.headers.get('X-Page-Size'))
        self.assertEqual(data, response)

    def test_no_page_size_header_by_default(self):
        """Without page_size no X-Page-Size header is sent."""
        client = tpm.TpmApiv6('https://tpm.example.com', username='USER', password='PASS')
        path_to_mock = 'log.json'
        request_url = api_url + path_to_mock
        data = load_fixture(path_to_mock)
        with requests_mock.Mocker() as m:
            m.get(request_url, text=json.dumps(data))
            client.list_log()
            self.assertIsNone(m.last_request.headers.get('X-Page-Size'))

    def test_page_size_too_small_raises(self):
        """page_size below 5 raises ConfigError."""
        with self.assertRaises(tpm.TpmApi.ConfigError):
            tpm.TpmApiv6('https://tpm.example.com', username='USER',
                         password='PASS', page_size=4)

    def test_page_size_too_large_raises(self):
        """page_size above 1000 raises ConfigError."""
        with self.assertRaises(tpm.TpmApi.ConfigError):
            tpm.TpmApiv6('https://tpm.example.com', username='USER',
                         password='PASS', page_size=1001)

    def test_page_size_non_integer_raises(self):
        """A non-integer page_size raises ConfigError."""
        with self.assertRaises(tpm.TpmApi.ConfigError):
            tpm.TpmApiv6('https://tpm.example.com', username='USER',
                         password='PASS', page_size='big')

    def test_page_size_bool_raises(self):
        """A boolean page_size raises ConfigError."""
        with self.assertRaises(tpm.TpmApi.ConfigError):
            tpm.TpmApiv6('https://tpm.example.com', username='USER',
                         password='PASS', page_size=True)


if __name__ == '__main__':
    unittest.main()

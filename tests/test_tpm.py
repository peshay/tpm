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
        if len(data) > item_limit and isinstance(data,list):
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
    client = tpm.TpmApiv4('https://tpm.example.com', username='USER', password='PASS')
    # get all retrievable sample data
    path_to_mock = 'projects.json'
    request_url = api_url + path_to_mock
    with requests_mock.Mocker() as m:
        fake_data(request_url, m)
        global Projects
        Projects = client.list_projects()
    path_to_mock = 'passwords.json'
    request_url = api_url + path_to_mock
    with requests_mock.Mocker() as m:
        fake_data(request_url, m)
        global Passwords
        Passwords = client.list_passwords()
    path_to_mock = 'my_passwords.json'
    request_url = api_url + path_to_mock
    with requests_mock.Mocker() as m:
        fake_data(request_url, m)
        global MyPasswords
        MyPasswords = client.list_mypasswords()
    path_to_mock = 'users.json'
    request_url = api_url + path_to_mock
    with requests_mock.Mocker() as m:
        fake_data(request_url, m)
        global Users
        Users = client.list_users()
    path_to_mock = 'groups.json'
    request_url = api_url + path_to_mock
    with requests_mock.Mocker() as m:
        fake_data(request_url, m)
        global Groups
        Groups = client.list_groups()

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

    def test_list_projects(self):
        """Test function list_projects."""
        path_to_mock = 'projects.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        data_file = open(resource_file)
        data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_projects()
        # number of passwords as from original json file.
        self.assertEqual(data, response)

    def test_list_projects_archived(self):
        """Test function list_projects_archived."""
        path_to_mock = 'projects/archived.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        data_file = open(resource_file)
        data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_projects_archived()
        # number of passwords as from original json file.
        self.assertEqual(data, response)

    def test_list_projects_favorite(self):
        """Test function list_projects_favorite."""
        path_to_mock = 'projects/favorite.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        data_file = open(resource_file)
        data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_projects_favorite()
        # number of passwords as from original json file.
        self.assertEqual(data, response)

    def test_list_projects_search(self):
        """Test function list_projects_search."""
        searches = ['company', 'internal', 'website']
        for search in searches:
            path_to_mock = 'projects/search/{}.json'.format(search)
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            data_file = open(resource_file)
            data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.list_projects_search(search)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_show_project(self):
        """Test function show_project."""
        for project in Projects:
            project_id = project.get('id')
            log.debug("Testing with Project ID: {}".format(project_id))
            path_to_mock = 'projects/{}.json'.format(project_id)
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            data_file = open(resource_file)
            data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.show_project(project_id)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_list_passwords_of_project(self):
        """Test function list_passwords_of_project."""
        for project in Projects:
            project_id = project.get('id')
            log.debug("Testing with Project ID: {}".format(project_id))
            path_to_mock = 'projects/{}/passwords.json'.format(project_id)
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            data_file = open(resource_file)
            data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.list_passwords_of_project(project_id)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_list_user_access_on_project(self):
        """Test function list_user_access_on_project."""
        for project in Projects:
            project_id = project.get('id')
            log.debug("Testing with Project ID: {}".format(project_id))
            path_to_mock = 'projects/{}/security.json'.format(project_id)
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            data_file = open(resource_file)
            data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.list_user_access_on_project(project_id)
            # number of passwords as from original json file.
            self.assertEqual(data, response)


class ExceptionTestCases(unittest.TestCase):
    """Test case for Config Exceptions."""
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

class ExceptionOnRequestsTestCases(unittest.TestCase):
    """Test case for Request based Exceptions."""
    def setUp(self):
        self.client = tpm.TpmApiv4('https://tpm.example.com', username='USER', password='PASS')

    def test_connection_exception(self):
        """Exception if connection fails."""
        exception_error = "Connection error for HTTPSConnectionPool(host='tpm.example.com', port=443)"
        with self.assertRaises(tpm.TPMException) as context:
            self.client.list_passwords()
        log.debug("context exception: {}".format(context.exception))
        self.assertTrue(exception_error in str(context.exception))

    """Test cases for Exceptions on connection"""
    def test_value_error_exception(self):
        """Exception if value is not json format."""
        exception_error = "Extra data: "
        path_to_mock = 'passwords/value_error.json'
        request_url = api_url + path_to_mock
        with self.assertRaises(ValueError) as context:
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.show_passwords('value_error')
        log.debug("context exception: {}".format(context.exception))
        self.assertTrue(exception_error in str(context.exception))

    def test_exception_on_403(self):
        """Exception if 403 forbidden."""
        path_to_mock = 'passwords.json'
        request_url = api_url + path_to_mock
        exception_error = "{} forbidden".format(request_url)
        with self.assertRaises(tpm.TPMException) as context:
            with requests_mock.Mocker() as m:
                m.get(request_url, text='forbidden', status_code=403)
                response = self.client.list_passwords()
        log.debug("context exception: {}".format(context.exception))
        self.assertTrue(exception_error in str(context.exception))

    def test_exception_on_404(self):
        """Exception if 404 not found."""
        path_to_mock = 'passwords.json'
        request_url = api_url + path_to_mock
        exception_error = "{} not found".format(request_url)
        with self.assertRaises(tpm.TPMException) as context:
            with requests_mock.Mocker() as m:
                m.get(request_url, text='not found', status_code=404)
                response = self.client.list_passwords()
        log.debug("context exception: {}".format(context.exception))
        self.assertTrue(exception_error in str(context.exception))

    def test_exception_on_405(self):
        """Exception if 405 Method Not Allowed."""
        path_to_mock = 'passwords.json'
        request_url = api_url + path_to_mock
        exception_error = "{} Method Not Allowed".format(request_url)
        with self.assertRaises(tpm.TPMException) as context:
            with requests_mock.Mocker() as m:
                m.get(request_url, text='Method Not Allowed', status_code=405)
                response = self.client.list_passwords()
        log.debug("context exception: {}".format(context.exception))
        self.assertTrue(str(context.exception).startswith(exception_error))

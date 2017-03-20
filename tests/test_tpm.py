import requests
import requests_mock
import unittest
import os.path
import tpm
import json

url = 'https://tpm.example.com/index.php/api/v4/projects.json'

def fake_data(url, action, data):
    """
    A stub urlopen() implementation that load json responses from
    the filesystem.
    """
    # Map path from url to a file
    path_parts = url.split('/')[6:]
    path = ''
    for part in path_parts:
        path += '/' + part
    resource_file = os.path.normpath('tests/resources/%s' %
                                     path)
    data_file = open(resource_file)
    data = json.load(data_file)
    # Must return a json-like object
    return data

class ClientTestCase(unittest.TestCase):
    """Test case for the client methods."""


    def setUp(self):
        self.client = tpm.TpmApiv4('https://tpm.example.com', username='USER', password='PASS')

    def test_request(self):
        """Test a list_projects."""
        with requests_mock.Mocker() as m:
            m.get(url, json=fake_data(url, 'post', data=''))
            response = self.client.list_projects()
        # number of projects is 5
        self.assertEqual(len(response), 5)

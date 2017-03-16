import os.path
import unittest
import json

import tpm
from mock import patch

class fake_req():
    links = []
    req = links

def fake_request(self, path, action, data=''):
    """
    A stub urlopen() implementation that load json responses from
    the filesystem.
    """
    self.req = fake_req
    # Map path from url to a file
    resource_file = os.path.normpath('tests/resources/%s' %
                                     path)
    data_file = open(resource_file)
    data = json.load(data_file)
    # Must return a json-like object
    return data


class ClientTestCase(unittest.TestCase):
    """Test case for the client methods."""

    def setUp(self):
        self.patcher = patch('tpm.TpmApiv4.request', fake_request)
        self.patcher.start()
        self.client = tpm.TpmApiv4('https://tpm.example.com', username='USER', password='PASS')

    def tearDown(self):
        self.patcher.stop()

    def test_request(self):
        """Test a list_projects."""
        response = self.client.list_projects()
        # number of projects is 5
        self.assertEqual(len(response), 5)

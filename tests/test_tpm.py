import requests
import requests_mock
import unittest
import os.path
import tpm
import json
import logging

log = logging.getLogger(__name__)

url_projects = 'https://tpm.example.com/index.php/api/v4/projects.json'

item_limit = 3

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

    def test_request(self):
        """Test a list_projects."""
        with requests_mock.Mocker() as m:
            fake_data(url_projects, m)
            response = self.client.list_projects()
        # number of projects is 5
        self.assertEqual(len(response), 5)

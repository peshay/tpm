import requests
import requests_mock
import unittest
import os.path
import tpm
import json
import logging

log = logging.getLogger(__name__)

url_projects = 'https://tpm.example.com/index.php/api/v4/projects.json'
url_getmore = 'https://tpm.example.com/index.php/api/v4/getmore'

nextdata = []
item_limit = 3

def fake_data(url, action, data):
    """
    A stub urlopen() implementation that load json responses from
    the filesystem.
    """
    global nextdata
    global url_getmore
    header = {}
    if url == url_getmore:
        data = nextdata
        log.debug("data is nextdata {0}".format(nextdata))
    else:
        # Map path from url to a file
        path_parts = url.split('/')[6:]
        path = '/'.join(path_parts)
        resource_file = os.path.normpath('tests/resources/%s' %
                                         path)
        data_file = open(resource_file)
        data = json.load(data_file)
    # Must return a json-like object
    if len(data) > item_limit:
        nextdata = data[item_limit:]
        data = data[:item_limit]
        header.update({ 'link': 'getmore; rel="next"', "value1": "crap2"})
    else:
        header.clear()
    log.debug("data to return: {0}".format(data))
    return data, header

class ClientTestCase(unittest.TestCase):
    """Test case for the client methods."""
    def setUp(self):
        self.client = tpm.TpmApiv4('https://tpm.example.com', username='USER', password='PASS')

    def test_request(self):
        """Test a list_projects."""
        with requests_mock.Mocker() as m:
            log.debug('mock url_projects')
            data_projects, header = fake_data(url_projects, 'post', data='')
            log.debug("the header: {}".format(header))
            m.get(url_projects, json=data_projects, headers=header)
            log.debug('mock url_getmore')
            log.debug("the header: {}".format(header))
            data_getmore, header = fake_data(url_getmore, 'post', data='')
            m.get(url_getmore, json=data_getmore, headers=header)
            response = self.client.list_projects()
        # number of projects is 5
        self.assertEqual(len(response), 5)

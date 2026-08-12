import hashlib
import hmac
import json
import logging
import os.path
import time
import unittest

import requests_mock

import tpm

log = logging.getLogger(__name__)

api_url = 'https://tpm.example.com/index.php/api/v5/'
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
        if data_len > item_limit and isinstance(data,list):
            returndata = data[:item_limit]
            returndata_txt = json.dumps(returndata)
            data = data[item_limit:]
            data_txt = json.dumps(data)
            pageingurl = url.replace('.json', f'/page/{count}.json')
            log.debug(f"Registering URL: {pageingurl}")
            log.debug(f"Registering data: {returndata_txt}")
            log.debug(f"Data length: {len(returndata)}")
            log.debug(f"Registering header: {header}")
            m.get(pageingurl.replace(" ", "+"), text=returndata_txt, headers=header.copy())
            m.post(pageingurl.replace(" ", "+"), text=returndata_txt, headers=header.copy())
            m.put(pageingurl.replace(" ", "+"), text=returndata_txt, headers=header.copy())
            header = { 'link': f'{pageingurl}; rel="next"'}
            data_len = len(data)
        else:
            log.debug(f"Registering URL: {url}")
            log.debug(f"Registering data: {data_txt}")
            log.debug(f"Registering header: {header}")
            m.get(url.replace(" ", "+"), text=data_txt, headers=header.copy())
            m.post(url.replace(" ", "+"), text=data_txt, headers=header.copy())
            m.put(url.replace(" ", "+"), text=data_txt, headers=header.copy())
            header.clear()
            break

class ClientProjectTestCase(unittest.TestCase):
    """Test cases for all project related queries."""
    client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')
    # get all retrievable sample data
    path_to_mock = 'projects.json'
    request_url = api_url + path_to_mock
    with requests_mock.Mocker() as m:
        fake_data(request_url, m)
        global Projects
        Projects = client.list_projects()

    def setUp(self):
        self.client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')

    def test_function_list_projects(self):
        """Test function list_projects."""
        path_to_mock = 'projects.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_projects()
        # number of passwords as from original json file.
        self.assertEqual(data, response)

    def test_function_list_projects_archived(self):
        """Test function list_projects_archived."""
        path_to_mock = 'projects/archived.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_projects_archived()
        # number of passwords as from original json file.
        self.assertEqual(data, response)

    def test_function_list_projects_favorite(self):
        """Test function list_projects_favorite."""
        path_to_mock = 'projects/favorite.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_projects_favorite()
        # number of passwords as from original json file.
        self.assertEqual(data, response)

    def test_function_list_projects_search(self):
        """Test function list_projects_search."""
        searches = ['company', 'internal', 'website', 'search with spaces']
        for search in searches:
            path_to_mock = f'projects/search/{search}.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.list_projects_search(search)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_function_show_project(self):
        """Test function show_project."""
        for project in Projects:
            project_id = project.get('id')
            log.debug(f"Testing with Project ID: {project_id}")
            path_to_mock = f'projects/{project_id}.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.show_project(project_id)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_function_list_passwords_of_project(self):
        """Test function list_passwords_of_project."""
        for project in Projects:
            project_id = project.get('id')
            log.debug(f"Testing with Project ID: {project_id}")
            path_to_mock = f'projects/{project_id}/passwords.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.list_passwords_of_project(project_id)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_function_list_user_access_on_project(self):
        """Test function list_user_access_on_project."""
        for project in Projects:
            project_id = project.get('id')
            log.debug(f"Testing with Project ID: {project_id}")
            path_to_mock = f'projects/{project_id}/security.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.list_user_access_on_project(project_id)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_function_create_project(self):
        """Test function create_project."""
        path_to_mock = 'projects.json'
        request_url = api_url + path_to_mock
        return_data = { "id": 4 }
        create_data = { "name": "someproject"}
        with requests_mock.Mocker() as m:
            m.post(request_url, json=return_data, status_code=200)
            response = self.client.create_project(create_data)
        self.assertEqual(response, return_data.get('id'))

    def test_function_update_project(self):
        """Test function update_project."""
        path_to_mock = 'projects/4.json'
        request_url = api_url + path_to_mock
        update_data = { "name": "someproject"}
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.update_project('4', update_data)
        self.assertEqual(response, None)

    def test_function_change_parent_of_project(self):
        """Test function change_parent_of_project."""
        path_to_mock = 'projects/4/change_parent.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.change_parent_of_project('4', '5')
        self.assertEqual(response, None)

    def test_function_update_security_of_project(self):
        """Test function update_security_of_project."""
        path_to_mock = 'projects/4/security.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.update_security_of_project('4', {'name': 'setdata'})
        self.assertEqual(response, None)

    def test_function_archive_project(self):
        """Test function archive_project."""
        path_to_mock = 'projects/4/archive.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.archive_project('4')
        self.assertEqual(response, None)

    def test_function_delete_project(self):
        """Test function delete_project."""
        path_to_mock = 'projects/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.delete(request_url, status_code=204)
            response = self.client.delete_project('4')
        self.assertEqual(response, None)

    def test_function_unarchive_project(self):
        """Test function unarchive_project."""
        path_to_mock = 'projects/4/unarchive.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.unarchive_project('4')
        self.assertEqual(response, None)

    def test_function_list_subprojects(self):
        """Test function list_subprojects."""
        for project in Projects:
            project_id = project.get('id')
            log.debug(f"Testing with Project ID: {project_id}")
            path_to_mock = f'projects/{project_id}/subprojects.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.list_subprojects(project_id)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_function_list_subprojects_action_new_pwd(self):
        """Test function list_subprojects_action_new_pwd."""
        action = 'new_pwd'
        for project in Projects:
            project_id = project.get('id')
            log.debug(f"Testing with Project ID: {project_id}")
            path_to_mock = f'projects/{project_id}/subprojects/{action}.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.list_subprojects_action(project_id, action)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

class ClientPasswordTestCase(unittest.TestCase):
    """Test cases for all password related queries."""
    client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')
    path_to_mock = 'passwords.json'
    request_url = api_url + path_to_mock
    with requests_mock.Mocker() as m:
        fake_data(request_url, m)
        global Passwords
        Passwords = client.list_passwords()

    def setUp(self):
        self.client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')

    def test_function_list_passwords(self):
        """Test function list_passwords."""
        path_to_mock = 'passwords.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = sorted(json.load(data_file), key=lambda k: k['id'])
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = sorted(self.client.list_passwords(), key=lambda k: k['id'])
        self.assertEqual(data, response)

    def test_function_list_passwords_archived(self):
        """Test function list_passwords_archived."""
        path_to_mock = 'passwords/archived.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = sorted(json.load(data_file), key=lambda k: k['id'])
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = sorted(self.client.list_passwords_archived(), key=lambda k: k['id'])
        self.assertEqual(data, response)

    def test_function_list_passwords_favorite(self):
        """Test function list_passwords_favorite."""
        path_to_mock = 'passwords/favorite.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = sorted(json.load(data_file), key=lambda k: k['id'])
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = sorted(self.client.list_passwords_favorite(), key=lambda k: k['id'])
        self.assertEqual(data, response)

    def test_function_list_passwords_search(self):
        """Test function list_passwords_search."""
        searches = ['backup', 'dns', 'facebook', 'firewall', 'reddit', 'test', 'search with spaces']
        for search in searches:
            path_to_mock = f'passwords/search/{search}.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.list_passwords_search(search)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_function_show_password(self):
        """Test function show_password."""
        for password in Passwords:
            password_id = password.get('id')
            log.debug(f"Testing with Password ID: {password_id}")
            path_to_mock = f'passwords/{password_id}.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.show_password(password_id)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_function_list_user_access_on_password(self):
        """Test function list_user_access_on_password."""
        for password in Passwords:
            password_id = password.get('id')
            log.debug(f"Testing with Password ID: {password_id}")
            path_to_mock = f'passwords/{password_id}/security.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.list_user_access_on_password(password_id)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_function_create_password(self):
        """Test function create_password."""
        path_to_mock = 'passwords.json'
        request_url = api_url + path_to_mock
        return_data = { "id": 4 }
        create_data = { "name": "someproject"}
        with requests_mock.Mocker() as m:
            m.post(request_url, json=return_data, status_code=200)
            response = self.client.create_password(create_data)
        self.assertEqual(response, return_data.get('id'))

    def test_function_update_password(self):
        """Test function update_password."""
        path_to_mock = 'passwords/4.json'
        request_url = api_url + path_to_mock
        update_data = { "name": "someproject"}
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.update_password('4', update_data)
        self.assertEqual(response, None)

    def test_function_update_security_of_password(self):
        """Test function update_security_of_password."""
        path_to_mock = 'passwords/4/security.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.update_security_of_password('4', {'name': 'setdata'})
        self.assertEqual(response, None)

    def test_function_update_custom_fields_of_password(self):
        """Test function update_custom_fields_of_password."""
        path_to_mock = 'passwords/4/custom_fields.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.update_custom_fields_of_password('4', {'name': 'setdata'})
        self.assertEqual(response, None)

    def test_function_delete_password(self):
        """Test function delete_password."""
        path_to_mock = 'passwords/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.delete(request_url, status_code=204)
            response = self.client.delete_password('4')
        self.assertEqual(response, None)

    def test_function_lock_password(self):
        """Test function lock_password."""
        path_to_mock = 'passwords/4/lock.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.lock_password('4')
        self.assertEqual(response, None)

    def test_function_unlock_password(self):
        """Test function unlock_password."""
        path_to_mock = 'passwords/4/unlock.json'
        request_url = api_url + path_to_mock
        unlock_reason = 'because I can'
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204, request_headers={'X-Unlock-Reason': unlock_reason})
            response = self.client.unlock_password('4', unlock_reason)
        self.assertEqual(response, None)

    def test_function_archive_password(self):
        """Test function archive_password."""
        path_to_mock = 'passwords/4/archive.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.archive_password('4')
        self.assertEqual(response, None)

    def test_function_unarchive_password(self):
        """Test function unarchive_password."""
        path_to_mock = 'passwords/4/unarchive.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.unarchive_password('4')
        self.assertEqual(response, None)

    def test_function_move_password(self):
        """Test function move_password."""
        path_to_mock = 'passwords/4/move.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.move_password('4', '5')
        self.assertEqual(response, None)

class ClientMyPasswordTestCase(unittest.TestCase):
    """Test cases for all mypassword related queries."""
    client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')
    path_to_mock = 'my_passwords.json'
    request_url = api_url + path_to_mock
    with requests_mock.Mocker() as m:
        fake_data(request_url, m)
        global MyPasswords
        MyPasswords = client.list_mypasswords()

    def setUp(self):
        self.client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')

    def test_function_list_mypasswords(self):
        """Test function list_mypasswords."""
        path_to_mock = 'my_passwords.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_mypasswords()
        # number of passwords as from original json file.
        self.assertEqual(data, response)

    def test_function_list_mypasswords_search(self):
        """Test function list_mypasswords_search."""
        searches = ['amazon', 'backup', 'facebook', 'john', 'jonny']
        for search in searches:
            path_to_mock = f'my_passwords/search/{search}.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.list_mypasswords_search(search)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_function_show_mypassword(self):
        """Test function show_mypassword."""
        for password in MyPasswords:
            password_id = password.get('id')
            log.debug(f"Testing with Password ID: {password_id}")
            path_to_mock = f'my_passwords/{password_id}.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.show_mypassword(password_id)
            # number of passwords as from original json file.
            self.assertEqual(data, response)

    def test_function_create_mypassword(self):
        """Test function create_mypassword."""
        path_to_mock = 'my_passwords.json'
        request_url = api_url + path_to_mock
        return_data = { "id": 4 }
        create_data = { "name": "someproject"}
        with requests_mock.Mocker() as m:
            m.post(request_url, json=return_data, status_code=200)
            response = self.client.create_mypassword(create_data)
        self.assertEqual(response, return_data.get('id'))

    def test_function_update_mypassword(self):
        """Test function update_mypassword."""
        path_to_mock = 'my_passwords/4.json'
        request_url = api_url + path_to_mock
        update_data = { "name": "someproject"}
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.update_mypassword('4', update_data)
        self.assertEqual(response, None)

    def test_function_delete_mypassword(self):
        """Test function delete_mypassword."""
        path_to_mock = 'my_passwords/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.delete(request_url, status_code=204)
            response = self.client.delete_mypassword('4')
        self.assertEqual(response, None)

    def test_function_set_favorite_password(self):
        """Test function set_favorite_password."""
        path_to_mock = 'favorite_passwords/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.post(request_url, status_code=204)
            response = self.client.set_favorite_password('4')
        self.assertEqual(response, None)

    def test_function_unset_favorite_password(self):
        """Test function unset_favorite_password."""
        path_to_mock = 'favorite_passwords/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.delete(request_url, status_code=204)
            response = self.client.unset_favorite_password('4')
        self.assertEqual(response, None)

    def test_function_set_favorite_project(self):
        """Test function set_favorite_project."""
        path_to_mock = 'favorite_project/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.post(request_url, status_code=204)
            response = self.client.set_favorite_project('4')
        self.assertEqual(response, None)

    def test_function_unset_favorite_project(self):
        """Test function unset_favorite_project."""
        path_to_mock = 'favorite_project/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.delete(request_url, status_code=204)
            response = self.client.unset_favorite_project('4')
        self.assertEqual(response, None)

    def test_function_move_mypassword(self):
        """Test function move_mypassword."""
        path_to_mock = 'my_passwords/4/move.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.move_mypassword('4', '5')
        self.assertEqual(response, data.get('id'))

class ClientUsersTestCase(unittest.TestCase):
    """Test cases for all user related queries."""
    client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')
    path_to_mock = 'users.json'
    request_url = api_url + path_to_mock
    with requests_mock.Mocker() as m:
        fake_data(request_url, m)
        global Users
        Users = client.list_users()

    def setUp(self):
        self.client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')

    def test_function_list_users(self):
        """Test function list_users."""
        path_to_mock = 'users.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_users()
        self.assertEqual(data, response)

    def test_function_show_user(self):
        """Test function show_user."""
        for user in Users:
            user_id = user.get('id')
            log.debug(f"Testing with Project ID: {user_id}")
            path_to_mock = f'users/{user_id}.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.show_user(user_id)
            self.assertEqual(data, response)

    def test_function_show_me(self):
        """Test function show_me."""
        path_to_mock = 'users/me.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.show_me()
            response2 = self.client.who_am_i()
        self.assertEqual(data, response)
        self.assertEqual(response2, response)

    def test_function_create_user(self):
        """Test function create_user."""
        path_to_mock = 'users.json'
        request_url = api_url + path_to_mock
        return_data = { "id": 4 }
        create_data = { "name": "someuser"}
        with requests_mock.Mocker() as m:
            m.post(request_url, json=return_data, status_code=200)
            response = self.client.create_user(create_data)
        self.assertEqual(response, return_data.get('id'))

    def test_function_create_user_ldap(self):
        """Test function create_user_ldap."""
        path_to_mock = 'users_ldap.json'
        request_url = api_url + path_to_mock
        return_data = { "id": 4 }
        create_data = { "name": "someuser"}
        with requests_mock.Mocker() as m:
            m.post(request_url, json=return_data, status_code=200)
            response = self.client.create_user_ldap(create_data)
        self.assertEqual(response, return_data.get('id'))

    def test_function_create_user_saml(self):
        """Test function create_user_saml."""
        path_to_mock = 'users_saml.json'
        request_url = api_url + path_to_mock
        return_data = { "id": 4 }
        create_data = { "name": "someuser"}
        with requests_mock.Mocker() as m:
            m.post(request_url, json=return_data, status_code=200)
            response = self.client.create_user_saml(create_data)
        self.assertEqual(response, return_data.get('id'))

    def test_function_update_user(self):
        """Test function update_user."""
        path_to_mock = 'users/4.json'
        request_url = api_url + path_to_mock
        update_data = { "name": "someuser"}
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.update_user('4', update_data)
        self.assertEqual(response, None)

    def test_function_change_user_password(self):
        """Test function change_user_password."""
        path_to_mock = 'users/4/change_password.json'
        request_url = api_url + path_to_mock
        update_data = { "password": "NewSecret"}
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.change_user_password('4', update_data)
        self.assertEqual(response, None)

    def test_function_activate_user(self):
        """Test function activate_user."""
        path_to_mock = 'users/4/activate.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.activate_user('4')
        self.assertEqual(response, None)

    def test_function_deactivate_user(self):
        """Test function deactivate_user."""
        path_to_mock = 'users/4/deactivate.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.deactivate_user('4')
        self.assertEqual(response, None)

    def test_function_convert_user_to_ldap(self):
        """Test function convert_user_to_ldap."""
        path_to_mock = 'users/4/convert_to_ldap.json'
        request_url = api_url + path_to_mock
        login_dn = 'CN=Jane,CN=Users,DC=tpm,DC=local'
        server_id = "1"
        def match_request_text(request):
            return {"login_dn": login_dn, "ldap_server_id": server_id}
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204, additional_matcher=match_request_text)
            response = self.client.convert_user_to_ldap('4', login_dn, server_id)
        self.assertEqual(response, None)

    def test_function_convert_user_to_saml(self):
        """Test function convert_user_to_saml."""
        path_to_mock = 'users/4/convert_to_saml.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.convert_user_to_saml('4')
        self.assertEqual(response, None)

    def test_function_convert_ldap_user_to_normal(self):
        """Test function convert_ldap_user_to_normal."""
        path_to_mock = 'users/4/convert_to_normal.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.convert_ldap_user_to_normal('4')
        self.assertEqual(response, None)

    def test_function_delete_user(self):
        """Test function delete_user."""
        path_to_mock = 'users/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.delete(request_url, status_code=204)
            response = self.client.delete_user('4')
        self.assertEqual(response, None)

class ClientGroupsTestCase(unittest.TestCase):
    """Test cases for all group related queries."""
    client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')
    path_to_mock = 'groups.json'
    request_url = api_url + path_to_mock
    with requests_mock.Mocker() as m:
        fake_data(request_url, m)
        global Groups
        Groups = client.list_groups()

    def setUp(self):
        self.client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')

    def test_function_list_groups(self):
        """Test function list_groups."""
        path_to_mock = 'groups.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_groups()
        self.assertEqual(data, response)

    def test_function_show_group(self):
        """Test function show_group."""
        for group in Groups:
            group_id = group.get('id')
            log.debug(f"Testing with Project ID: {group_id}")
            path_to_mock = f'groups/{group_id}.json'
            request_url = api_url + path_to_mock
            request_path = local_path + path_to_mock
            resource_file = os.path.normpath(request_path)
            with open(resource_file) as data_file:
                data = json.load(data_file)
            with requests_mock.Mocker() as m:
                fake_data(request_url, m)
                response = self.client.show_group(group_id)
            self.assertEqual(data, response)

    def test_function_create_group(self):
        """Test function create_group."""
        path_to_mock = 'groups.json'
        request_url = api_url + path_to_mock
        return_data = { "id": 4 }
        create_data = { "name": "somegroup"}
        with requests_mock.Mocker() as m:
            m.post(request_url, json=return_data, status_code=200)
            response = self.client.create_group(create_data)
        self.assertEqual(response, return_data.get('id'))

    def test_function_update_group(self):
        """Test function update_group."""
        path_to_mock = 'groups/4.json'
        request_url = api_url + path_to_mock
        update_data = { "name": "somegroup"}
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.update_group('4', update_data)
        self.assertEqual(response, None)

    def test_function_add_user_to_group(self):
        """Test function add_user_to_group."""
        group_id = '3'
        user_id = '4'
        path_to_mock = f'groups/{group_id}/add_user/{user_id}.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.add_user_to_group(group_id, user_id)
        self.assertEqual(response, None)

    def test_function_delete_user_from_group(self):
        """Test function delete_user_from_group."""
        group_id = '3'
        user_id = '4'
        path_to_mock = f'groups/{group_id}/delete_user/{user_id}.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.delete_user_from_group(group_id, user_id)
        self.assertEqual(response, None)

    def test_function_delete_group(self):
        """Test function delete_group."""
        path_to_mock = 'groups/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.delete(request_url, status_code=204)
            response = self.client.delete_group('4')
        self.assertEqual(response, None)

class GeneralClientTestCases(unittest.TestCase):
    """general test cases for client queries."""
    def setUp(self):
        self.client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')

    def test_paging(self):
        """Test paging, if number of items is same as from original data source."""
        path_to_mock = 'passwords.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_passwords()
        # number of passwords as from original json file.
        source_items = len(data)
        paging_count = round((source_items / 20) + 0.5)
        response_items = len(response)
        log.debug(f"Paging should be {paging_count}")
        log.debug(f"Paged {m.call_count} times")
        log.debug(f"Source Items: {source_items}; Response Items: {response_items}")
        self.assertEqual(paging_count, m.call_count)
        self.assertEqual(source_items, response_items)

    def test_provide_unlock_reason(self):
        """Test providing an unlock reason."""
        path_to_mock = 'passwords/14.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            json.load(data_file)
        unlock_reason = 'because I can'
        client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS', unlock_reason=unlock_reason)
        with requests_mock.Mocker() as m:
            m.get(request_url, request_headers={'X-Unlock-Reason': unlock_reason})
            client.show_password('14')
            history = m.request_history
            request_unlock_reason = history[0].headers.get('X-Unlock-Reason')
        self.assertEqual(request_unlock_reason, unlock_reason)

    def test_key_authentciation(self):
        """Test Key authentication header."""
        private_key='private_secret'
        public_key='public_secret'
        client = tpm.TpmApiv5('https://tpm.example.com', private_key=private_key, public_key=public_key)
        path_to_mock = 'version.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            client.get_version()
            history = m.request_history
        request_hash = history[0].headers.get('X-Request-Hash')
        history[0].headers.get('X-Public-Key')
        request_timestamp = history[0].headers.get('X-Request-Timestamp')
        str(int(time.time()))
        unhashed = 'api/v5/' + path_to_mock + request_timestamp
        hashed = hmac.new(str.encode(private_key),
                             msg=unhashed.encode('utf-8'),
                             digestmod=hashlib.sha256).hexdigest()
        self.assertEqual(request_hash, hashed)

    def test_function_generate_password(self):
        """Test function generate_password."""
        path_to_mock = 'generate_password.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.generate_password()
        self.assertEqual(data, response)

    def test_get_version(self):
        """Test function get_version."""
        path_to_mock = 'version.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.get_version()
        self.assertEqual(data, response)

    def test_a_call_with_v3(self):
        """Test function get_version with v3 API."""
        path_to_mock = 'version.json'
        request_url = 'https://tpm.example.com/index.php/api/v3/' + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        client = tpm.TpmApiv3('https://tpm.example.com', username='USER', password='PASS')
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = client.get_version()
        self.assertEqual(data, response)

    def test_function_check_latest(self):
        """Test function generate_password."""
        path_to_mock = 'version/check_latest.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.get_latest_version()
        self.assertEqual(data, response)

    def test_function_up_to_date_true(self):
        """Test function up_to_date is true."""
        path_to_mock = 'version/check_latest.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response_up_to_date_true = self.client.up_to_date()
            self.assertTrue(response_up_to_date_true)

    def test_function_up_to_date_false(self):
        """Test function up_to_date is false."""
        path_to_mock = 'version/check_latest.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            fake_data(request_url, m, 'version/check_outdated.json')
            response_up_to_date_false = self.client.up_to_date()
            self.assertFalse(response_up_to_date_false)


class ExceptionTestCases(unittest.TestCase):
    """Test case for Config Exceptions."""
    def test_wrong_auth_exception1(self):
        """Exception if wrong authentication mehtod with username but private_key."""
        with self.assertRaises(tpm.TpmApi.ConfigError) as context:
            tpm.TpmApiv5('https://tpm.example.com', username='USER', private_key='PASS')
        log.debug(f"context exception: {context.exception}")
        self.assertEqual("'No authentication specified (user/password or private/public key)'", str(context.exception))

    def test_wrong_auth_exception2(self):
        """Exception if wrong authentication mehtod with public key but password."""
        with self.assertRaises(tpm.TpmApi.ConfigError) as context:
            tpm.TpmApiv5('https://tpm.example.com', public_key='USER', password='PASS')
        log.debug(f"context exception: {context.exception}")
        self.assertEqual("'No authentication specified (user/password or private/public key)'", str(context.exception))

    def test_wrong_auth_exception3(self):
        """Exception if wrong authentication mehtod with username but public_key."""
        with self.assertRaises(tpm.TpmApi.ConfigError) as context:
            tpm.TpmApiv5('https://tpm.example.com', username='USER', public_key='PASS')
        log.debug(f"context exception: {context.exception}")
        self.assertEqual("'No authentication specified (user/password or private/public key)'", str(context.exception))

    def test_wrong_auth_exception4(self):
        """Exception if wrong authentication mehtod with private key but password."""
        with self.assertRaises(tpm.TpmApi.ConfigError) as context:
            tpm.TpmApiv5('https://tpm.example.com', private_key='USER', password='PASS')
        log.debug(f"context exception: {context.exception}")
        self.assertEqual("'No authentication specified (user/password or private/public key)'", str(context.exception))

    def test_wrong_url_exception(self):
        """Exception if URL does not match REGEXurl."""
        wrong_url = 'ftp://tpm.example.com'
        with self.assertRaises(tpm.TpmApiv5.ConfigError) as context:
            tpm.TpmApiv5(wrong_url, username='USER', password='PASS')
        log.debug(f"context exception: {context.exception}")
        self.assertEqual(f"'Invalid URL: {wrong_url}'", str(context.exception))

class ExceptionOnRequestsTestCases(unittest.TestCase):
    """Test case for Request based Exceptions."""
    def setUp(self):
        self.client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')

    def test_connection_exception(self):
        """Exception if connection fails."""
        exception_error = "Connection error for "
        with self.assertRaises(tpm.TPMException) as context:
            self.client.list_passwords()
        log.debug(f"context exception: {context.exception}")
        self.assertTrue(exception_error in str(context.exception))

    def test_value_error_exception(self):
        """Exception if value is not json format."""
        path_to_mock = 'passwords/value_error.json'
        request_url = api_url + path_to_mock
        exception_error = "No JSON object could be decoded: "
        exception_error3 = "Expecting value: line 1 column 1 (char 0): "
        resource_file = os.path.normpath(f'tests/resources/{path_to_mock}')
        # str() of the open handle is deliberately not valid JSON, which is
        # what makes the response body fail to decode at position 0.
        with open(resource_file) as data, \
                self.assertRaises(ValueError) as context, \
                requests_mock.Mocker() as m:
            m.get(request_url, text=str(data))
            self.client.show_password('value_error')
        log.debug(f"context exception: {context.exception}")
        self.assertTrue(str(context.exception).startswith(exception_error) or str(context.exception).startswith(exception_error3))

    def test_exception_on_error_in_result(self):
        """Exception if "error" found in result."""
        exception_error = 'something bad happened'
        error_json={'error': 'not good', 'message': exception_error}
        path_to_mock = 'passwords/json_error.json'
        request_url = api_url + path_to_mock
        with self.assertRaises(tpm.TPMException) as context, requests_mock.Mocker() as m:
            m.get(request_url, json=error_json)
            self.client.show_password('json_error')
        log.debug(f"context exception: {context.exception}")
        self.assertTrue(exception_error in str(context.exception))

    def test_exception_on_403(self):
        """Exception if 403 forbidden."""
        path_to_mock = 'passwords.json'
        request_url = api_url + path_to_mock
        exception_error = f"{request_url} forbidden"
        with self.assertRaises(tpm.TPMException) as context, requests_mock.Mocker() as m:
            m.get(request_url, text='forbidden', status_code=403)
            self.client.list_passwords()
        log.debug(f"context exception: {context.exception}")
        self.assertTrue(exception_error in str(context.exception))

    def test_exception_on_404(self):
        """Exception if 404 not found."""
        path_to_mock = 'passwords.json'
        request_url = api_url + path_to_mock
        exception_error = f"{request_url} not found"
        with self.assertRaises(tpm.TPMException) as context, requests_mock.Mocker() as m:
            m.get(request_url, text='not found', status_code=404)
            self.client.list_passwords()
        log.debug(f"context exception: {context.exception}")
        self.assertTrue(exception_error in str(context.exception))

    def test_exception_on_405(self):
        """Exception if 405 Method Not Allowed."""
        path_to_mock = 'passwords.json'
        request_url = api_url + path_to_mock
        exception_error = f"{request_url} Method Not Allowed"
        with self.assertRaises(ValueError) as context, requests_mock.Mocker() as m:
            m.get(request_url, text='Method Not Allowed', status_code=405)
            self.client.list_passwords()
        log.debug(f"context exception: {context.exception}")
        self.assertTrue(str(context.exception).endswith(exception_error))

class ClientFilesTestCase(unittest.TestCase):
    """Test cases for all file related queries."""
    client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')

    def setUp(self):
        self.client = tpm.TpmApiv5('https://tpm.example.com', username='USER', password='PASS')

    def test_function_list_password_files(self):
        """NEW v5: Test function list_password_files."""
        path_to_mock = 'passwords/14/files.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_password_files('14')
            history = m.request_history
            log.debug(f"response: {history[0].url}")
        self.assertEqual(data, response)

    def test_function_upload_password(self):
        """NEW v5: Upload a file to password."""
        path_to_mock = 'passwords/14/upload.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.upload_password_file('14', request_path, notes="some notes")
        self.assertEqual(response, data.get('id'))

    def test_function_list_project_files(self):
        """NEW v5: Test function list_project_files."""
        path_to_mock = 'projects/4/files.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.list_project_files('4')
        # file list as from original json file.
        self.assertEqual(data, response)

    def test_function_upload_project(self):
        """NEW v5: Upload a file to project."""
        path_to_mock = 'projects/4/upload.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.upload_project_file('4', request_path, notes="some notes")
        self.assertEqual(response, data.get('id'))

    def test_function_show_file_info(self):
        """NEW v5: Show info of a file."""
        path_to_mock = 'files/4.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.show_file_info('4')
        # file list as from original json file.
        self.assertEqual(data, response)

    def test_function_update_file_notes(self):
        """NEW v5: Update notes on a file."""
        path_to_mock = 'files/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.put(request_url, status_code=204)
            response = self.client.update_file_notes('4', "new notes")
        self.assertEqual(response, None)

    def test_function_max_upload_file_size(self):
        """NEW v5: Test function max_upload_file_size."""
        path_to_mock = 'files/max_upload_file_size.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.max_upload_file_size()
        self.assertEqual(data, response)

    def test_function_uploads_folder_info(self):
        """NEW v5: Test function uploads_folder_info."""
        path_to_mock = 'files/uploads_folder_info.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.uploads_folder_info()
        self.assertEqual(data, response)

    def test_function_download_file(self):
        """NEW v5: Test function download_file."""
        path_to_mock = 'files/download/4.json'
        request_url = api_url + path_to_mock
        request_path = local_path + path_to_mock
        resource_file = os.path.normpath(request_path)
        with open(resource_file) as data_file:
            data = json.load(data_file)
        with requests_mock.Mocker() as m:
            fake_data(request_url, m)
            response = self.client.download_file("4")
        self.assertEqual(data, response)

    def test_function_delete_file(self):
        """NEW v5: Test function delete_file."""
        path_to_mock = 'files/4.json'
        request_url = api_url + path_to_mock
        with requests_mock.Mocker() as m:
            m.delete(request_url, status_code=204)
            response = self.client.delete_file('4')
        self.assertEqual(response, None)
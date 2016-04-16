# ===============================================================================
# Copyright 2015 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
import base64
import json
import urllib2

import requests
from datetime import datetime


# ============= local library imports  ==========================


def get_branches(new):
    cmd = 'https://api.github.com/repos/{}/branches'.format(new)
    doc = urllib2.urlopen(cmd)
    return [branch['name'] for branch in json.load(doc)]


GITHUB_API_URL = 'https://api.github.com'


def make_request(r):
    return '{}{}'.format(GITHUB_API_URL, r)


def get_organization_repositiories(name):
    cmd = '/orgs/{}/repos'.format(name)
    cmd = make_request(cmd)
    doc = requests.get(cmd)
    return [repo['name'] for repo in json.loads(doc.text)]


def create_organization_repository(org, name, usr, pwd, **kw):
    cmd = '/orgs/{}/repos'.format(org)
    cmd = make_request(cmd)
    payload = {'name': name}
    payload.update(**kw)
    auth = base64.encodestring('{}:{}'.format(usr, pwd)).replace('\n', '')
    headers = {"Authorization": "Basic {}".format(auth)}
    r = requests.post(cmd, data=json.dumps(payload), headers=headers)
    print cmd, payload, usr, pwd
    print r
    return r


class GithubObject(object):
    def __init__(self, usr='', pwd=''):
        self._pwd = pwd
        self._usr = usr

    def _make_headers(self, auth=True):
        headers = {}
        if auth:
            auth = base64.encodestring('{}:{}'.format(self._usr, self._pwd)).replace('\n', '')
            headers['Authorization'] = 'Basic {}'.format(auth)
        return headers

    def _process_post(self, po):
        pass


class RepositoryRecord:
    pass


class Organization(GithubObject):
    def __init__(self, name, *args, **kw):
        self._name = name
        super(Organization, self).__init__(*args, **kw)

    @property
    def base_cmd(self):
        return '/orgs/{}'.format(self._name)

    @property
    def repo_names(self):
        return [repo['name'] for repo in self.get_repos()]

    @property
    def info(self):
        cmd = make_request(self.base_cmd)
        doc = requests.get(cmd)
        return json.loads(doc.text)

    def repos(self, attributes):
        return [self._repo_factory(ri, attributes) for ri in self.get_repos()]

    def get_repos(self):
        cmd = make_request('{}/repos'.format(self.base_cmd))
        doc = requests.get(cmd)
        return json.loads(doc.text)

    def has_repo(self, name):
        return name in self.repo_names

    def create_repo(self, name, usr, pwd, **payload):
        return create_organization_repository(self._name, name, usr, pwd, **payload)
        # cmd = make_request(self.base_cmd)
        # payload['name'] = name
        #
        # headers = self._make_headers(auth=True)
        # r = requests.post(cmd, data=json.dumps(payload), headers=headers)
        # self._process_post(r)

    def _repo_factory(self, ri, attributes):
        repo = RepositoryRecord()
        date_attrs = ('pushed_at', 'created_at')
        for ai in attributes:
            v = ri[ai]
            if ai in date_attrs:
                date = datetime.strptime(v, '%Y-%m-%dT%H:%M:%SZ')
                v = date.strftime('%m-%d-%Y %H:%M')
            setattr(repo, ai, v)
        return repo


if __name__ == '__main__':
    with open('/Users/ross/Programming/githubauth.txt') as rfile:
        usr = rfile.readline().strip()
        pwd = rfile.readline().strip()
    # print get_organization_repositiories('NMGRL')
    org = Organization('NMGRLData', usr, pwd)
    print org.repo_names, len(org.repo_names)
    # print org.create_repo('test2', auto_init=True)
    # print org.repos, len(org.repos)
# ============= EOF =============================================

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
import base64
import json
import os
import urllib2
# ============= standard library imports ========================
# ============= local library imports  ==========================
import requests


def get_branches(new):
    cmd = 'https://api.github.com/repos/{}/branches'.format(new)
    doc = urllib2.urlopen(cmd)
    return [branch['name'] for branch in json.load(doc)]


BASE_URL = 'https://api.github.com'


def make_request(r):
    return '{}{}'.format(BASE_URL, r)


def make_auth(usr, pwd):
    auth = base64.encodestring('{}:{}'.format(usr, pwd)).replace('\n', '')
    headers = {"Authorization": "Basic {}".format(auth)}
    return headers


def get_organization_repositiories(name):
    cmd = '/orgs/{}/repos'.format(name)
    cmd = make_request(cmd)
    doc = requests.get(cmd)
    return [repo['name'] for repo in json.loads(doc.text)]


def create_organization_repository(org, name, usr, pwd):
    cmd = '/orgs/{}/repos'.format(org)
    cmd = make_request(cmd)
    payload = {'name': name}
    headers = make_auth(usr, pwd)
    r = requests.post(cmd, data=json.dumps(payload), headers=headers)
    print r.text


def list_collaborators(owner, repo, usr, pwd):
    cmd = '/repos/{}/{}/collaborators'
    cmd = cmd.format(owner, repo)
    cmd = make_request(cmd)
    headers = make_auth(usr, pwd)
    r = requests.get(cmd, headers=headers)
    return json.loads(r.text)


class GithubObject(object):
    def __init__(self, usr=None, pwd=None):
        if usr is None:
            usr = os.environ.get('GITHUB_USR')
        if pwd is None:
            pwd = os.environ.get('GITHUB_PWD')
        self._pwd = pwd
        self._usr = usr

    # def _make_headers(self, auth=True):
    #     headers = {}
    #     if auth:
    #         auth = base64.encodestring('{}:{}'.format(self._usr, self._pwd)).replace('\n', '')
    #         headers['Authorization'] = 'Basic {}'.format(auth)
    #     return headers

    def _process_post(self, po):
        pass

    def _make_auth(self):
        return make_auth(self._usr, self._pwd)


class Organization(GithubObject):
    def __init__(self, name, *args, **kw):
        super(Organization, self).__init__(*args, **kw)
        self._name = name

    @property
    def repos(self):
        cmd = make_request('/orgs/{}/repos'.format(self._name))
        doc = requests.get(cmd)
        return [repo['name'] for repo in json.loads(doc.text)]

    @property
    def teams(self):
        cmd = '/orgs/{}/teams'.format(self._name)
        cmd = make_request(cmd)
        headers = self._make_auth()
        doc = requests.get(cmd, headers=headers)
        return [Team(ti) for ti in json.loads(doc.text)]

    def add_team_to_repository(self, team_name, repo, permission='push'):
        cmd = '/teams/{}/repos/{}/{}'

        team_id = self._get_team_id(team_name)

        cmd = cmd.format(team_id, self._name, repo)
        cmd = make_request(cmd)

        headers = self._make_auth()
        headers['Accept'] = 'application/vnd.github.ironman-preview+json'
        payload = {'permission': permission}
        r = requests.put(cmd, data=json.dumps(payload), headers=headers)
        print r.text

    def create_repo(self, name, **payload):

        cmd = make_request('/orgs/{}/repos'.format(self._name))
        payload['name'] = name

        headers = self._make_auth()
        r = requests.post(cmd, data=json.dumps(payload), headers=headers)
        self._process_post(r)

    def _get_team_id(self, name):
        return next((team.id for team in self.teams if team.name == name), None)


class Team:
    def __init__(self, ti):
        self.id = ti['id']
        self.name = ti['name']


if __name__ == '__main__':
    # print get_organization_repositiories('NMGRL')
    # org = Organization('NMGRL', '', '')
    # print org.repos, len(org.repos)
    # print org.create_repo('test2', auto_init=True)
    # print org.repos, len(org.repos)

    org = 'NMGRLData'
    repo = 'Irradiation-NM-273'

    organ = Organization(org)
    organ.add_team_to_repository('Users', repo)

    # print add_team_to_repository('Users', org, repo, usr, pwd)
    #
    # cs = list_collaborators('NMGRLData', repo, usr, pwd)
    # for ci in cs:
    #     print ci['login']
# ============= EOF =============================================

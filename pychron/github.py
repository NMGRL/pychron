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

# ============= standard library imports ========================
from __future__ import absolute_import
from __future__ import print_function

import base64

import requests

# ============= local library imports  ==========================
from pychron import json
from pychron.core.helpers.datetime_tools import format_iso_datetime
from pychron.globals import globalv

GITHUB_API_URL = "https://api.github.com"


def make_request(r):
    return "{}{}".format(GITHUB_API_URL, r)


def get_list(cmd, attr="name", headers=None):
    if headers is None:
        headers = {}

    cmd = make_request(cmd)

    with requests.Session() as s:

        def _rget(ci):
            r = s.get(ci, headers=headers, verify=globalv.cert_file)

            result = r.json()
            if attr:
                result = [di[attr] for di in result]

            try:
                dd = _rget(r.links["next"]["url"])
            except KeyError:
                return result

            if attr:
                try:
                    dd = [di[attr] for di in dd]
                except TypeError:
                    pass

            result.extend(dd)
            return result

    return _rget(cmd)

    # return [item[attr] for item in json.loads(doc.text)]


def get_branches(name):
    cmd = "/repos/{}/branches".format(name)
    return get_list(cmd)


def get_tags(name):
    cmd = "/repos/{}/tags".format(name)
    return get_list(cmd)


def get_organization_repositiories(name, attr="name"):
    cmd = "/orgs/{}/repos".format(name)
    return get_list(cmd, attr=attr)


# def create_organization_repository(org, name, usr, pwd, **kw):
#     cmd = "/orgs/{}/repos".format(org)
#     cmd = make_request(cmd)
#     payload = {"name": name}
#     payload.update(**kw)
#     auth = base64.encodestring("{}:{}".format(usr, pwd)).replace("\n", "")
#     headers = {"Authorization": "Basic {}".format(auth)}
#     r = requests.post(cmd, data=json.dumps(payload), headers=headers)
#     print(cmd, payload, usr, pwd)
#     print(r)
#     return r


class GithubObject(object):
    def __init__(self, usr="", pwd="", oauth_token=None):
        self._pwd = pwd
        self._usr = usr
        self._oauth_token = oauth_token

    def _make_headers(self, auth=True):
        headers = {}
        if auth:
            if self._oauth_token:
                auth = "token {}".format(self._oauth_token)
            else:
                auth = base64.encodestring(
                    "{}:{}".format(self._usr, self._pwd)
                ).replace("\n", "")
                auth = "Basic {}".format(auth)
            headers["Authorization"] = auth
        print(headers)
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
        return "/orgs/{}".format(self._name)

    @property
    def repo_names(self):
        return sorted([repo["name"] for repo in self.get_repos()])

    @property
    def info(self):
        cmd = make_request(self.base_cmd)
        doc = requests.get(cmd)
        return json.loads(doc.text)

    def repos(self, attributes):
        return [self._repo_factory(ri, attributes) for ri in self.get_repos()]

    def get_repos(self):
        cmd = "/orgs/{}/repos".format(self._name)
        r = get_list(cmd, attr=None, headers=self._make_headers())

        # r = get_organization_repositiories(self._name, attr=None)
        if not isinstance(r, list):
            r = []
        return r

    def has_repo(self, name):
        return name in self.repo_names

    # def create_repo(self, name, usr, pwd, **payload):
    #    return create_organization_repository(self._name, name, usr, pwd, **payload)
    # cmd = make_request(self.base_cmd)
    # payload['name'] = name
    #
    # headers = self._make_headers(auth=True)
    # r = requests.post(cmd, data=json.dumps(payload), headers=headers)
    # self._process_post(r)

    def _repo_factory(self, ri, attributes):
        repo = RepositoryRecord()
        date_attrs = ("pushed_at", "created_at")
        for ai in attributes:
            v = ri[ai]
            if ai in date_attrs:
                v = format_iso_datetime(ai)
            setattr(repo, ai, v)
        return repo


if __name__ == "__main__":
    with open("/Users/ross/Programming/githubauth.txt") as rfile:
        usr = rfile.readline().strip()
        pwd = rfile.readline().strip()
    # print get_organization_repositiories('NMGRL')
    org = Organization("NMGRLData", usr, pwd)
    print(org.repo_names, len(org.repo_names))
    # print org.create_repo('test2', auto_init=True)
    # print org.repos, len(org.repos)
# ============= EOF =============================================

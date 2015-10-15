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
from traits.api import HasTraits, Str, List
from traitsui.api import View, UItem, Item, HGroup, VGroup, CheckListEditor, Controller, TextEditor
from traitsui.menu import Action
import traits.trait_notifiers
from pyface.message_dialog import warning
# ============= standard library imports ========================
import keyring as keyring
import base64
import json
import requests
import logging
import traceback
import sys
import os
import pickle
# ============= local library imports  ==========================
from pychron.github import GITHUB_API_URL
from pychron.paths import paths

LABELS = ['Bug',
          'Enhancement',
          'Question',
          'DataReduction',
          'DataCollection',
          'DiodeLaser',
          'CO2Laser',
          'UVLaser',
          'ExtactionLine',
          'DataEntry',
          'Laser',
          'Spectrometer',
          'ExperimentWriting',
          'Browser',
          'Loading',
          'PyScripts',
          'NoActionRequired',
          'Recall',
          'LabBook',
          'Priority',
          'UI']

SubmitAction = Action(name='Submit', action='submit')


def submit_issue_github():
    pass


def submit_issue_offline():
    pass


def check_github_access():
    try:
        r = requests.get(GITHUB_API_URL)
        return r.status_code == 200
    except requests.ConnectionError:
        pass


class NoPasswordException(BaseException):
    pass


def report_issues():
    if not check_github_access():
        return

    p = os.path.join(paths.hidden_dir, 'issues.p')
    if os.path.isfile(p):
        nonreported = []
        with open(p, 'r') as rfile:
            issues = pickle.load(rfile)

            warn_no_password = False
            for issue in issues:
                result = create_issue(issue)

                if not result:
                    nonreported.append(issue)

        if nonreported:
            with open(p, 'w') as wfile:
                pickle.dump(nonreported, wfile)
        else:
            os.remove(p)


def create_issue(issue):
    org = os.environ.get('GITHUB_ORGANIZATION', 'NMGRL')
    cmd = '{}/repos/{}/pychron/issues'.format(GITHUB_API_URL, org)

    usr = os.environ.get('GITHUB_USER')
    pwd = keyring.get_password('github', usr)
    if pwd is None:
        pwd = os.environ.get('GITHUB_PASSWORD')

    if not pwd:
        warning(None, 'No password set for "{}". Contact Developer.\n'
                      'Pychron will quit when this window is closed'.format(usr))
        sys.exit()

    auth = base64.encodestring('{}:{}'.format(usr, pwd)).replace('\n', '')
    headers = {"Authorization": "Basic {}".format(auth)}

    r = requests.post(cmd, data=json.dumps(issue), headers=headers)
    return r.status_code == 201


class ExceptionModel(HasTraits):
    title = Str
    description = Str
    labels = List
    exctext = Str

    helpstr = Str("""<p align="center"><br/> <font size="14" color="red"><b>There was a Pychron error<br/>
Please consider submitting a bug report to the developer</b></font><br/>
Enter a <b>Title</b>, select a few <b>Labels</b> and add a <b>Description</b> of the bug. Then click <b>Submit</b><br/></p>""")


class ExceptionHandler(Controller):
    def submit(self, info):
        if not self.submit_issue_github():
            self.submit_issue_offline()

        info.ui.dispose()

    def submit_issue_github(self):
        issue = self._make_issue()
        return create_issue(issue)

    def submit_issue_offline(self):
        p = os.path.join(paths.hidden_dir, 'issues.p')
        if not os.path.isfile(p):
            issues = []
        else:
            with open(p, 'r') as rfile:
                issues = pickle.load(rfile)

        issue = self._make_issue()

        issues.append(issue)
        with open(p, 'w') as wfile:
            pickle.dump(issues, wfile)

    def _make_issue(self):
        m = self.model
        issue = {'title': m.title,
                 'labels': m.labels,
                 'body': self._make_body()}
        return issue

    def _make_body(self):
        m = self.model
        return '{}\n\n```\n{}\n```'.format(m.description, m.exctext)

    def traits_view(self):
        v = View(VGroup(
            UItem('helpstr',
                  style='readonly'),
            Item('title'),
                        HGroup(
                            VGroup(UItem('labels', style='custom', editor=CheckListEditor(values=LABELS)),
                                   show_border=True, label='Labels (optional)'),
                            VGroup(UItem('description', style='custom'), show_border=True, label='Description (optional)')),
                        UItem('exctext',
                              style='custom',
                              editor=TextEditor(read_only=True))),
                 title='Exception',
                 buttons=[SubmitAction, 'Cancel'])

        return v


def except_handler(exctype, value, tb):
    if exctype == RuntimeError:
        warning(None, 'RunTimeError: {}'.format(value))
    elif value == "'NoneType' object has no attribute 'text'":
        pass
    else:
        lines = traceback.format_exception(exctype, value, tb)
        if not exctype == KeyboardInterrupt:
            em = ExceptionModel(exctext=''.join(lines),
                                labels=['Bug'])
            ed = ExceptionHandler(model=em)
            ed.edit_traits()

        root = logging.getLogger()
        root.critical('============ Exception ==============')
        for ti in lines:
            ti = ti.strip()
            if ti:
                root.critical(ti)
        root.critical('============ End Exception ==========')


def traits_except_handler(obj, name, old, new):
    except_handler(*sys.exc_info())


def set_exception_handler(func=None):
    """
        set sys.excepthook to func.  if func is None use a default handler

        default handler formats and logs the traceback as critical and calls sys.__excepthook__
        for normal exception handling

    :return:
    """

    sys.excepthook = except_handler
    traits.trait_notifiers.handle_exception = traits_except_handler


if __name__ == '__main__':
    # em = ExceptionModel()
    # e = ExceptionHandler(model=em)
    # e.configure_traits()
    # print check_github_access()
    # print keyring.get_password('github', 'foo')
    # print keyring.get_password('github', 'foob')
    pass
# ============= EOF =============================================

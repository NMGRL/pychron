#===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================



#============= enthought library imports =======================
from traits.api import Str, Enum, Bool, String
from traitsui.api import View, Item, HGroup, spring, \
    Handler, VGroup, HTMLEditor, CodeEditor
from pyface.wx.dialog import confirmation
#============= standard library imports ========================
import os
from wx import stc

#============= local library imports  ==========================
from pychron.managers.manager import Manager
from traitsui.menu import Action
# from pychron.scripts.core.script_validator import ScriptValidator
from pychron.paths import paths
# from traitsui.wx.code_editor import SourceEditor
# from traitsui.wx.basic_editor_factory import BasicEditorFactory
# from traitsui.editors.code_editor import ToolkitEditorFactory

SCRIPT_PATHS = dict(bakeout=('pychron.scripts.bakeout_script', 'BakeoutScript',
                             'pychron.scripts.bakeout_script_parser',
                             'BakeoutScriptParser',
                             ),

                    extractionline=('pychron.scripts.extraction_line_script',
                                             'ExtractionLineScript',
                            'pychron.scripts.extraction_line_script_parser',
                            'ExtractionLineScriptParser',
                                             )
                            )

SCRIPT_EXTENSIONS = dict(bakeout='.bo')


class ScriptHandler(Handler):
    def init(self, info):
        info.object.ui = info.ui
        _stc = info.ui._editors[2].control

        _stc.SetLexer(stc.STC_LEX_LUA)
        _stc.SetKeyWords(0, 'goto maintain')

    def save(self, info):
        info.object.save()

    def save_as(self, info):
        info.object.save_as()

    def open_script(self, info):
        info.object.open_script()

    def object_save_path_changed(self, info):
        if info.initialized:
            info.ui.title = 'Script Editor - {}'.format(info.object.save_path)


class ScriptManager(Manager):
    show_kind = Bool(False)
    kind = Enum('Bakeout', 'ExtractionLine')
    body = String
    help_message = Str
    save_enabled = Bool(False)
    save_path = String
    _original_body = Str
    _parser = None

#    script_validator = Instance(ScriptValidator, ())
    title = 'Script Editor - '

    default_directory_name = Str

    def _help_message_default(self):
        return self._get_help()

    def _check_save(self):
        if self.script_validator.errors:
            n = len(self.script_validator.errors)
            is_are = 'is' if n == 1 else 'are'
            e_es = 'error' if n == 1 else 'errors'
            d = confirmation(None, '''There {} {} {}.
Are you sure you want to save ?'''.format(is_are, n, e_es))
            r = d == 5103
        else:
            r = True

        return r

    def _get_default_directory(self):
        if self.default_directory_name:
            return os.path.join(paths.scripts_dir, self.default_directory_name)
        else:
            return paths.scripts_dir

    def save_as(self):
        if not self._check_save():
            return

        p = self.save_file_dialog(default_directory=self._get_default_directory())
#        p = '/Users/ross/Desktop/foo.txt'
        if p is not None:
            ext = SCRIPT_EXTENSIONS[self.kind.lower()]
            if not p.endswith(ext):
                p += ext

            self._dump_script(p)
            self.save_path = p

    def save(self):
        if not self._check_save():
            return

        p = self.save_path
        self._dump_script(p)
        self.save_enabled = False

    def open_script(self):
        p = self.open_file_dialog(default_directory=self._get_default_directory())
#        p = '/Users/ross/Desktop/foo.txt'
        if p is not None:
            self._load_script(p)
            self.save_path = p

    def _load_script(self, p):
        self.info('loading script {}'.format(p))
        with open(p, 'r') as f:
            self.body = f.read()
            self._original_body = self.body

    def _dump_script(self, p):

        self.info('saving script to {}'.format(p))
        with open(p, 'w') as f:
            f.write(self.body)
        self._original_body = self.body

    def _kind_changed(self):
        self.help_message = self._get_help()
        self._parser = None

    def _get_help(self):
        sp = SCRIPT_PATHS[self.kind.lower()]
        n = sp[1]
        m = __import__(sp[0],
                   fromlist=[n]
                       )
        s = getattr(m, n)

        return s.get_documentation()

    def _get_parser(self):
        if self._parser is None:
            sp = SCRIPT_PATHS[self.kind.lower()]
            n = sp[3]
            m = __import__(sp[2],
                   fromlist=[n]
                       )
            s = getattr(m, n)()
            self._parser = None
        else:
            s = self._parser
        return s

    def _body_changed(self):
        if self._original_body:
            if self.body == self._original_body:
                self.save_enabled = False
            else:
                self.save_enabled = True

        self.script_validator.errors = []
        self.script_validator.validate(self.body, self._get_parser())

    def traits_view(self):
        editor = VGroup(HGroup(spring, 'kind', visible_when='show_kind'),
                 Item('body', editor=CodeEditor(), show_label=False))

        helpgrp = Item('help_message',
                    editor=HTMLEditor(),
                     show_label=False)

        errorgrp = Item('script_validator', style='custom', show_label=False)

        v = View(
                 HGroup(editor,
                        VGroup(helpgrp, errorgrp)),
                 resizable=True,
                 buttons=[
                          Action(name='Open', action='open_script'),
                          Action(name='Save', action='save',
                                enabled_when='object.save_enabled'),
                          Action(name='Save As', action='save_as')
                          ],
                 width=700,
                 height=500,
                 handler=ScriptHandler,
                 title=self.title
                 )
        return v

if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('scripts')
#    s = ScriptManager(kind='ExtractionLine')
    s = ScriptManager(kind='Bakeout')
    s.configure_traits()
#============= EOF =============================================

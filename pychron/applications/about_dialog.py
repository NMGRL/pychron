# ===============================================================================
# Copyright 2014 Jake Ross
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
# ===============================================================================

#============= enthought library imports =======================
import sys

from PySide import QtGui, QtCore
from PySide.QtGui import QPlainTextEdit
from pyface.ui.qt4.about_dialog import AboutDialog
from traits.api import List,Str


#============= standard library imports ========================
#============= local library imports  ==========================
_ABOUT_TEXT = '''
<html>
  <body>
    <center>
      <h1>%s</h1>
      <table width="100%%" cellspacing="4" cellpadding="0" border="0" >
        <tr>
          <td align="center">
          <p>
            <img src="%s" alt="",width="50%%">
          </td>
        </tr>
      </table>
  </center>
  </body>
</html>
'''
_FOOTER_TEXT='''
<html>
  <body>
    <center>
      <p>
      Python %s
      Qt %s
      </p>
      <p>
      Copyright &copy; 2003-2010 Enthought, Inc.<br>
      Copyright &copy; 2007 Riverbank Computing Limited
      </p>
  </center>
  </body>
</html>'''

class myAboutDialog(AboutDialog):
    changes=List
    local_rev=Str
    remote_rev=Str
    version_info=Str

    def _create_contents(self, parent):
        label = QtGui.QLabel()
        footer = QtGui.QLabel()

        if parent.parent() is not None:
            title = parent.parent().windowTitle()
        else:
            title = ""

        # Set the title.
        self.title = "About %s" % title

        # Load the image to be displayed in the about box.
        image = self.image.create_image()
        path = self.image.absolute_path

        # The additional strings.
        # additions = '<br />'.join(self.additions)

        # Get the version numbers.
        py_version = sys.version[0:sys.version.find("(")]
        qt_version = QtCore.__version__

        # Set the page contents.
        label.setText(_ABOUT_TEXT % (self.version_info, path))
        footer.setText(_FOOTER_TEXT % (py_version, qt_version))

        # Create the button.
        buttons = QtGui.QDialogButtonBox()

        if self.ok_label:
            buttons.addButton(self.ok_label, QtGui.QDialogButtonBox.AcceptRole)
        else:
            buttons.addButton(QtGui.QDialogButtonBox.Ok)

        buttons.connect(buttons, QtCore.SIGNAL('accepted()'), parent, QtCore.SLOT('accept()'))

        revisions=self._create_revisions()
        changes=self._create_changes()
        lay = QtGui.QVBoxLayout()

        lay.addWidget(label)

        lay.addWidget(revisions)
        lay.addWidget(changes)
        lay.addWidget(footer)
        lay.addWidget(buttons)
        parent.setLayout(lay)

    def _create_revisions(self):
        label=QtGui.QLabel()
        label.setText('<b>Local=</b>{} <b>Remote=</b>{}'.format(self.local_rev, self.remote_rev))
        return label

    def _create_changes(self):
        c=QPlainTextEdit()
        c.setReadOnly(True)
        txt=''
        for i in range(10):
            for a,d,m in self.changes:
                txt+='<p>{} {}</p><p><b><pre> {}</pre></b></p>'.format(a,d, m)

        c.appendHtml(txt)
        cur=c.textCursor()
        cur.movePosition(QtGui.QTextCursor.Start)
        c.setTextCursor(cur)
        c.ensureCursorVisible()
        return c


# ============= EOF =============================================



#===============================================================================
# Copyright 2012 Jake Ross
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
# from traits.api import HasTraits
import time
from threading import Event

from pyface.api import OK, YES
from pyface.ui.qt4.confirmation_dialog import ConfirmationDialog
from pyface.message_dialog import MessageDialog

from pychron.ui.gui import invoke_in_main_thread

#from pyface.confirmation_dialog import ConfirmationDialog

#============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================
class myMessageMixin(object):
    '''
        makes  message dialogs thread save. 
    
    '''
    timeout_return_code = YES

    def open(self, timeout=0):
        """
            open the confirmation dialog on the GUI thread but wait for return
        """

        evt = Event()
        invoke_in_main_thread(self._open, evt)

        st=time.time()
        while not evt.is_set():
            time.sleep(0.25)
            if timeout:
                et = time.time() - st - 1
                if et > timeout - 1:
                    invoke_in_main_thread(self.destroy)
                    return self.timeout_return_code

                if self.control:
                    t = '{}\n\nTimeout in {:n}s'.format(self.message, int(timeout - et))
                    invoke_in_main_thread(self.control.setText, t)

        return self.return_code

    def _open(self, evt):

        if self.control is None:
            self._create()

        #if timeout:
        #    self._timeout_message.setText('Timeout in {}s'.format(timeout))

        if self.style == 'modal':
            try:
                self.return_code = self._show_modal()
            except AttributeError:
                pass
            finally:
                self.close()

        else:
            self.show(True)
            self.return_code = OK

        evt.set()
        return self.return_code

class myMessageDialog(myMessageMixin, MessageDialog):
    pass


class _ConfirmationDialog(ConfirmationDialog):
    pass
    #def _create_control(self, parent):
    #    dlg=super(_ConfirmationDialog, self)._create_control(parent)
    #
    #    layout = QtGui.QVBoxLayout()
    #    layout.addWidget(dlg)
    #
    #    #self._timeout_message=QLabel()
    #    #layout.addWidget(self._timeout_message)
    #
    #    #dlg.add
    #    #dlg.setLayout(layout)
    #    return dlg


class myConfirmationDialog(myMessageMixin, _ConfirmationDialog):
    pass









#============= EOF =============================================

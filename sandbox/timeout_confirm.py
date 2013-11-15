import os
import sys
from threading import Thread


d = os.path.dirname(os.getcwd())
sys.path.append(d)

from pychron.ui import set_toolkit

set_toolkit('qt4')

from pychron.ui.dialogs import myConfirmationDialog

from traits.api import HasTraits, Button
from traitsui.api import View


class A(HasTraits):
    a = Button

    def _a_fired(self):
        #self._test()
        t = Thread(target=self._test)
        t.start()

    def _test(self):
        dlg = myConfirmationDialog(message='Timeout Confirm Test')
        ret = dlg.open(timeout=10)
        print 'ret', ret

    def traits_view(self):
        return View('a')


A().configure_traits()
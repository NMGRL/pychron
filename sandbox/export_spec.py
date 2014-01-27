import os
import sys


d = os.path.dirname(os.getcwd())
sys.path.append(d)

from pychron.core.ui import set_toolkit

set_toolkit('qt4')


#e=ExportSpec(p='/Users/ross/Sandbox/aaaa_isotopes.h5')
#for iso,det in

#
#from pychron.core.ui.dialogs import myConfirmationDialog
#
#from traits.api import HasTraits, Button
#from traitsui.api import View
#
#
#class A(HasTraits):
#    a = Button
#
#    def _a_fired(self):
#        #self._test()
#        t = Thread(target=self._test)
#        t.start()
#
#    def _test(self):
#        dlg = myConfirmationDialog(message='Timeout Confirm Test')
#        ret = dlg.open(timeout=10)
#        print 'ret', ret
#
#    def traits_view(self):
#        return View('a')
#
#
#A().configure_traits()
"""
 test script that periodically
 sends random messages using zmq.Publisher patterb
"""
import sys
import os
from traits.has_traits import HasTraits
from traits.trait_types import Str
from traitsui.item import UItem
from traitsui.view import View


d = os.path.dirname(os.getcwd())
sys.path.append(d)

from pychron.core.ui import set_toolkit

set_toolkit('qt4')
from pychron.core.ui.text_editor import myTextEditor


class A(HasTraits):
    text = Str
    traits_view = View(UItem('text', editor=myTextEditor(wrap=False,
                                                         editable=False,
                                                         tab_width=15,
                                                         bgcolor='#F7F6D0',
                                                         fontsize=10
    )),
                       resizable=True,
                       width=700)


if __name__ == '__main__':
    a = A()
    p = '/Users/ross/Pychrondata_dev/experiments/Current Experiment.txt'
    with open(p, 'r') as rfile:
        a.text = rfile.read()
    a.configure_traits()


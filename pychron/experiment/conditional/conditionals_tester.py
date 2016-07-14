from pychron.core.ui import set_qt
set_qt()


from traits.api import HasTraits, Button
from traitsui.api import View

from pychron.experiment.conditional.conditionals_edit_view import edit_conditionals
from pychron.paths import paths
paths.build('_dev')

if __name__ == '__main__':
    class D(HasTraits):
        test = Button

        def _test_fired(self):
            edit_conditionals('normal', save_as=False)


    D().configure_traits(view=View('test'))
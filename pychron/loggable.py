#!/usr/bin/python
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
from traits.api import HasTraits, Any, String

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.globals import globalv
from pychron.core.helpers.color_generators import colorname_generator
from pychron.core.helpers.logger_setup import new_logger
from threading import current_thread
from pychron.core.ui.thread import currentThreadName

from pychron.core.ui.dialogs import myConfirmationDialog, myMessageDialog
from pychron.core.ui.gui import invoke_in_main_thread

color_name_gen = colorname_generator()
NAME_WIDTH = 40


def confirmation_dialog(msg, return_retval=False,
                        cancel=False, title='',
                        timeout=None, size=None,
                        timeout_ret=None):

    if size is None:
        size = (-1, -1)

    dlg = myConfirmationDialog(
        timeout_return_code=timeout_ret,
        cancel=cancel,
        message=msg,
        title=title,
        style='modal',
        size=size)



    retval = dlg.open(timeout)
    if return_retval:
        return retval
    else:
        from pyface.api import YES

        return retval == YES


__gloggers__ = dict()


class Loggable(HasTraits):
    """
    """
    application = Any
    logger = Any  # (transient=True)
    name = String
    logger_name = String
    use_logger_display = True
    use_warning_display = True
    logcolor = 'black'
    shared_logger = False

    # logger_display = None
    def __init__(self, *args, **kw):
        super(Loggable, self).__init__(*args, **kw)

        t = str(type(self))
        if self.shared_logger and t in __gloggers__:
            self.logger = __gloggers__[t]
        else:
            self._add_logger()

    def _name_changed(self):
        self._add_logger()

    def _logger_name_changed(self):
        self._add_logger()

    def _add_logger(self):
        """

        """
        if self.logger_name:
            name = self.logger_name
        elif self.name:
            name = self.name
        else:
            name = self.__class__.__name__

        self.logger = new_logger(name)

        c = color_name_gen.next()
        if c in ['gray', 'silver', 'greenyellow']:
            c = color_name_gen.next()
        self.logcolor = c

    def add_window(self, ui):

        try:
            if self.application is not None:
                self.application.uis.append(ui)
        except AttributeError:
            pass

    def open_view(self, obj, **kw):
        def _open_():
            ui = obj.edit_traits(**kw)
            self.add_window(ui)

        invoke_in_main_thread(_open_)

    def warning_dialog(self, msg, sound=None, title='Warning'):
        dialog = myMessageDialog(
            parent=None, message=str(msg),
            title=title,
            severity='warning')
        #         if sound:
        #             from pychron.core.helpers.media import loop_sound
        #             evt = loop_sound(sound)
        #             dialog.close = lambda: self._close_warning(evt)

        #         from threading import current_thread
        #         print current_thread()
        dialog.open()
    
    def confirmation_dialog(self,*args, **kw):
        return confirmation_dialog(*args, **kw)

    def information_dialog(self, msg, title='Information'):
        dlg = myMessageDialog(parent=None, message=msg,
                              title=title,
                              severity='information')
        dlg.open()

    def db_save_dialog(self):
        return self.confirmation_dialog('Save to Database')

    def message(self, msg):
        from pychron.displays.gdisplays import gMessageDisplay

        if not gMessageDisplay.opened and not gMessageDisplay.was_closed:
            gMessageDisplay.opened = True
            invoke_in_main_thread(gMessageDisplay.edit_traits)

        gMessageDisplay.add_text(msg)

        self.info(msg)

    def warning(self, msg, decorate=True):
        """
        """

        if self.logger is not None:
            if self.use_warning_display:
                from pychron.displays.gdisplays import gWarningDisplay

                if globalv.show_warnings:
                #if not gWarningDisplay.opened and not gWarningDisplay.was_closed:
                #invoke_in_main_thread(gWarningDisplay.edit_traits)
                #gWarningDisplay.opened = True
                    gWarningDisplay.add_text(
                        '{{:<{}s}} -- {{}}'.format(NAME_WIDTH).format(self.logger.name.strip(), msg))

            # if decorate:
            #     msg = '****** {}'.format(msg)
            self._log_('warning', msg)

    def info(self, msg, decorate=True, dolater=False, color=None):
        """

        """
        if self.logger is not None:
            if self.use_logger_display:
                from pychron.displays.gdisplays import gLoggerDisplay

                if globalv.show_infos:
                #                     if not gLoggerDisplay.opened and not gLoggerDisplay.was_closed:
                #                         invoke_in_main_thread(gLoggerDisplay.edit_traits)


                    args = ('{{:<{}s}} -- {{}}'.format(NAME_WIDTH).format(self.logger.name.strip(),
                                                                          msg))
                    gLoggerDisplay.add_text(args, color=color)

            # if decorate:
            #     msg = '====== {}'.format(msg)

            self._log_('info', msg)

    def close_displays(self):
        from pychron.displays.gdisplays import gLoggerDisplay, gWarningDisplay, gMessageDisplay

        gLoggerDisplay.close_ui()
        gWarningDisplay.close_ui()
        gMessageDisplay.close_ui()

    def debug(self, msg, decorate=True):
        # '''
        # '''
        #
        # if decorate:
        #     msg = '++++++ {}'.format(msg)

        self._log_('debug', msg)


    def _log_(self, func, msg):

        def get_thread_name():
            ct = current_thread()
            name = ct.name
            if name.startswith('Dummy'):
                name = currentThreadName()

            return name

        if self.logger is None:
            return

        extras = {'threadName_': get_thread_name()}
        func = getattr(self.logger, func)

        if isinstance(msg, (list, tuple)):
            msg=','.join(map(str, msg))

        msg=self._post_process_msg(msg)
        func(msg, extra=extras)

    def _post_process_msg(self, msg):
        return msg
        #        func(msg)

#============= EOF =============================================

#!/usr/bin/python
# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import HasTraits, Any, String

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.globals import globalv
from pychron.core.helpers.color_generators import colorname_generator
from pychron.core.helpers.logger_setup import new_logger
from threading import current_thread

# from pychron.core.ui.dialogs import myConfirmationDialog, myMessageDialog
# from pychron.core.ui.gui import invoke_in_main_thread

color_name_gen = colorname_generator()
NAME_WIDTH = 40
__gloggers__ = dict()


class unique(object):
    def __init__(self):
        self._registry = {}

    def __call__(self, f):
        def wrapped_f(*args, **kw):
            obj = args[0]
            msg = args[1]
            hmsg = hash(msg)
            ido = id(obj)
            if not ido in self._registry:
                self._registry[ido] = []

            msgs = self._registry[ido]
            if not hmsg in msgs:
                msgs.append(hmsg)
                f(*args)

        return wrapped_f


def confirmation_dialog(msg, return_retval=False,
                        cancel=False, title='',
                        timeout=None, size=None,
                        timeout_ret=None, **kw):
    if size is None:
        size = (-1, -1)
    from pychron.core.ui.dialogs import myConfirmationDialog

    dlg = myConfirmationDialog(
        cancel=cancel,
        message=msg,
        title=title,
        style='modal',
        size=size, **kw)

    if timeout_ret is not None:
        dlg.timeout_return_code = timeout_ret

    retval = dlg.open(timeout)
    from pyface.api import YES, OK

    if return_retval:
        return retval
    else:

        return retval in (YES, OK)


class Loggable(HasTraits):
    """
    """
    application = Any
    logger = Any  # (transient=True)
    name = String
    logger_name = String
    # use_logger_display = True
    # use_warning_display = True
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

    def report_logger_stats(self):
        self.debug('&&&& len __gloggers__ = {}'.format(len(__gloggers__)))

    @unique()
    def unique_warning(self, *args, **kw):
        self.warning(*args, **kw)

    @unique()
    def unique_info(self, *args, **kw):
        self.info(*args, **kw)

    @unique()
    def unique_debug(self, *args, **kw):
        self.debug(*args, **kw)

    def warning(self, msg):
        """
        """

        if self.logger is not None:
            if globalv.use_warning_display:
                from pychron.displays.gdisplays import gWarningDisplay

                if globalv.show_warnings:
                    gWarningDisplay.add_text(
                        '{{:<{}s}} -- {{}}'.format(NAME_WIDTH).format(self.logger.name.strip(), msg))

            self._log_('warning', msg)

    def info(self, msg, dolater=False, color=None):
        """

        """
        if self.logger is not None:
            if globalv.use_logger_display:
                from pychron.displays.gdisplays import gLoggerDisplay

                if globalv.show_infos:
                    args = ('{{:<{}s}} -- {{}}'.format(NAME_WIDTH).format(self.logger.name.strip(),
                                                                          msg))
                    gLoggerDisplay.add_text(args, color=color)

            self._log_('info', msg)

    def debug_exception(self):
        import traceback

        self.debug(traceback.format_exc())

    def debug(self, msg):
        self._log_('debug', msg)

    #dialogs
    def warning_dialog(self, msg, sound=None, title='Warning'):
        self.warning(msg)

        from pychron.core.ui.dialogs import myMessageDialog

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

    def confirmation_dialog(self, *args, **kw):
        return confirmation_dialog(*args, **kw)

    def information_dialog(self, msg, title='Information'):
        from pychron.core.ui.dialogs import myMessageDialog

        dlg = myMessageDialog(parent=None, message=msg,
                              title=title,
                              severity='information')
        dlg.open()

    def message(self, msg):
        from pychron.displays.gdisplays import gMessageDisplay

        if not gMessageDisplay.opened and not gMessageDisplay.was_closed:
            gMessageDisplay.opened = True
            from pychron.core.ui.gui import invoke_in_main_thread

            invoke_in_main_thread(gMessageDisplay.edit_traits)

        gMessageDisplay.add_text(msg)

        self.info(msg)

    #private
    def _add_logger(self):
        """

        """

        if self.logger_name:
            name = self.logger_name
        elif self.name:
            name = self.name
        else:
            name = self.__class__.__name__

        if self.logger is None:
            __gloggers__[name] = self.logger
            self.logger = new_logger(name)

        c = color_name_gen.next()
        if c in ['gray', 'silver', 'greenyellow']:
            c = color_name_gen.next()
        self.logcolor = c

    def _log_(self, func, msg):

        def get_thread_name():
            ct = current_thread()
            name = ct.name
            # from pychron.core.ui.thread import currentThreadName
            # if name.startswith('Dummy'):
            #     name = currentThreadName()

            return name

        if self.logger is None:
            return

        extras = {'threadName_': get_thread_name()}
        func = getattr(self.logger, func)

        if isinstance(msg, (list, tuple)):
            msg = ','.join(map(str, msg))

        msg = self._post_process_msg(msg)
        func(msg, extra=extras)

    def _post_process_msg(self, msg):
        return msg

    #handlers
    def _name_changed(self):
        self._add_logger()

    def _logger_name_changed(self):
        self._add_logger()

# ============= EOF =============================================

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

# ============= standard library imports ========================
from threading import current_thread
from typing import Any as TypingAny, Callable, Dict

# ============= enthought library imports =======================
from traits.api import Any, String

# ============= local library imports  ==========================
from pychron.base_fs import BaseFS
from pychron.core.confirmation import confirmation_dialog
from pychron.core.helpers.color_generators import colorname_generator
from pychron.core.helpers.color_utils import contrast_color, normalize_color_name
from pychron.core.helpers.logger_setup import new_logger
from pychron.globals import globalv

color_name_gen = colorname_generator()
NAME_WIDTH = 40
__gloggers__: Dict[str, TypingAny] = dict()


class unique(object):
    def __init__(self) -> None:
        self._registry: Dict[int, list[int]] = {}

    def __call__(self, f: Callable[..., TypingAny]) -> Callable[..., None]:
        def wrapped_f(*args, **kw) -> None:
            obj = args[0]
            msg = args[1]
            hmsg = hash(msg)
            ido = id(obj)
            if ido not in self._registry:
                self._registry[ido] = []

            msgs = self._registry[ido]
            if hmsg not in msgs:
                msgs.append(hmsg)
                f(*args, **kw)

        return wrapped_f


class Loggable(BaseFS):
    """ """

    application = Any
    logger = None  # (transient=True)
    name = String
    logger_name = String
    # use_logger_display = True
    # use_warning_display = True
    logcolor = "black"
    shared_logger = False

    def __init__(self, *args, **kw) -> None:
        super(Loggable, self).__init__(*args, **kw)
        self.init_logger()

    def init_logger(self) -> None:
        cache_key = self._logger_cache_key()
        if self.shared_logger and cache_key in __gloggers__:
            self.logger = __gloggers__[cache_key]
        else:
            self._add_logger()

    def report_logger_stats(self) -> None:
        self.debug("&&&& len __gloggers__ = {}".format(len(__gloggers__)))

    @unique()
    def unique_warning(self, *args, **kw):
        self.warning(*args, **kw)

    @unique()
    def unique_info(self, *args, **kw):
        self.info(*args, **kw)

    @unique()
    def unique_debug(self, *args, **kw):
        self.debug(*args, **kw)

    def warning(self, msg: str) -> None:
        """ """

        if self.logger is not None:
            if globalv.use_warning_display:
                from pychron.core.displays.gdisplays import gWarningDisplay

                if globalv.show_warnings:
                    gWarningDisplay.add_text(
                        "{{:<{}s}} -- {{}}".format(NAME_WIDTH).format(
                            self.logger.name.strip(), msg
                        )
                    )

            self._log_("warning", msg)

    def info(self, msg: str, dolater: bool = False, color=None) -> None:
        """ """
        if self.logger is not None:
            if globalv.use_logger_display:
                from pychron.core.displays.gdisplays import gLoggerDisplay

                if globalv.show_infos:
                    args = "{{:<{}s}} -- {{}}".format(NAME_WIDTH).format(
                        self.logger.name.strip(), msg
                    )
                    gLoggerDisplay.add_text(args, color=color)

            self._log_("info", msg)

    def debug_exception(self) -> str:
        import traceback

        exc = traceback.format_exc()
        self.debug(exc)
        return exc

    def warning_exception(self) -> str:
        import traceback

        exc = traceback.format_exc()
        self.warning_dialog(exc)
        return exc

    def critical(self, msg: str) -> None:
        self._log_("critical", msg)

    def debug(self, msg: str, *args, **kw) -> None:
        try:
            msg = msg.format(*args, **kw)
        except BaseException:
            pass
        self._log_("debug", msg)

    def log(self, msg: str, level: int = 10) -> None:
        def log(m, *args, **kw):
            self.logger.debug(m)
            self.logger.log(level, m, *args, **kw)

        self._log_(log, msg)

    # dialogs
    def warning_dialog(self, msg: str, sound=None, title: str = "Warning", **kw) -> None:
        self.warning(msg)

        from pychron.core.ui.dialogs import myMessageDialog

        dialog = myMessageDialog(
            parent=None, message=str(msg), title=title, severity="warning", **kw
        )
        #         if sound:
        #             from pychron.core.helpers.media import loop_sound
        #             evt = loop_sound(sound)
        #             dialog.close = lambda: self._close_warning(evt)

        #         from threading import current_thread
        #         print current_thread()
        dialog.open()

    def confirmation_dialog(self, *args, **kw):
        return confirmation_dialog(*args, **kw)

    def information_dialog(self, msg: str, title: str = "Information", **kw) -> None:
        from pychron.core.ui.dialogs import myMessageDialog

        self.info(msg)
        dlg = myMessageDialog(
            parent=None, message=msg, title=title, severity="information", **kw
        )
        dlg.open()

    def message(self, msg: str) -> None:
        from pychron.core.displays.gdisplays import gMessageDisplay

        if not gMessageDisplay.opened and not gMessageDisplay.was_closed:
            gMessageDisplay.opened = True
            from pychron.core.ui.gui import invoke_in_main_thread

            invoke_in_main_thread(gMessageDisplay.edit_traits)

        gMessageDisplay.add_text(msg)

        self.info(msg)

    # private
    def _logger_cache_key(self) -> str:
        if self.shared_logger:
            return str(type(self))

        if self.logger_name:
            return self.logger_name

        if self.name:
            return self.name

        return self.__class__.__name__

    def _add_logger(self) -> None:
        """ """
        if self.logger_name:
            name = self.logger_name
        elif self.name:
            name = self.name
        else:
            name = self.__class__.__name__

        if self.logger is None:
            self.logger = new_logger(name)
            __gloggers__[self._logger_cache_key()] = self.logger

        c = normalize_color_name(next(color_name_gen))
        while contrast_color(c, dark="black", light="white") != "white":
            c = normalize_color_name(next(color_name_gen))
        self.logcolor = c

    def _log_(self, func, msg) -> None:
        # def get_thread_name():
        #     name = 'foo'
        #     # ct = current_thread()
        #     # name = ct.name
        #     from pychron.core.ui.thread import currentThreadName
        #     # if name.startswith('Dummy'):
        #     #     name = currentThreadName()
        #
        #     return name

        if self.logger is None:
            return

        # extras = {'threadName_': get_thread_name()}
        if isinstance(func, str):
            func = getattr(self.logger, func)

        if isinstance(msg, (list, tuple)):
            msg = ",".join(map(str, msg))

        msg = self._post_process_msg(msg)
        # func(msg, extra=extras)
        func(msg)

    def _post_process_msg(self, msg):
        return msg

    # handlers
    def _name_changed(self) -> None:
        self._add_logger()

    def _logger_name_changed(self) -> None:
        self._add_logger()


# class Loggable(HasTraits, Loggable):
#     def __init__(self, *args, **kw):
#         super().__init__(*args, **kw)
#         self.init_logger()

# ============= EOF =============================================

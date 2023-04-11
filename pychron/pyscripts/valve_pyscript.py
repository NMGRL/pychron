# ===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
import time

from traits.api import Any

from pychron.globals import globalv
from pychron.pychron_constants import NULL_STR, EL_PROTOCOL
from pychron.pyscripts.decorators import verbose_skip, makeRegistry, makeNamedRegistry
from pychron.pyscripts.pyscript import PyScript

command_register = makeRegistry()
named_register = makeNamedRegistry(command_register)


class ValvePyScript(PyScript):
    runner = Any
    allow_lock = False
    retry_actuation = True
    cancel_on_failed_actuation = True

    def get_command_register(self):
        return list(command_register.commands.items())

    def gosub(self, *args, **kw):
        kw["runner"] = self.runner
        s = super(ValvePyScript, self).gosub(*args, **kw)
        if s:
            s.runner = None
        return s

    @verbose_skip
    @command_register
    def lock(self, name=None, description=""):
        if description is None:
            description = NULL_STR

        self.console_info("locking {} ({})".format(name, description))
        if self.allow_lock:
            return self._manager_actions(
                [("lock_valve", (name,), dict(mode="script", description=description))],
                protocol=EL_PROTOCOL,
            )
        else:
            self.warning("Valve locking not enabled for this script")

    @verbose_skip
    @command_register
    def unlock(self, name=None, description=""):
        if description is None:
            description = NULL_STR

        self.console_info("unlocking {} ({})".format(name, description))
        if self.allow_lock:
            return self._manager_actions(
                [
                    (
                        "unlock_valve",
                        (name,),
                        dict(mode="script", description=description),
                    )
                ],
                protocol=EL_PROTOCOL,
            )
        else:
            self.warning("Valve locking not enabled for this script")

    @verbose_skip
    @named_register("open")
    def _m_open(
        self, name=None, description="", cancel_on_failed_actuation=True, ntries=100
    ):
        self._valve_actuation(
            "open", name, description, cancel_on_failed_actuation, ntries
        )

    @verbose_skip
    @command_register
    def close(
        self, name=None, description="", cancel_on_failed_actuation=True, ntries=100
    ):
        self._valve_actuation(
            "close", name, description, cancel_on_failed_actuation, ntries
        )

    def _valve_actuation(
        self, action, name, description, cancel_on_failed_actuation, ntries
    ):
        self.console_info(
            "{} name={} desc={}".format(
                action, name or NULL_STR, description or NULL_STR
            )
        )

        result = self._manager_actions(
            [
                (
                    "{}_valve".format(action),
                    (name,),
                    dict(mode="script", description=description),
                )
            ],
            protocol=EL_PROTOCOL,
        )

        self.debug(
            "-------------------------- {} {} ({}) result={}".format(
                action, name, description, result
            )
        )
        if result is not None:
            if not self._finish_valve_change(
                action, result, name, description, ntries=ntries
            ):
                if not globalv.experiment_debug:
                    if cancel_on_failed_actuation:
                        self.cancel()
                        msg = 'Failed to {} valve name="{}", description="{}"'.format(
                            action, name, description
                        )

                    else:
                        # certain valves can fail to actuate but still you'd want to analyses the gas in the
                        # extraction line. So we dont want to cancel. but we dont want to run another analysis either.
                        # setting "end_at_run_completion" should do it
                        self._failed_actuation_hook()
                        msg = 'Failed to {} valve name="{}", description="{}". Continuing'.format(
                            action, name, description
                        )

                    from pychron.core.ui.gui import invoke_in_main_thread

                    invoke_in_main_thread(self.warning_dialog, msg)

                else:
                    self.debug("Experiment debug mode. not canceling")

    @verbose_skip
    @command_register
    def is_open(self, name=None, description=""):
        self.console_info(
            "is name={} desc={} open?".format(name or NULL_STR, description or NULL_STR)
        )
        result = self._get_valve_state(name, description)
        if result:
            return result[0] is True

    @verbose_skip
    @command_register
    def is_closed(self, name=None, description=""):
        self.console_info("is {} ({}) closed?".format(name, description))
        result = self._get_valve_state(name, description)
        if result:
            r = result[0] is False
            self.debug("is closed {}".format(r))
            return r

    # private
    def _failed_actuation_hook(self):
        pass

    def _finish_valve_change(
        self, action, result, name, description, retry=1, ntries=100
    ):
        """
        :param action:
        :param result:
        :param name:
        :param description:
        :param retry:
        :return:
        """
        ok, changed = result[0]
        # if changed:
        #     time.sleep(0.25)

        locked = self._manager_actions(
            [
                (
                    "get_software_lock",
                    (name,),
                    dict(mode="script", description=description),
                )
            ],
            protocol=EL_PROTOCOL,
        )

        # if action == 'close':
        # ok = not ok
        self.debug("action={}, ok={}, locked={}".format(action, ok, locked))
        change_ok = True
        if (
            not ok
            and not locked[0]
            and not globalv.experiment_debug
            and not globalv.valve_debug
        ):
            msg = 'Failed to {} valve Name="{}", Description="{}"'.format(
                action, name or "", description or ""
            )
            self.console_info(msg)
            change_ok = False
            if self.retry_actuation and retry < ntries:
                time.sleep(1)
                msg = 'Retry actuation. i={} Action="{}", Name="{}", Description="{}"'.format(
                    retry, action, name or "", description or ""
                )
                self.console_info(msg)

                result = self._manager_actions(
                    [
                        (
                            "{}_valve".format(action),
                            (name,),
                            dict(mode="script", description=description),
                        )
                    ],
                    protocol=EL_PROTOCOL,
                )

                if result is not None:
                    change_ok = self._finish_valve_change(
                        action,
                        result,
                        name,
                        description,
                        retry=retry + 1,
                        ntries=ntries,
                    )

        return change_ok

        # return not cancel
        # if cancel:
        #     if not globalv.experiment_debug:
        #         # self.warning_dialog(msg)
        #         self.cancel()
        #     else:
        #         self.debug('Experiment debug mode. not canceling')
        # else:
        #     return True

    def _get_valve_state(self, name, description):
        return self._manager_actions(
            [("get_valve_state", (name,), dict(description=description))],
            protocol=EL_PROTOCOL,
        )


# ============= EOF =============================================

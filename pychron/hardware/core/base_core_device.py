# ===============================================================================
# Copyright 2016 Jake Ross
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

# =============enthought library imports=======================

from __future__ import absolute_import
from __future__ import print_function

# from threading import Lock
import inspect

# from pyface.timer.api import Timer
# =============standard library imports ========================
import random
import time

from traits.api import provides

from pychron.consumer_mixin import ConsumerMixin
from pychron.globals import globalv
from pychron.hardware.core.communicators.scheduler import CommunicationScheduler
from pychron.hardware.core.exceptions import TimeoutError, CRCError
from pychron.has_communicator import HasCommunicator

# =============local library imports  ==========================
from .i_core_device import ICoreDevice


def crc_caller(func):
    def d(*args, **kw):
        try:
            return func(*args, **kw)
        except CRCError:
            stack = inspect.stack()
            print("{} called by {}".format(func.__name__, stack[1][3]))

    return d


@provides(ICoreDevice)
class BaseCoreDevice(HasCommunicator, ConsumerMixin):
    """ """

    _auto_started = False
    _no_response_counter = 0
    _scheduler_name = None

    def load_from_device(self):
        pass

    def send_email_notification(self, message):
        if self.application:
            tm = self.application.get_service("pychron.social.emailer.Emailer")
            if tm:
                tm.broadcast(message)
            else:
                self.warning("No emailer available")

    # ICoreDevice protocol
    def close(self):
        if self.communicator:
            self.communicator.close()

    def get(self, *args, **kw):
        return self.current_scan_value

    def set(self, v):
        pass

    def is_connected(self):
        if self.communicator:
            return not self.communicator.simulation

    def test_connection(self):
        if self.communicator:
            return self.communicator.test_connection()

    def set_simulation(self, tf):
        if self.communicator:
            self.communicator.simulation = tf

    def load(self, *args, **kw):
        """
        Load a configuration file.
        Get Communications info to make a new communicator
        """
        config = self.get_configuration()
        if config:
            if config.has_section("General"):
                name = self.config_get(config, "General", "name", optional=True)
                if name is not None:
                    self.name = name

            if config.has_section("Communications"):
                comtype = self.config_get(config, "Communications", "type")
                if not self._load_communicator(config, comtype):
                    return False

                self.set_attribute(
                    config,
                    "_scheduler_name",
                    "Communications",
                    "scheduler",
                    optional=True,
                )

            self._load_hook(config)

            # load additional child specific args
            r = self.load_additional_args(config)
            if r:
                self._loaded = True
            return r

    def open(self, *args, **kw):
        self.debug("open device")
        return HasCommunicator.open(self, **kw)

    def initialize(self, *args, **kw):
        a = super(BaseCoreDevice, self).initialize(*args, **kw)
        b = False
        if self.communicator is not None:
            b = self.communicator.initialize(*args, **kw)

        return a and b

    def load_additional_args(self, config):
        """
        remember to return a boolean in any subclass that overrides this method.
        if True bootstraping of this device will continue. otherwise device will not fully initialize
        """
        return True

    def blocking_poll(
        self, func, args=None, kwargs=None, period=1, timeout=None, script=None
    ):
        """
        repeatedly ask func at 1/period rate
        if func returns true return True
        if timeout return False
        """
        if isinstance(func, str):
            func = getattr(self, func)
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()

        st = time.time()
        while 1:
            if script and script.is_canceled():
                return
            if func(*args, **kwargs):
                return True
            elif timeout:
                et = time.time() - st
                if et > timeout:
                    self.warning(
                        'blocking poll of "{}" timed out after {}s'.format(
                            func.__name__, timeout
                        )
                    )
                    raise TimeoutError(func.__name__, timeout)
            time.sleep(period)

    @crc_caller
    def ask(self, cmd, **kw):
        """ """

        comm = self.communicator
        if comm is not None:
            if comm.scheduler:
                r = comm.scheduler.schedule(comm.ask, args=(cmd,), kwargs=kw)
            else:
                r = comm.ask(cmd, **kw)

            if hasattr(self, "_communicate_hook"):
                self._communicate_hook(cmd, r)
            return r
        else:
            self.info("no communicator for this device {}".format(self.name))

    @crc_caller
    def write(self, *args, **kw):
        """ """
        self.tell(*args, **kw)

    @crc_caller
    def tell(self, *args, **kw):
        """ """
        if self.communicator is not None:
            cmd = " ".join([str(a) for a in args] + [str(a) for a in kw.items()])

            self._communicate_hook(cmd, "-")
            return self.communicator.tell(*args, **kw)

    @crc_caller
    def read(self, *args, **kw):
        """ """
        if self.communicator is not None:
            return self.communicator.read(*args, **kw)

    # if self.simulation:
    #            return 'simulation'

    #            gdict = globals()
    #            if communicator_type in gdict:
    #                return gdict[communicator_type](name='_'.join((self.name, communicator_type)),
    #                                   id_query=self.id_query,
    #                                   id_response=self.id_response
    #                                )
    def post_initialize(self, *args, **kw):
        if self.graph_ytitle:
            self.graph.set_y_title(self.graph_ytitle)

        self.setup_scan()
        self.setup_alarms()
        self.setup_scheduler()

        if self.auto_start:
            self.start_scan()

    def get_random_value(self, mi=0, ma=10):
        """
        convienent method for getting a random integer between min and max

        Defaults:
            min=0
            max=10

        """
        return random.randint(mi, ma) if globalv.communication_simulation else None

    def setup_scheduler(self, name=None):
        if self.application:
            if name is None:
                name = self._scheduler_name
            if name is not None:
                sc = self.application.get_service(
                    CommunicationScheduler, 'name=="{}"'.format(name)
                )
                if sc is None:
                    sc = CommunicationScheduler(name=name)
                    self.application.register_service(type(sc), sc)
                self.set_scheduler(sc)

    def set_scheduler(self, s):
        if self.communicator is not None:
            self.communicator.scheduler = s

    def repeat_command(
        self,
        cmd,
        ntries=2,
        check_val=None,
        check_type=None,
        break_val=None,
        verbose=True,
        delay=None,
        **kw
    ):
        if isinstance(cmd, tuple):
            cmd = self._build_command(*cmd)
        else:
            cmd = self._build_command(cmd)

        resp = None
        for i in range(ntries + 1):
            resp = self._parse_response(self.ask(cmd, verbose=verbose))
            if verbose:
                resp = resp or ""
                resp = resp.strip()
                n = len(str(resp))
                m = "repeat command {} response = {} len={} ".format(i + 1, resp, n)
                self.debug(m)

            if break_val and resp == break_val:
                return

            if check_val is not None:
                if self.simulation:
                    resp = check_val

                if resp == check_val:
                    break
                else:
                    if delay:
                        time.sleep(delay)
                    continue

            if check_type is not None:
                if self.simulation:
                    resp = random.randint(1, 10)
                else:
                    try:
                        resp = check_type(resp)
                    except (ValueError, TypeError):
                        continue

            if resp is not None:
                break

        return resp

    # ===============================================================================
    # scanable interface
    # ===============================================================================
    # def _scan_hook(self, v):
    #     for a in self.alarms:
    #         if a.test_condition(v):
    #             alarm_msg = a.get_message(v)
    #             self.warning(alarm_msg)
    #             manager = self.application.get_service('pychron.social.twitter_manager.TwitterManager')
    #             if manager is not None:
    #                 manager.post(alarm_msg)
    #             break

    def _parse_response(self, v):
        return v

    def _load_hook(self, config):
        pass


# ========================= EOF ============================================

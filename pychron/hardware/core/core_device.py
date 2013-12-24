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

#=============enthought library imports=======================
from traits.api import HasTraits, Str, implements, Any, List, \
    Bool, Enum
# from pyface.timer.api import Timer
#=============standard library imports ========================
import random
# from threading import Lock
from datetime import datetime
#=============local library imports  ==========================
from i_core_device import ICoreDevice
# from pychron.core.helpers.timer import Timer
# from pychron.managers.data_managers.csv_data_manager import CSVDataManager
# from pychron.core.helpers.datetime_tools import generate_datetimestamp
from pychron.hardware.core.scanable_device import ScanableDevice
from pychron.rpc.rpcable import RPCable
from pychron.has_communicator import HasCommunicator
from pychron.hardware.core.communicators.scheduler import CommunicationScheduler
from pychron.consumer_mixin import ConsumerMixin


class Alarm(HasTraits):
    alarm_str = Str
    triggered = False

    def get_alarm_params(self):
        als = self.alarm_str
        cond = als[0]
        if cond not in ['<', '>']:
            cond = '='
            trigger = float(als)
        else:
            trigger = float(als[1:])
        return cond, trigger

    def test_condition(self, value):
        cond, trigger = self.get_alarm_params()

        expr = 'value {} {}'.format(cond, trigger)

        triggered = eval(expr, {}, dict(value=value))

        if triggered:
            if not self.triggered:
                self.triggered = True
        else:
            self.triggered = False

        return self.triggered

    def get_message(self, value):
        cond, trigger = self.get_alarm_params()
        tstamp = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')

        return '<<<<<<ALARM {}>>>>>> {} {} {}'.format(tstamp, value, cond, trigger)


class CoreDevice(ScanableDevice, RPCable, HasCommunicator, ConsumerMixin):
    '''
    '''
    #    graph_klass = TimeSeriesStreamGraph

    implements(ICoreDevice)
    name = Str
    #    id_query = ''
    #    id_response = ''

    current_scan_value = 0

    application = Any

    _no_response_counter = 0
    alarms = List(Alarm)

    dm_kind = Enum('h5', 'csv')
    use_db = Bool(False)
    _auto_started = False

    _scheduler_name = None

    def close(self):
        if self._communicator:
            self._communicator.close()

    def _communicate_hook(self, cmd, r):
        self.last_command = cmd
        self.last_response = r if r else ''

    def load(self, *args, **kw):
        '''
            Load a configuration file.  
            Get Communications info to make a new communicator
        '''
        config = self.get_configuration()
        if config:

            if config.has_section('General'):
                name = self.config_get(config, 'General', 'name', optional=True)
                if name is not None:
                    self.name = name

            if config.has_section('Communications'):
                comtype = self.config_get(config, 'Communications', 'type')
                if not self._load_communicator(config, comtype):
                    return False

                self.set_attribute(config, '_scheduler_name', 'Communications', 'scheduler', optional=True)

            self._load_hook(config)

            # load additional child specific args
            r = self.load_additional_args(config)
            if r:
                self._loaded = True
            return r

    def initialize(self, *args, **kw):
        a = super(CoreDevice, self).initialize(*args, **kw)
        b = False
        if self._communicator is not None:
            b = self._communicator.initialize(*args, **kw)

        return a and b

    def load_additional_args(self, config):
        '''
        '''
        return True

    def ask(self, cmd, **kw):
        '''
        '''
        comm = self._communicator
        if comm is not None:
            if comm.scheduler:
                r = comm.scheduler.schedule(comm.ask, args=(cmd,),
                                            kwargs=kw
                )
            else:
                r = comm.ask(cmd, **kw)
            self._communicate_hook(cmd, r)
            return r
        else:
            self.info('no communicator for this device {}'.format(self.name))

    def write(self, *args, **kw):
        '''
        '''
        self.tell(*args, **kw)

    def tell(self, *args, **kw):
        '''
        '''
        if self._communicator is not None:
            cmd = ' '.join(map(str, args) + map(str, kw.iteritems()))
            self._communicate_hook(cmd, '-')
            return self._communicator.tell(*args, **kw)

    def read(self, *args, **kw):
        '''
        '''
        if self._communicator is not None:
            return self._communicator.read(*args, **kw)

    def get(self):
        return self.current_scan_value

    #        if self.simulation:
    #            return 'simulation'

    def set(self, v):
        pass


    #            gdict = globals()
    #            if communicator_type in gdict:
    #                return gdict[communicator_type](name='_'.join((self.name, communicator_type)),
    #                                   id_query=self.id_query,
    #                                   id_response=self.id_response
    #                                )
    def post_initialize(self, *args, **kw):
        self.graph.set_y_title(self.graph_ytitle)
        self.setup_scan()
        self.setup_alarms()
        self.setup_scheduler()

        if self.auto_start:
            self.start_scan()


    def get_random_value(self, mi=0, ma=10):
        '''
            convienent method for getting a random integer between min and max
            
            Defaults:
                min=0
                max=10

        '''
        return random.randint(mi, ma)

    def setup_scheduler(self, name=None):

        if self.application:
            if name is None:
                name = self._scheduler_name
            if name is not None:
                sc = self.application.get_service(CommunicationScheduler, 'name=="{}"'.format(name))
                if sc is None:
                    sc = CommunicationScheduler(name=name)
                    self.application.register_service(type(sc), sc)
                self.set_scheduler(sc)

    def set_scheduler(self, s):
        if self._communicator is not None:
            self._communicator.scheduler = s
            #            self._communicator._lock=s._lock

    def _parse_response(self, v):
        return v

    def repeat_command(self, cmd, ntries=2, check_val=None, check_type=None,
                       verbose=True):

        if isinstance(cmd, tuple):
            cmd = self._build_command(*cmd)
        else:
            cmd = self._build_command(cmd)

        for i in range(ntries + 1):
            resp = self._parse_response(self.ask(cmd, verbose=verbose))
            if verbose:
                m = 'repeat command {} response = {} len={} '.format(i + 1,
                                                                     resp,
                                                                     len(str(resp)) if resp is not None else None)
                self.debug(m)
            if check_val is not None:
                if self.simulation:
                    resp = check_val

                if resp == check_val:
                    break
                else:
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

    #===============================================================================
    # scanable interface
    #===============================================================================
    def _scan_hook(self, v):
        for a in self.alarms:
            if a.test_condition(v):
                alarm_msg = a.get_message(v)
                self.warning(alarm_msg)
                manager = self.application.get_service('pychron.social.twitter_manager.TwitterManager')
                if manager is not None:
                    manager.post(alarm_msg)
                break


#========================= EOF ============================================

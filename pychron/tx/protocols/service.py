# ===============================================================================
# Copyright 2015 Jake Ross
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
# ============= standard library imports ========================
import io
import os

from twisted.internet import defer
from twisted.internet.protocol import Protocol

# ============= local library imports  ==========================
from twisted.logger import Logger, jsonFileLogObserver
from pychron.paths import paths
from pychron.tx.errors import InvalidArgumentsErrorCode
from pychron.tx.exceptions import ServiceNameError, ResponseError


def default_err(failure):
    failure.trap(BaseException)
    return failure


def service_err(failure):
    failure.trap(ServiceNameError)
    return failure


def response_err(failure):
    failure.trap(ResponseError)
    return failure


def nargs_err(failure):
    failure.trap(ValueError)
    return InvalidArgumentsErrorCode(str(failure.value))


path = os.path.join(paths.log_dir, 'pps.log.json')
obs = jsonFileLogObserver(io.open(path, 'w'))
logger = Logger(observer=obs)


class ServiceProtocol(Protocol):
    def __init__(self, *args, **kw):
        # super(ServiceProtocol, self).__init__(*args, **kw)
        self._services = {}
        self._delim = ' '

        self.debug = logger.debug
        self.warning = logger.warn
        self.info = logger.info
        self.error = logger.error
        self.critical = logger.critical

    def dataReceived(self, data):
        self.debug('Received n={n}: {data!r}', n=len(data), data=data)
        service = self._get_service(data)
        if service:
            self._get_response(service, data)

            # else:
            #     self.transport.write('Invalid request: {}'.format(data))

            # self.transport.loseConnection()

    def register_service(self, service_name, success, err=None):
        """

        """

        if err is None:
            err = default_err

        d = defer.Deferred()
        if not isinstance(success, (list, tuple)):
            success = (success,)

        for si in success:
            d.addCallback(si)

        d.addCallback(self._prepare_response)
        d.addCallback(self._send_response)

        d.addErrback(nargs_err)
        d.addErrback(service_err)
        d.addErrback(err)

        self._services[service_name] = d

    def _prepare_response(self, data):
        if isinstance(data, bool) and data:
            return 'OK'
        elif data is None:
            return 'No Response'
        else:
            return data

    def _send_response(self, resp):
        resp = str(resp)
        self.debug('Response {data!r}', data=resp)
        self.transport.write(resp)
        self.transport.loseConnection()

    def _get_service(self, data):
        args = data.split(self._delim)
        name = args[0]
        try:
            service = self._services[name]
            return service
        except KeyError:
            raise ServiceNameError(name, data)

    def _get_response(self, service, data):
        delim = self._delim
        data = delim.join(data.split(delim)[1:])
        service.callback(*tuple(data.split(',')))

# ============= EOF =============================================
# def sleep(secs):
#     d = defer.Deferred()
#     reactor.callLater(secs, d.callback, None)
#     return d


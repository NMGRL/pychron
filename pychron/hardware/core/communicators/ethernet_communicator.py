# ===============================================================================
# Copyright 2011 Jake Ross
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
import select

# ============= standard library imports ========================
import socket
import time
from typing import Any, Optional

# ============= enthought library imports =======================
from traits.api import Float

# ============= local library imports  ==========================
from pychron.globals import globalv
from pychron.hardware.core.checksum_helper import computeCRC
from pychron.hardware.core.communicators.communicator import (
    Communicator,
    process_response,
)
from pychron.experiment.telemetry.device_io import record_device_io_event
from pychron.regex import IPREGEX


class MessageFrame(object):
    def __init__(self, message_len=False, nmessage_len=4, checksum=False, nchecksum=4):
        self.nchecksum = nchecksum
        self.checksum = checksum
        self.nmessage_len = nmessage_len
        self.message_len = message_len

    def set_str(self, s):
        """
        L4,-,C4
        """
        if s:
            args = s.split(",")
            if len(args) == 3:
                ml = args[0]
                cs = args[2]
                self.nmessage_len = int(ml[1:])
                self.nchecksum = int(cs[1:])
                self.checksum = True
                self.message_len = True


class Handler(object):
    sock = None
    datasize = 2**12
    address = None
    message_frame = None
    read_terminator = None
    keep_alive = False
    strip = True

    def set_frame(self, f):
        self.message_frame = MessageFrame()
        if f:
            self.message_frame.set_str(f)

    def get_packet(self):
        raise NotImplementedError

    def send_packet(self, p):
        raise NotImplementedError

    def end(self):
        if self.sock:
            try:
                self.sock.close()
            finally:
                self.sock = None

    # private
    # def _recv_into(self, datasize):
    #     buff = bytearray(datasize)
    #     pos = 0
    #     sock = self.sock
    #     while pos < datasize:
    #         cr = sock.recv_into(memoryview(buff)[pos:])
    #         if cr == 0:
    #             raise EOFError
    #         pos += cr
    #     return buff

    def _recvall(self, recv, datasize=None, frame=None, terminator=None):
        """
        recv: callable that accepts 1 argument (datasize). should return a str
        """
        # ss = []
        total = 0

        # disable message len checking
        # msg_len = 1
        # if self.use_message_len_checking:
        # msg_len = 0

        msg_len = None
        nm = -1

        if frame is None:
            frame = self.message_frame

        if frame.message_len:
            msg_len = 0
            nm = frame.nmessage_len

        data = b""
        if datasize is None:
            datasize = self.datasize

        if terminator is None:
            terminator = self.read_terminator

        while 1:
            s = recv(datasize)
            if not s:
                break

            if msg_len is not None:
                msg_len = int(s[:nm], 16)

            total += len(s)
            data += s
            if terminator is not None:
                if data.endswith(terminator):
                    break
            else:
                if msg_len and total >= msg_len:
                    break
                else:
                    break

        if frame.message_len:
            # trim off header
            data = data[nm:]

        if frame.checksum:
            nc = frame.nchecksum
            checksum = data[-nc:]
            data = data[:-nc]
            comp = computeCRC(data)
            if comp != checksum:
                return

        # else:
        #     data = self._recv_into(datasize)

        data = data.decode("utf-8")
        if self.strip:
            data = data.strip()
        return data

    def select_read(self, terminator=None, timeout=3):
        if terminator is None:
            terminator = "#\r\n"

        terminator = terminator.encode("utf-8")

        inputs = [self.sock]
        outputs = []
        readable, writable, exceptional = select.select(inputs, outputs, inputs, timeout)

        buff = bytearray(2**12)
        if readable:
            rsock = readable[0]
            if rsock == self.sock:
                st = time.time()
                while 1:
                    rsock.recv_into(buff)
                    if terminator in buff:
                        data = buff.split(terminator)[0]
                        return data.decode("utf-8")

                    if time.time() - st > timeout:
                        break


class TCPHandler(Handler):
    def open_socket(self, addr, timeout=1.0, **kw):
        self.address = addr
        self.sock = socket.create_connection(addr, timeout=timeout)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, self.keep_alive)
        self.sock.settimeout(timeout)

    def get_packet(self, datasize=None, message_frame=None):
        return self._recvall(self.sock.recv, datasize=datasize, frame=message_frame)

    def readline(self, terminator):
        return self._recvall(self.sock.recv, terminator=terminator, datasize=1)

    def send_packet(self, p):
        self.sock.sendall(p.encode("utf-8"))


class UDPHandler(Handler):
    def open_socket(self, addr, timeout=1.0, bind=False):
        self.address = addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if globalv.communication_simulation:
            timeout = 0.01
        self.sock.settimeout(timeout)

        try:
            if bind:
                addr = "", addr[1]
                self.sock.bind(addr)
        except BaseException:
            self.end()
            raise

    def get_packet(self, datasize=None, message_frame=None):
        def recv(ds):
            rx, _ = self.sock.recvfrom(ds)
            return rx

        return self._recvall(recv, datasize=datasize, frame=message_frame)

    def send_packet(self, p):
        self.sock.sendto(p.encode("utf-8"), self.address)


class EthernetCommunicator(Communicator):
    """
    Communicator of UDP or TCP.
    """

    host = None
    port = None
    read_port = None
    handler = None
    read_handler = None
    kind = "UDP"
    test_cmd = None
    use_end = True
    verbose = False
    error_mode = False
    message_frame = ""
    timeout = Float(1.0)
    strip = True
    # default_timeout = 3
    default_datasize = 2**12

    _comms_report_attrs = (
        "host",
        "port",
        "read_port",
        "kind",
        "timeout",
        "default_datasize",
    )

    @property
    def address(self):
        return "{}://{}:{}".format(self.kind, self.host, self.port)

    def load(self, config, path):
        """ """
        super(EthernetCommunicator, self).load(config, path)

        self.host = self.config_get(config, "Communications", "host")
        if self.host != "localhost" and not IPREGEX.match(self.host):
            try:
                result = socket.getaddrinfo(self.host, 0, 0, 0, 0)
                if result:
                    for family, kind, a, b, host in result:
                        if family == socket.AF_INET and kind == socket.SOCK_STREAM:
                            self.host = host[0]
            except socket.gaierror:
                self.debug_exception()

        # self.host = 'localhost'
        self.port = self.config_get(config, "Communications", "port", cast="int")
        self.read_port = self.config_get(
            config, "Communications", "read_port", cast="int", optional=True
        )
        self.timeout = self.config_get(
            config,
            "Communications",
            "timeout",
            cast="float",
            optional=True,
            default=1.0,
        )
        self.kind = self.config_get(config, "Communications", "kind", optional=True)
        self.test_cmd = self.config_get(
            config, "Communications", "test_cmd", optional=True, default=""
        )
        self.use_end = self.config_get(
            config,
            "Communications",
            "use_end",
            cast="boolean",
            optional=True,
            default=True,
        )
        self.strip = self.config_get(
            config,
            "Communications",
            "strip",
            cast="boolean",
            optional=True,
            default=True,
        )
        self.message_frame = self.config_get(
            config, "Communications", "message_frame", optional=True, default=""
        )
        # self.default_timeout = self.config_get(
        #     config,
        #     "Communications",
        #     "default_timeout",
        #     cast="int",
        #     optional=True,
        #     default=3,
        # )
        self.default_datasize = self.config_get(
            config,
            "Communications",
            "default_datasize",
            cast="int",
            optional=True,
            default=2**12,
        )
        if self.kind is None:
            self.kind = "UDP"

        return True

    def open(self, *args, **kw):
        for k in ("host", "port", "message_frame", "kind"):
            if k in kw:
                setattr(self, k, kw[k])

        if self.transport_adapter is not None:
            self.simulation = True
            return self.transport_adapter.open(**kw)

        return self.test_connection()

    def _io_device_name(self) -> str:
        return getattr(self, "name", None) or self.address or "ethernet_communicator"

    def _io_payload(self, operation: str, **payload: Any) -> dict[str, Any]:
        base = {
            "address": self.address,
            "kind": self.kind,
            "backend": self.backend,
            "operation_type": operation,
        }
        base.update(payload)
        return base

    def _command_preview(self, cmd: Any) -> Optional[str]:
        if cmd is None:
            return None
        text = str(cmd).strip()
        if len(text) > 96:
            text = "{}...".format(text[:93])
        return text

    def _record_io_checkpoint(
        self,
        operation: str,
        *,
        stage: str,
        success: Optional[bool] = None,
        duration_seconds: Optional[float] = None,
        error: Optional[str] = None,
        flush: bool = False,
        **payload: Any,
    ) -> None:
        record_device_io_event(
            self._io_device_name(),
            operation,
            success=success,
            duration_seconds=duration_seconds,
            payload=self._io_payload(operation, **payload),
            error=error,
            component="ethernet_communicator",
            stage=stage,
            flush=flush,
        )

    def _notify_health(
        self,
        success: bool,
        operation: str,
        *,
        error: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> None:
        callback_name = "health_success_callback" if success else "health_failure_callback"
        callback = getattr(self, callback_name, None)
        if callable(callback):
            callback(
                operation,
                error=error,
                duration_seconds=duration_seconds,
                device_name=getattr(self, "health_device_name", self._io_device_name()),
            )

    def test_connection(self) -> bool:
        if self.transport_adapter is not None:
            self.simulation = True
            return self.transport_adapter.connected or self.transport_adapter.open()

        self.simulation = False

        # with self._lock:
        #     handler = self.get_handler()

        # send a test command so see if wer have connection
        cmd = self.test_cmd

        if cmd:
            self.debug("sending test command {}".format(cmd))
            r = self.ask(cmd)
            if r is None:
                self.simulation = True

                # if handler:
                #     if handler.send_packet(cmd):
                #         r = handler.get_packet(cmd)
                #         if r is None:
                #             self.simulation = True
                #     else:
                #         self.simulation = True
                # else:
                #     self.simulation = True
        # ret = not self.simulation and handler is not None
        ret = not self.simulation
        self._notify_health(ret, "test_connection", error=None if ret else "test connection failed")
        return ret

    def get_read_handler(self, handler, **kw):
        if self.read_port:
            if self.read_handler:
                handler = self.read_handler
            else:
                handler = self.get_handler(addrs=(self.host, self.read_port), bind=True, **kw)
                self.read_handler = handler

        return handler

    def get_handler(self, addrs=None, timeout=None, bind=False):
        if timeout is None:
            timeout = self.timeout
        if addrs is None:
            addrs = (self.host, self.port)

        try:
            h = self.handler
            if h is None or h.address != addrs:
                if self.kind.lower() == "udp":
                    h = UDPHandler()
                else:
                    h = TCPHandler()

                if self.read_terminator:
                    h.read_terminator = self.read_terminator.encode("utf-8")
                # self.debug('get handler cmd={}, {},{} {}'.format(cmd.strip() if cmd is not None else '---', self.host,
                #                                                  self.port, timeout))
                h.keep_alive = not self.use_end
                h.open_socket(addrs, timeout=timeout or 1, bind=bind)
                h.set_frame(self.message_frame)
                h.datasize = self.default_datasize
                h.strip = self.strip
                self.handler = h
            return h
        except socket.error as e:
            self.debug(
                "Get Handler {}. timeout={}. comms simulation={}".format(
                    str(e), timeout, globalv.communication_simulation
                )
            )
            self.error_mode = True
            if bind:
                self.read_handler = None
            else:
                self.handler = None

    def ask(
        self,
        cmd: Any,
        retries: int = 3,
        verbose: bool = True,
        quiet: bool = False,
        info: Any = None,
        timeout: Any = None,
        message_frame: Any = None,
        delay: Any = None,
        use_error_mode: bool = True,
        *args: Any,
        **kw: Any,
    ) -> Any:
        """
        @param cmd: ASCII text to send
        @param retries: number of retries if command fails
        @param verbose: add to log
        @param quiet: if true do not log the response
        @param info: str to add to response
        @param timeout: timeout in seconds
        @param message_frame: MessageFrame object
        @param delay: delay in seconds to wait before a `cmd` is sent

        """

        operation_started_at = time.time()
        command_preview = self._command_preview(cmd)
        self._record_io_checkpoint(
            "ask",
            stage="start",
            flush=True,
            command=command_preview,
            retries=retries,
            timeout=timeout,
        )

        if self.transport_adapter is not None:
            payload = "{}{}".format(cmd, self.write_terminator)
            with self._lock:
                r = self.transport_adapter.request(
                    payload,
                    timeout=timeout,
                    message_frame=message_frame,
                    delay=delay,
                )
                re = process_response(r) if r is not None else "ERROR: replay returned no response"
                if verbose or (self.verbose and not quiet):
                    self.log_response(payload, re, info)
                self._record_io_checkpoint(
                    "ask",
                    stage="end",
                    success=r is not None,
                    duration_seconds=time.time() - operation_started_at,
                    command=command_preview,
                    timeout=timeout,
                    response_preview=self._command_preview(re),
                )
                self._notify_health(
                    r is not None,
                    "ask",
                    error=None if r is not None else re,
                    duration_seconds=time.time() - operation_started_at,
                )
                return r

        if self.simulation:
            if verbose:
                self.info("no handle    {}".format(cmd.strip()))
            self._record_io_checkpoint(
                "ask",
                stage="end",
                success=True,
                duration_seconds=time.time() - operation_started_at,
                command=command_preview,
                simulation=True,
            )
            return

        cmd = "{}{}".format(cmd, self.write_terminator)

        r = None
        with self._lock:
            if use_error_mode and self.error_mode:
                retries = 2

            if timeout is None:
                timeout = self.timeout

            re = "ERROR: Connection refused: {}, timeout={}".format(self.address, timeout)
            for i in range(retries):
                r = self._ask(
                    cmd,
                    timeout=timeout,
                    message_frame=message_frame,
                    delay=delay,
                    use_error_mode=use_error_mode,
                )
                if r is not None:
                    break
                else:
                    time.sleep(0.025)
                    self.debug("doing retry {}".format(i))
                    # else:
                    #     self._reset_connection()

            if r is not None:
                re = process_response(r)
            # else:
            #     self.error_mode = True

            if self.use_end:
                self.reset()

            if verbose or (self.verbose and not quiet):
                self.log_response(cmd, re, info)

        self._record_io_checkpoint(
            "ask",
            stage="end",
            success=r is not None,
            duration_seconds=time.time() - operation_started_at,
            command=command_preview,
            timeout=timeout,
            retries=retries,
            response_preview=self._command_preview(re),
            error=None if r is not None else re,
        )
        self._notify_health(
            r is not None,
            "ask",
            error=None if r is not None else re,
            duration_seconds=time.time() - operation_started_at,
        )
        return r

    def reset(self):
        if self.transport_adapter is not None:
            self.transport_adapter.reset()
            return
        if self.handler:
            self.handler.end()
        if self.read_handler:
            self.read_handler.end()
        self._reset_connection()

    def select_read(self, *args: Any, **kw: Any) -> Any:
        if self.transport_adapter is not None:
            return self.transport_adapter.select_read(*args, **kw)

        timeout = self.timeout
        handler = self.get_handler(timeout=timeout)
        if handler:
            handler = self.get_read_handler(handler, timeout=timeout)

        return handler.select_read(*args, **kw)

    def readline(self, terminator: Any = b"\r\n") -> Any:
        if self.transport_adapter is not None:
            return self.transport_adapter.readline(terminator=terminator)

        operation_started_at = time.time()
        terminator_preview = self._command_preview(terminator)
        self._record_io_checkpoint(
            "readline", stage="start", flush=True, terminator=terminator_preview
        )
        timeout = self._reset_error_mode()

        handler = self.get_handler(timeout=timeout)
        if handler:
            handler = self.get_read_handler(handler, timeout=timeout)

        if handler:
            if isinstance(terminator, str):
                terminator = terminator.encode("utf8")

            try:
                response = handler.readline(terminator)
                self._record_io_checkpoint(
                    "readline",
                    stage="end",
                    success=True,
                    duration_seconds=time.time() - operation_started_at,
                    terminator=terminator_preview,
                    response_preview=self._command_preview(response),
                )
                self._notify_health(
                    True, "readline", duration_seconds=time.time() - operation_started_at
                )
                return response
            except socket.timeout as e:
                self.warning("read. read packet. error: {}".format(e))
                self.error_mode = True
                self._record_io_checkpoint(
                    "readline",
                    stage="end",
                    success=False,
                    duration_seconds=time.time() - operation_started_at,
                    terminator=terminator_preview,
                    error=str(e),
                )
                self._notify_health(
                    False,
                    "readline",
                    error=str(e),
                    duration_seconds=time.time() - operation_started_at,
                )

    def read(self, datasize: Any = None, *args: Any, **kw: Any) -> Any:
        if self.transport_adapter is not None:
            return self.transport_adapter.read(datasize=datasize, *args, **kw)

        operation_started_at = time.time()
        self._record_io_checkpoint("read", stage="start", flush=True, datasize=datasize)
        for i in range(3):
            with self._lock:
                timeout = self._reset_error_mode()

                handler = self.get_handler(timeout=timeout)
                if handler:
                    handler = self.get_read_handler(handler, timeout=timeout)

                if handler:
                    try:
                        response = handler.get_packet(datasize=datasize)
                        self._record_io_checkpoint(
                            "read",
                            stage="end",
                            success=True,
                            duration_seconds=time.time() - operation_started_at,
                            datasize=datasize,
                            timeout=timeout,
                            response_preview=self._command_preview(response),
                        )
                        self._notify_health(
                            True, "read", duration_seconds=time.time() - operation_started_at
                        )
                        return response
                    except socket.timeout as e:
                        self.warning("read. read packet. error: {}".format(e))
                        self.error_mode = True
                        self._record_io_checkpoint(
                            "read",
                            stage="retry",
                            success=False,
                            duration_seconds=time.time() - operation_started_at,
                            datasize=datasize,
                            timeout=timeout,
                            error=str(e),
                            attempt=i + 1,
                        )
                        self._notify_health(
                            False,
                            "read",
                            error=str(e),
                            duration_seconds=time.time() - operation_started_at,
                        )

            time.sleep(timeout)

        else:
            self._record_io_checkpoint(
                "read",
                stage="end",
                success=False,
                duration_seconds=time.time() - operation_started_at,
                datasize=datasize,
                error="empty response after retries",
            )
            self._notify_health(
                False,
                "read",
                error="empty response after retries",
                duration_seconds=time.time() - operation_started_at,
            )
            return ""

    def tell(self, cmd: Any, verbose: bool = True, quiet: bool = False, info: Any = None) -> None:
        if self.transport_adapter is not None:
            payload = "{}{}".format(cmd, self.write_terminator)
            with self._lock:
                self.transport_adapter.write(payload)
                if verbose or self.verbose and not quiet:
                    self.log_tell(payload, info)
            return

        operation_started_at = time.time()
        command_preview = self._command_preview(cmd)
        self._record_io_checkpoint("tell", stage="start", flush=True, command=command_preview)
        with self._lock:
            handler = self.get_handler()
            if handler:
                try:
                    cmd = "{}{}".format(cmd, self.write_terminator)
                    handler.send_packet(cmd)
                    if verbose or self.verbose and not quiet:
                        self.log_tell(cmd, info)
                    self._record_io_checkpoint(
                        "tell",
                        stage="end",
                        success=True,
                        duration_seconds=time.time() - operation_started_at,
                        command=command_preview,
                    )
                    self._notify_health(
                        True, "tell", duration_seconds=time.time() - operation_started_at
                    )
                except socket.error as e:
                    self.warning("tell. send packet. error: {}".format(e))
                    self.error_mode = True
                    self._record_io_checkpoint(
                        "tell",
                        stage="end",
                        success=False,
                        duration_seconds=time.time() - operation_started_at,
                        command=command_preview,
                        error=str(e),
                    )
                    self._notify_health(
                        False,
                        "tell",
                        error=str(e),
                        duration_seconds=time.time() - operation_started_at,
                    )

    # private
    def _reset_connection(self):
        self.handler = None
        self.read_handler = None
        self.error_mode = False

    def _reset_error_mode(self, timeout=None, use_error_mode=True):
        if self.error_mode:
            if self.handler:
                self.handler.end()
            if self.read_handler:
                self.read_handler.end()

            self.handler = None
            self.read_handler = None

            if use_error_mode:
                timeout = 0.5

        if timeout is None:
            timeout = self.timeout

        self.error_mode = False
        return timeout

    def _ask(self, cmd, timeout=None, message_frame=None, delay=None, use_error_mode=True):
        timeout = self._reset_error_mode(timeout, use_error_mode)

        handler = self.get_handler(timeout=timeout)
        if not handler:
            return

        try:
            handler.send_packet(cmd)

            if delay:
                time.sleep(delay)

            handler = self.get_read_handler(handler, timeout=timeout)
            try:
                return handler.get_packet(message_frame=message_frame)
            except socket.error as e:
                self.debug_exception()
                self.warning(
                    "ask. get packet for {}. error: {} address: {}".format(cmd, e, handler.address)
                )
                self.error_mode = True
        except socket.error as e:
            self.warning("ask. send packet. error: {} address: {}".format(e, handler.address))
            self.error_mode = True


# ============= EOF ====================================

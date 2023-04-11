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


# =============enthought library imports=======================
# =============standard library imports =======================
import binascii
import struct

from pychron.hardware.core.checksum_helper import computeCRC

# =============local library imports  =========================
from pychron.hardware.core.communicators.serial_communicator import SerialCommunicator
from pychron.hardware.core.exceptions import CRCError

WRITE_FUNCTION_CODE = "06"
WRITE_MULTIPLE_FUNCTION_CODE = "10"
READ_FUNCTION_CODE = "03"


class ModbusCommunicator(SerialCommunicator):
    """
    modbus message syntax
    [Device address][function code][data][error check]
    """

    slave_address = "01"
    device_word_order = "low_high"

    def load(self, config, path):
        """ """
        super(ModbusCommunicator, self).load(config, path)
        self.set_attribute(config, "slave_address", "Communications", "slave_address")

    def write(
        self, register, value, nregisters=1, response_type="register_write", **kw
    ):
        """ """
        if nregisters == 1:
            return self.set_single_register(register, value, response_type, **kw)
        else:
            return self.set_multiple_registers(
                register, nregisters, value, response_type, **kw
            )

    def tell(self, *args, **kw):
        return self.write(*args, **kw)

    def read(self, register, response_type="float", nregisters=1, **kw):
        """ """
        if "nbytes" not in kw:
            if response_type == "int":
                kw["nbytes"] = 7
            elif response_type == "float":
                kw["nbytes"] = 8

        return self.read_holding_register(register, nregisters, response_type, **kw)

    def _execute_request(self, args, response_type, **kw):
        """ """
        cmd = "".join([self.slave_address] + args)

        # convert hex string into list of ints
        cmdargs = self._parse_hexstr(cmd, return_type="int")

        # calculate the CRC and append to message
        crc = computeCRC(cmdargs)
        cmd += crc

        kw["is_hex"] = True

        if self.scheduler is not None:
            resp = self.scheduler.schedule(self.ask, args=(cmd,), kwargs=kw)
        else:
            resp = self.ask(cmd, **kw)

        return self._parse_response(cmd, resp, response_type)

    def _parse_hexstr(self, hexstr, return_type="hex"):
        """ """

        if isinstance(hexstr, bytes):
            if return_type == "int":

                def func(b):
                    return int.from_bytes([b], "big")

            else:

                def func(b):
                    return b

            return [func(b) for b in hexstr]
        else:
            gen = range(0, len(hexstr), 2)
            if return_type == "int":
                return [int(hexstr[i : i + 2], 16) for i in gen]
            else:
                return [hexstr[i : i + 2] for i in gen]

    def _parse_response(self, cmd, resp, response_type):
        """ """
        # self.debug('asdf {} {}'.format(cmd, resp))
        if resp is not None and resp is not "simulation":
            args = self._parse_hexstr(resp)
            if args:
                # self.debug('args={}'.format(args))
                if bytes(args[:2]) != bytes.fromhex(cmd[:4]):
                    self.warning(
                        "{} != {}     {} >> {}".format(cmd[:4], args[:2], cmd, resp)
                    )
                    return
            else:
                return

            # check the crc
            crc = args[-2:]
            calc_crc = computeCRC(args[:-2])
            calc_crc = [int(calc_crc[:2], 16), int(calc_crc[2:], 16)]
            if not crc == calc_crc:
                msg = "Returned CRC ({}) does not match calculated ({})".format(
                    crc, calc_crc
                )
                self.warning(msg)
                raise CRCError("{} {}".format(cmd, msg))
            else:
                if response_type == "register_write":
                    return True
                # ndata = int(args[2], 16)
                ndata = int.from_bytes([args[2]], "big")
                dataargs = args[3 : 3 + ndata]
                if len(dataargs) < ndata:
                    ndata = 4
                    dataargs = args[3 : 3 + ndata]

                if ndata > 2:
                    data = []
                    for i in range(ndata // 4):
                        s = 4 * i
                        low_word = "".join(
                            ["{:02X}".format(d) for d in dataargs[s : s + 2]]
                        )
                        high_word = "".join(
                            ["{:02X}".format(d) for d in dataargs[s + 2 : s + 4]]
                        )
                        # low_word = ''.join(dataargs[s:s + 2])
                        # high_word = ''.join(dataargs[s + 2:s + 4])

                        if self.device_word_order == "low_high":
                            """
                            dataargs in low word - high word order
                            1234 5678
                            want high word -low word order
                            5678 1234
                            """
                            di = "".join([high_word, low_word])
                        else:
                            di = "".join([low_word, high_word])
                        data.append(di)

                    data = "".join(data)

                if response_type == "float":
                    fmt_str = "!" + "f" * (ndata // 4)
                    resp = struct.unpack(fmt_str, bytes.fromhex(data))
                    # return a single value
                    if ndata == 4:
                        return resp[0]
                    else:
                        # return a list of values
                        return resp

                else:
                    data = args[3 : 3 + ndata]
                    return int.from_bytes(data, "big")
                    # return int(data, 16)

    def set_multiple_registers(self, startid, nregisters, value, response_type, **kw):
        """ """

        data_address = "{:04X}".format(int(startid))
        n = "{:04X}".format(int(nregisters))
        nbytes = "{:02X}".format(int(nregisters * 2))

        if isinstance(value, tuple):
            value = "".join(["{:04X}".format(vi) for vi in value])
        else:
            # convert decimal value to 32-bit float
            binstr = struct.pack("!f", value)

            # convert binary string to a ascii hex string
            hexstr = binascii.hexlify(binstr)
            if self.device_word_order == "low_high":
                high = hexstr[:4]
                low = hexstr[4:]

                # flip order of words
                # value = ''.join([low, high])
                value = low + high
            else:
                value = hexstr
            value = value.decode("utf8")

        return self._execute_request(
            [WRITE_MULTIPLE_FUNCTION_CODE, data_address, n, nbytes, value],
            response_type,
            **kw
        )

    def set_single_register(self, rid, value, response_type, **kw):
        """ """
        register_addr = "{:04X}".format(int(rid))
        value = "{:04X}".format(int(value))
        return self._execute_request(
            [WRITE_FUNCTION_CODE, register_addr, value], response_type, **kw
        )

    def read_holding_register(self, holdid, nregisters, response_type, **kw):
        """ """

        data_address = "{:04X}".format(holdid)
        n = "{:04X}".format(nregisters)
        return self._execute_request(
            [READ_FUNCTION_CODE, data_address, n], response_type, **kw
        )


# def read_input_status(self, inputid, ninputs):
#        '''
#        '''
#        func_code = '02'
#        data_address = '{:04X}'.format(inputid - 10001)
#        n = '{04x}'.format(ninputs)
#        return self._execute_request([func_code, data_address, n])
# ============= EOF =====================================

# ===============================================================================
# Copyright 2021 ross
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
try:
    from pymodbus.constants import Endian
    from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
except ImportError:
    pass


class ModbusMixin:
    """
    simple mapper of the Modbus commands
    """

    def _read_float(self, register, *args, **kw):
        result = self._read_holding_registers(int(register), 2, *args, **kw)
        return self._decode_float(result)

    def _read_input_float(self, register, *args, **kw):
        result = self._read_input_registers(int(register), 2, *args, **kw)
        return self._decode_float(result)

    def _decode_float(self, result):
        decoder = BinaryPayloadDecoder.fromRegisters(
            result.registers, Endian.Big, wordorder=Endian.Little
        )
        return decoder.decode_32bit_float()

    def _get_payload(self, value, is_float=True):
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
        if is_float:
            builder.add_32bit_float(value)
        else:
            builder.add_32bit_int(int(value))
        payload = builder.build()
        return payload

    def _write_int(self, register, value, *args, **kw):
        payload = self._get_payload(value, is_float=False)
        self.debug(
            "writing int register={} payload={} value={}".format(
                register, payload, value
            )
        )
        self._write_registers(register, payload, skip_encode=True)

    def _write_float(self, register, value, *args, **kw):
        payload = self._get_payload(value)
        self.debug(
            "writing float register={} payload={} value={}".format(
                register, payload, value
            )
        )
        self._write_registers(register, payload, skip_encode=True)

    def _func(self, funcname, *args, **kw):
        if self.communicator:
            self.debug("ModbusMixin: {} {} {}".format(funcname, args, kw))
            return getattr(self.communicator, funcname)(*args, **kw)

    def _read_coils(self, *args, **kw):
        return self._func("read_coils", *args, **kw)

    def _write_coil(self, *args, **kw):
        return self._func("write_coil", *args, **kw)

    def _read_holding_registers(self, *args, **kw):
        return self._func("read_holding_registers", *args, **kw)

    def _read_input_registers(self, *args, **kw):
        return self._func("read_input_registers", *args, **kw)

    def _write_register(self, *args, **kw):
        return self._func("write_register", *args, **kw)

    def _write_registers(self, *args, **kw):
        return self._func("write_registers", *args, **kw)


# ============= EOF =============================================

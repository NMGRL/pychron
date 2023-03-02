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


from __future__ import absolute_import
from __future__ import print_function

from six.moves import range


def computeBCC(data_str):
    """
    data str= ASCII string

    XOR each chr in string

    returns a two char ASCII string
    """
    bcc = 0

    for d in data_str:
        # print d
        # d = ord(d)
        #        bcc = bcc ^ ord(d)
        bcc = bcc ^ ord(d)
    #    print bcc
    bcc = bcc & 127
    #    print bcc
    return bcc


#    return '%02X' % bcc


def __generate_crc16_table(poly, reflect=True):
    """Generates a crc16 lookup table

    .. note:: This will only be generated once
    """

    if reflect:
        poly = int("{:016b}".format(poly)[::-1], 2)

    table = []
    for i in range(0x100):  # 256
        crc = 0
        for _ in range(0x8):
            if (i ^ crc) & 0x1:
                crc = (crc >> 0x1) ^ poly
            else:
                crc >>= 0x1
            i >>= 0x1
        table.append(crc)

    return table


MODBUS_CRC_TABLE = __generate_crc16_table(0x8005)


def computeCRC(data, start_crc=0xFFFF):
    """Computes a crc16 on the passed in data.
    @param data The data to create a crc16 of

    The difference between modbus's crc16 and a normal crc16
    is that modbus starts the crc value out at 0xffff.

    Accepts a string or a integer list
    """
    crc = start_crc
    if isinstance(data, str):
        data = [ord(d) for d in data]

    for a in data:
        crc = ((crc >> 8) & 0xFF) ^ MODBUS_CRC_TABLE[(crc ^ a) & 0xFF]

    # flip lo and hi bits
    crc = "{:04x}".format(crc)
    crc = "{}{}".format(crc[2:], crc[:2])
    return crc


def checkCRC(data, check):
    """Checks if the data matches the passed in CRC
    @param data The data to create a crc16 of
    @param check The CRC to validate
    """
    return computeCRC(data) == check


if __name__ == "__main__":
    #    s=chr(2)+'000200050007'+chr(3)
    # s = '000200050007' + chr(3)
    # s = '000B0001' + chr(3)
    # s = '000204B0001' + chr(3)
    # print chr(computeBCC(s))

    # print(computeCRC('A1,B0'))
    c = computeCRC("hi!a")

    print(c, "{:04b}".format(int(c, 16)))
# ============= EOF ====================================

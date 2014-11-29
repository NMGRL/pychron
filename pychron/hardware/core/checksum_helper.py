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



def computeBCC(data_str):
    '''
        data str= ASCII string
        
        XOR each chr in string 
        
        returns a two char ASCII string
    '''
    bcc = 0

    for d in data_str:
#        print d
#        d = ord(d)
#        bcc = bcc ^ ord(d)
        bcc = bcc ^ ord(d)
#    print bcc
    bcc = bcc & 127
#    print bcc
    return bcc
#    return '%02X' % bcc


def __generate_crc16_table():
    '''
    '''
    ''' Generates a crc16 lookup table

    .. note:: This will only be generated once
    '''
    result = []
    for byte in range(256):
        crc = 0x0000
        for _bit in range(8):
            if (byte ^ crc) & 0x0001:
                crc = (crc >> 1) ^ 0xa001
            else:
                crc >>= 1
            byte >>= 1
        result.append(crc)
    return result
__crc16_table = __generate_crc16_table()


def computeCRC(data, start_crc=0xffff):
    '''
    '''
    ''' Computes a crc16 on the passed in data.
    @param data The data to create a crc16 of

    The difference between modbus's crc16 and a normal crc16
    is that modbus starts the crc value out at 0xffff.

    Accepts a string or a integer list
    '''
    crc = start_crc
    pre = lambda x: x
    if isinstance(data, str):
        pre = lambda x: ord(x)

    for a in data:
        crc = ((crc >> 8) & 0xff) ^ __crc16_table[
               (crc ^ pre(a)) & 0xff]

    # flip lo and hi bits
    crc = '%04x' % crc

    crc = '%s%s' % (crc[2:], crc[:2])
    return crc


def checkCRC(data, check):
    '''
        @type check: C{str}
        @param check:
    '''
    ''' Checks if the data matches the passed in CRC
    @param data The data to create a crc16 of
    @param check The CRC to validate
    '''
    return computeCRC(data) == check

if __name__ == '__main__':
#    s=chr(2)+'000200050007'+chr(3)
    s = '000200050007' + chr(3)
    s = '000B0001' + chr(3)
    s = '000204B0001' + chr(3)
    print chr(computeBCC(s))
# ============= EOF ====================================

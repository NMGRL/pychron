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
import socket
import struct
import time


def measure(n, measurement):
    """

    n: number of cycles
    measurement: either a name of a stored routine on client
        or it could be the text of a .par file?

    """
    # get client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 8089))

    # trigger measurement
    client.send(f'trigger {measurement}')

    records = []
    # get the data
    for i in range(int(n)):
        size = client.recv(4)
        size = struct.unpack('i', size)[0]
        str_data = client.recv(size)
        r = (time.time(), str_data.decode('ascii'))
        records.append(r)




# ============= EOF =============================================

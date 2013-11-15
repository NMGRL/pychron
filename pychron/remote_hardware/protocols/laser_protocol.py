'''
Copyright 2011 Jake Ross

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing:None, software
distributed under the License is distributed on an "AS IS" BASIS:None,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND:None, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

#=============enthought library imports=======================
#============= standard library imports ========================
#============= local library imports  ==========================


class LaserProtocol:
    commands = {'ReadLaserPower': None,
        'GetLaserStatus': None,
        'Enable': None,
        'Disable': None,
        'SetXY': '1,1',
        'SetX': '1,1',
        'SetY': '1',
        'SetZ': '1',
        'GetPosition': None,
        'GetDriveMoving': None,
        'GetXMoving': None,
        'GetYMoving': None,
        'GetZMoving': None,
        'StopDrive': None,
        'SetDriveHome': None,
        'SetHomeX': None,
        'SetHomeY': None,
        'SetHomeZ': None,
        'GoToHole': '1',
        'GetJogProcedures': None,
        'DoJog': ('addc', 10),
        'AbortJog': None,
        'SetBeamDiameter': '1',
        'GetBeamDiameter': None,
        'SetZoom': '1',
        'GetZoom': None,
        'SetSampleHolder': 'Ba',
        'GetSampleHolder': None,
        'SetLaserPower': '1'
        }

#============= EOF =====================================

# # ===============================================================================
# # Copyright 2018 ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# # http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# # ===============================================================================
#
# # ============= enthought library imports =======================
#
# # ============= standard library imports ========================
#
# # ============= local library imports  ==========================
#
# # ============= views ===================================
# from pychron.hardware.gauges.base_gauge import BaseGauge
#
#
# class BasePfeifferGauge(BaseGauge):
#
#     def _build_query(self, addr, typetag):
#
#         if typetag == 'pressure':
#             s = 'PR'
#         rs = '{}{};'.format(s, addr)
#         return rs
#
#     def _build_command(self, addr, typetag, value):
#
#         base = '{},{},{},{},{},{},{};'
#         if typetag == 'power':
#             tag = 'SEN'
#
#             if value.lower() in ('on', '2'):
#                 value = '2'
#             elif value.lower() in ('off', '1'):
#                 value = '1'
#         elif typetag == 'degas':
#             tag = 'DGS'
#             if value.lower() in ('on', '1'):
#                 value = '1'
#             elif value in ('off', '0'):
#                 value = '0'
#         else:
#             return
#
#         return base.format(tag, *[(value if addr == i else '0') for i in range(6)])
#
#     def _parse_response(self, type_, raw):
#         """
#         parse a serial response
#
#         @type_ type_: C{str}
#         @param type_: the response type_
#         @type_ raw: C{str}
#         @param raw: the raw response C{str}
#         @rtype: C{str or boolean}
#         @return: a float for pressure, boolean otherwise
#         """
#
#         if self.simulation:
#             return float(self.get_random_value(0, 10))
#
#         if raw is None:
#             return
#
#         data = raw.split(';')
#         i = 0 if len(data) <= 2 else len(data) - 2
#
#         value = data[i]
#         si = value.find('ACK')
#         if si == -1:
#             self.warning('{}'.format(raw))
#             return
#         else:
#             si += 3
#
#         if type_ in ('pressure', 'setpoint_value'):
#             v = value[si:]
#             try:
#
#                 return float(v)
#             except ValueError as e:
#                 self.warning(e)
#                 return
#
#         elif type_ in ('filament', 'setpoint_enable'):
#             return value[si:] == 'ON'
#
# # ============= EOF ====================================

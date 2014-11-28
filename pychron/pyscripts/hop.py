# # ===============================================================================
# # Copyright 2013 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# # ===============================================================================
#
# #============= enthought library imports =======================
# from traits.api import HasTraits, Str, Int
# from traitsui.api import View, HGroup, UItem
# #============= standard library imports ========================
# #============= local library imports  ==========================
#
# DETORDER = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
# class Hop(HasTraits):
#     position = Str
#     detectors = Str
#     counts = Int
#     def to_string(self):
#         if not (self.position and self.detectors and self.counts):
#             return
#
#         import string
#
#         rpos = self.position
#         k = ''
#         for pii in rpos:
#             if pii in string.ascii_letters:
#                 k += pii
#
#         rrpos = rpos
#         for ai in string.ascii_letters:
#             rrpos = rrpos.replace(ai, '')
#
#         dets = self.detectors.split(',')
#         rdet = dets[0]
#         if not rdet in DETORDER:
#             return
#
#         refidx = DETORDER.index(rdet)
#
#         poss = []
#         for di in dets:
#             di = di.strip()
#             if not di in DETORDER:
#                 return
#
#             moff = DETORDER.index(di)
#             pos = int(rrpos) + refidx - moff
#             pos = '{}{}'.format(k, pos)
#             poss.append((pos, di))
#
#         ss = []
#         for i, (pi, di) in enumerate(poss):
#             si = '{}:{}'.format(pi, di)
#             if i < len(poss) - 1:
#                 si += ','
#                 si = '{:<10s}'.format(si)
#             ss.append(si)
#         ss = ''.join(ss)
#
#         ss = "'{}',".format(ss)
#         return "{:<30s}{}".format(ss, self.counts)
#
#     def traits_view(self):
#         v = View(HGroup(UItem('position', width= -60),
#                         UItem('detectors', width=250),
#                         UItem('counts', width= -60)
#                         )
#                  )
#         return v
# # ============= EOF =============================================

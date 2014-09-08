# #===============================================================================
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
# #===============================================================================
#
# #============= enthought library imports =======================
# from traits.api import HasTraits, Int, List, String, Float, Bool, \
# on_trait_change, Str, Any, Instance
# from traitsui.api import View, Item, VGroup, Group, HGroup, Label, Spring, \
#     UItem, ListEditor, InstanceEditor, spring, EnumEditor, TableEditor
# from traitsui.table_column import ObjectColumn
# from traitsui.extras.checkbox_column import CheckboxColumn
# #============= standard library imports ========================
# import re
# import os
# from ConfigParser import ConfigParser
# #============= local library imports  ==========================
# from pychron.core.helpers.filetools import to_bool
# from pychron.loggable import Loggable
# from pychron.pychron_constants import NULL_STR, FIT_TYPES
# from pychron.paths import paths
# from pychron.pyscripts.parameters import MeasurementAction, Detector, Hop, \
#     MeasurementTruncation, MeasurementTermination
#
#
# class FitBlock(HasTraits):
#     start = Str(enter_set=True, auto_set=False)
#     end = Str(enter_set=True, auto_set=False)
#     detectors = List
#
#     def traits_view(self):
#         editor = TableEditor(
#             sortable=False,
#             reorderable=False,
#             columns=[
#                 ObjectColumn(name='label',
#                              editable=False,
#                              label='Det.'),
#                 CheckboxColumn(name='use', label='Use'),
#                 ObjectColumn(name='isotope',
#                              editor=EnumEditor(name='isotopes')
#                 ),
#                 ObjectColumn(name='fit',
#                              editor=EnumEditor(values=[NULL_STR] + FIT_TYPES)
#                 ),
#             ]
#         )
#         v = View(
#             HGroup(Item('start'), Item('end')),
#             UItem('detectors', editor=editor))
#         return v
#
#     def to_string(self):
#         s = self.start
#         if not s:
#             s = None
#
#         e = self.end
#         if not e:
#             e = None
#
#         f = ','.join(["'{}'".format(di.fit) for di in self.detectors])
#         return '(({},{}), ({}))'.format(s, e, f)
#
#     def __repr__(self):
#         return 'Block {}-{}'.format(self.start, self.end)
#
#
# class ParameterEditor(Loggable):
#     body = String
#     editor = Any
#
#     def parse(self, txt):
#         pass
#
#     def traits_view(self):
#         v = View()
#         return v
#
#
# STR_FMT = "{}= '{}'"
# FMT = '{}= {}'
# #===============================================================================
# # multicollect
# #===============================================================================
# MULTICOLLECT_COUNTS_REGEX = re.compile(r'(MULTICOLLECT_COUNTS) *= *\d+$')
# MULTICOLLECT_ISOTOPE_REGEX = re.compile(r'(MULTICOLLECT_ISOTOPE) *= *')
# MULTICOLLECT_DETECTOR_REGEX = re.compile(r'(MULTICOLLECT_DETECTOR) *= *')
# ACTIVE_DETECTORS_REGEX = re.compile(r'(ACTIVE_DETECTORS) *= *')
# FITS_REGEX = re.compile(r'(FITS) *= *')
#
# MULTICOLLECT_ISOTOPE_FMT = STR_FMT
# MULTICOLLECT_DETECTOR_FMT = STR_FMT
#
# #===============================================================================
# # baseline
# #===============================================================================
# BASELINE_COUNTS_REGEX = re.compile(r'(BASELINE_COUNTS) *= *\d+$')
# BASELINE_DETECTOR_REGEX = re.compile(r'(BASELINE_DETECTOR) *= *')
# BASELINE_MASS_REGEX = re.compile(r'(BASELINE_MASS) *= *')
# BASELINE_BEFORE_REGEX = re.compile(r'(BASELINE_BEFORE) *= *')
# BASELINE_AFTER_REGEX = re.compile(r'(BASELINE_AFTER) *= *')
# BASELINE_SETTLING_TIME_REGEX = re.compile(r'(BASELINE_SETTLING_TIME) *= *')
#
# BASELINE_DETECTOR_FMT = STR_FMT
#
# #===============================================================================
# # peak center
# #===============================================================================
# PEAK_CENTER_BEFORE_REGEX = re.compile(r'(PEAK_CENTER_BEFORE) *= *')
# PEAK_CENTER_AFTER_REGEX = re.compile(r'(PEAK_CENTER_AFTER) *= *')
# PEAK_CENTER_DETECTOR_REGEX = re.compile(r"(PEAK_CENTER_DETECTOR) *= *")
# PEAK_CENTER_ISOTOPE_REGEX = re.compile(r"(PEAK_CENTER_ISOTOPE) *= *")
#
# PEAK_CENTER_DETECTOR_FMT = STR_FMT
# PEAK_CENTER_ISOTOPE_FMT = STR_FMT
# #===============================================================================
# # equilibration
# #===============================================================================
# EQ_TIME_REGEX = re.compile(r"(EQ_TIME) *= *")
# EQ_INLET_REGEX = re.compile(r"(EQ_INLET) *= *")
# EQ_OUTLET_REGEX = re.compile(r"(EQ_OUTLET) *= *")
# EQ_DELAY_REGEX = re.compile(r"(EQ_DELAY) *= *")
#
# EQ_INLET_FMT = STR_FMT
# EQ_OUTLET_FMT = STR_FMT
#
# #===============================================================================
# # peak hops
# #===============================================================================
# USE_PEAK_HOP_REGEX = re.compile(r'(USE_PEAK_HOP) *= *')
# NCYCLES_REGEX = re.compile(r'(NCYCLES) *= *')
# BASELINE_NCYCLES_REGEX = re.compile(r'(BASELINE_NCYCLES) *= *')
# HOPS_REGEX = re.compile(r'(HOPS) *= *\[')
#
#
# #===============================================================================
# # conditions
# #===============================================================================
# ACTIONS_REGEX = re.compile(r'ACTIONS *= *')
# TRUNCATIONS_REGEX = re.compile(r'TRUNCATIONS *= *')
# TERMINATIONS_REGEX = re.compile(r'TERMINATIONS *= *')
#
#
# class memo_scroll(object):
#     def __init__(self, editor):
#         self.editor = editor
#
#     def __enter__(self, *args):
#         self._prev_scroll = self.editor.get_scroll()
#
#     def __exit__(self, *args):
#         self.editor.set_scroll(self._prev_scroll)
#
#
# class MeasurementParameterEditor(ParameterEditor):
#     #===========================================================================
#     # counts
#     #===========================================================================
#     multicollect_counts = Int(100)
#     active_detectors = List
#
#     #===========================================================================
#     # baselines
#     #===========================================================================
#     baseline_counts = Int(100)
#     baseline_detector = String
#     baseline_mass = Float
#     baseline_before = Bool
#     baseline_after = Bool
#     baseline_settling_time = Int(3)
#
#     #===========================================================================
#     # peak center
#     #===========================================================================
#     peak_center_before = Bool
#     peak_center_after = Bool
#     peak_center_isotope = String
#     peak_center_detector = String
#
#     #===========================================================================
#     # equilibration
#     #===========================================================================
#     eq_time = Float
#     eq_outlet = String
#     eq_inlet = String
#     eq_delay = Float
#
#     #===========================================================================
#     # peak hop
#     #===========================================================================
#     ncycles = Int
#     use_peak_hop = Bool
#     baseline_ncycles = Int
#     hops = List
#
#     #===========================================================================
#     # conditions
#     #===========================================================================
#     actions = List
#     truncations = List
#     terminations = List
#
#     fits = String
#     suppress_update = False
#
#     fit_blocks = List(FitBlock)
#     fit_block = Instance(FitBlock)
#
#     #===============================================================================
#     # parse
#     #===============================================================================
#     def parse(self, txt):
#         self.suppress_update = True
#         #        self.body = txt
#         str_to_str = lambda x: x.replace("'", '').replace('"', '')
#         lines = txt.split('\n')
#
#         def extract_detectors(v):
#             v = eval(v)
#             for di in self.active_detectors:
#                 di.use = di.label in v
#
#         attrs = (
#             ('multicollect_counts', int),
#             ('active_detectors', extract_detectors),
#
#             ('baseline_before', to_bool),
#             ('baseline_after', to_bool),
#             ('baseline_counts', int),
#             ('baseline_detector', str_to_str),
#             ('baseline_mass', float),
#
#             ('peak_center_before', to_bool),
#             ('peak_center_after', to_bool),
#             ('peak_center_detector', str_to_str),
#             ('peak_center_isotope', str_to_str),
#
#             ('eq_time', float),
#             ('eq_inlet', str_to_str),
#             ('eq_outlet', str_to_str),
#             ('eq_delay', float),
#
#             ('use_peak_hop', to_bool),
#             ('ncycles', int),
#         )
#         found = []
#         for li in lines:
#             for v, cast in attrs:
#                 if self._extract_parameter(li, v, cast=cast):
#                     found.append(v)
#                     continue
#
#         self._extract_fits(lines)
#
#         hoplist = self._extract_multiline_parameter(lines, 'hops')
#         if hoplist:
#             self.hops = self._extract_hops(hoplist)
#
#         actions = self._extract_multiline_parameter(lines, 'actions')
#         if actions:
#             self.actions = self._extract_actions(actions)
#
#         truncations = self._extract_multiline_parameter(lines, 'truncations')
#         if truncations:
#             self.truncations = self._extract_truncations(truncations)
#
#         terminations = self._extract_multiline_parameter(lines, 'terminations')
#         if terminations:
#             self.terminations = self._extract_truncations(terminations)
#
#         for name, _cast in attrs:
#             if name not in found:
#                 nv = self._get_new_value(name, getattr(self, name))
#                 lines.insert(3, nv)
#
#         self.suppress_update = False
#
#     def _make_fit_blocks(self, blocks):
#         def block_factory(b, f):
#             if b:
#                 s, e = b
#                 if s is not None:
#                     s = str(s)
#                 else:
#                     s = ''
#                 if e is not None:
#                     e = str(e)
#                 else:
#                     e = ''
#
#             else:
#                 s, e = '', ''
#
#             dets = [Detector(label=di.label,
#                              fit=f)
#                     for f, di in zip(f, self.active_detectors)]
#
#             fb = FitBlock(start=s, end=e,
#                           detectors=dets
#             )
#             return fb
#
#         return [
#             block_factory(bounds, fits)
#             for bounds, fits in blocks
#         ]
#
#
#     def _extract_fits(self, lines):
#         v = self._extract_multiline_parameter(lines, 'fits')
#         fb = None
#         if v:
#             if isinstance(v[0], tuple):
#                 if isinstance(v[0][0], tuple):
#                     fb = v
#             else:
#                 fb = [(None, v)]
#
#         if fb:
#             fb = self._make_fit_blocks(fb)
#             self.fit_blocks = fb
#             self.fit_block = fb[0]
#             #
#             # #         print fits
#             # #         v = eval(fits)
#             #         if len(v) == 1:
#             #             v = v * len(self.active_detectors)
#             #
#             #         for vi, di in zip(v, [di for di in self.active_detectors if di.use]):
#             #
#             #             if vi.endswith('SD'):
#             #                 vi = FIT_TYPES[3]
#             #             elif vi.endswith('SEM'):
#             #                 vi = FIT_TYPES[4]
#             #             di.fit = vi
#
#     def _extract_actions(self, items):
#         acs = []
#         for use, (key, comp, crit, start,
#                   freq, action, resume) in items:
#             ac = MeasurementAction(use=use,
#                                    key=key,
#                                    comparator=comp,
#                                    criterion=crit,
#                                    start_count=start,
#                                    frequency=freq,
#                                    action=action,
#                                    resume=resume
#             )
#             acs.append(ac)
#         return acs
#
#     def _extract_truncations(self, items):
#         return self._extract_conditions(MeasurementTruncation, items)
#
#     def _extract_terminations(self, items):
#         return self._extract_conditions(MeasurementTermination, items)
#
#     def _extract_conditions(self, klass, items, **kw):
#         acs = []
#         for use, (key, comp, crit, start, freq) in items:
#             ac = klass(use=use,
#                        key=key,
#                        comparator=comp,
#                        criterion=crit,
#                        start_count=start,
#                        frequency=freq,
#                        **kw
#             )
#             acs.append(ac)
#
#         return acs
#
#     def _extract_hops(self, hl):
#         hops = []
#         for _, (hi, cnts, settle) in enumerate(hl):
#             poss, dets = zip(*[it.split(':') for it in hi.split(',')])
#             pos = poss[0]
#             dets = ','.join(map(str.strip, dets))
#             hop = Hop(position=pos, detectors=dets,
#                       counts=cnts,
#                       settling_time=settle)
#             hops.append(hop)
#
#         return hops
#
#     def _endline(self, li, terminator=']'):
#         '''
#             use regex in future
#         '''
#         li = li.strip()
#         if li.startswith('#'):
#             return
#         elif '#' in li:
#             li = li.split('#')[0]
#
#         if li.endswith(terminator):
#             return True
#
#     def _extract_multiline_parameter(self, lines, param):
#         rlines = []
#         start = None
#         regex = self._get_regex(param)
#         endline = self._endline
#         for li in lines:
#
#             if regex.match(li):
#                 li = li.split('=')[1]
#                 rlines.append(li)
#                 try:
#                     v = eval(li)
#                     if isinstance(v, (tuple, list)):
#                         break
#                 except SyntaxError:
#                     pass
#                     #                 if endline(li):
#                 #                     break
#                 start = True
#
#             elif start and endline(li):
#                 rlines.append(li)
#                 break
#             elif start:
#                 rlines.append(li)
#
#         if rlines:
#             r = '\n'.join(rlines)
#             #             if param == 'fits':
#             #                 print rlines
#             try:
#                 return eval(r)
#             except Exception, e:
#             #                 print r
#                 self.debug(e)
#
#     def _extract_parameter(self, line, attr, cast=None):
#         regex = globals()['{}_REGEX'.format(attr.upper())]
#
#         if regex.match(line):
#             try:
#                 _, v = line.split('=')
#             except ValueError:
#                 return
#
#             v = v.strip()
#             if cast:
#                 v = cast(v)
#
#             if v is not None:
#                 setattr(self, attr, v)
#                 self._update_value(attr, v)
#             return True
#             #===============================================================================
#             # modification
#             #===============================================================================
#
#     def _modify_body(self, name, new):
#
#         if not self.editor or self.suppress_update:
#             return
#
#         with memo_scroll(self.editor):
#             regex = self._get_regex(name)
#             nv = self._get_new_value(name, new)
#             ostr = []
#             modified = False
#             print regex, name, new
#             body = self.editor.getText()
#             for i, li in enumerate(body.split('\n')):
#
#                 if li.startswith('def main('):
#                     main_idx = i
#
#                 if regex.match(li.strip()):
#                     ostr.append(nv)
#                     modified = True
#                 else:
#                     ostr.append(li)
#
#                     #        print name, new, modified
#
#             if not modified:
#                 ostr.insert(main_idx, nv)
#
#             body = '\n'.join(ostr)
#             self.editor.setText(body)
#             return modified
#
#     def _modify_body_multiline(self, param, new):
#         if not self.editor or self.suppress_update:
#             return
#
#         with memo_scroll(self.editor):
#
#             body = self.editor.getText()
#             lines = body.split('\n')
#             regex = self._get_regex(param)
#             endline = self._endline
#             rlines = []
#             start = None
#             # delete the previous entry
#
#             for i, li in enumerate(lines):
#                 if regex.match(li.strip()):
#                     idx = i
#                     start = True
#                     continue
#                 elif start:
#                     if endline(li):
#                         start = False
#                     continue
#
#                 rlines.append(li)
#
#             rlines.insert(idx, new)
#             body = '\n'.join(rlines)
#             self.editor.setText(body)
#
#     def _get_regex(self, name):
#         return globals()['{}_REGEX'.format(name.upper())]
#
#     def _get_new_value(self, name, new):
#         p = name.upper()
#         ff = '{}_FMT'.format(p)
#         if ff in globals():
#             fmt = globals()[ff]
#         else:
#             fmt = FMT
#
#         p = '{:<25s}'.format(p)
#         return fmt.format(p, new)
#
#     #===============================================================================
#     # handlers
#     #===============================================================================
#     @on_trait_change('actions:[], actions[]')
#     def _update_actions(self, name, new):
#         self._update_conditions(self.actions, 'actions')
#
#     @on_trait_change('terminations:[], terminations[]')
#     def _update_terminations(self, name, new):
#         self._update_conditions(self.terminations, 'terminations')
#
#     @on_trait_change('truncations:[], truncations[]')
#     def _update_truncations(self, name, new):
#         self._update_conditions(self.truncations, 'truncations')
#
#     def _update_conditions(self, items, name):
#         acs = [
#             ac.to_string()
#             for ac in items
#         ]
#
#         acs = ['{},'.format(hi) for hi in acs if hi]
#         nacs = [acs[0]]
#         for hi in acs[1:]:
#             nacs.append('        {}'.format(hi))
#
#         dname = '{} = ['.format(name.upper())
#         n = len(dname) - 1
#         action_str = '{}{}\n{}]'.format(dname,
#                                         '\n'.join(nacs),
#                                         n * ' ',
#         )
#
#         return self._modify_body_multiline(name.lower(), action_str)
#
#     @on_trait_change('''peak_center_+, eq_+, multicollect_counts, baseline_+,
# use_peak_hop, ncycles, baseline_ncycles
# ''')
#     def _update_value(self, name, new):
#         return self._modify_body(name, new)
#
#     @on_trait_change('hops:[counts,detectors, position]')
#     def _update_hops(self, obj, name, new):
#
#         hs = [hi.to_string()
#               for hi in self.hops]
#         hs = ['({}),'.format(hi) for hi in hs if hi]
#         nhs = [hs[0]]
#         for hi in hs[1:]:
#             nhs.append('        {}'.format(hi))
#         hopstr = 'HOPS = [{}\n]'.format('\n'.join(nhs))
#
#         ho = self.hops[0]
#         det = ho.detectors.split(',')[0]
#         iso = ho.position
#
#         self._modify_body('multicollect_detector', det)
#         self._modify_body('multicollect_isotope', iso)
#         self._modify_body_multiline('hops', hopstr)
#
#     @on_trait_change('fit_block:[start,end,detectors:fit]')
#     def _update_fit_block(self, obj, name, old, new):
#     #         print obj, name, old, new
#         blocks = ['{},'.format(bi.to_string()) for bi in self.fit_blocks]
#         #         print blocks
#         nbs = [blocks[0]]
#         for bi in blocks[1:]:
#             nbs.append('        {}'.format(bi))
#
#         new = 'FITS = [{}\n        ]'.format('\n'.join(nbs))
#
#         self._modify_body_multiline('fits', new)
#
#     #===============================================================================
#     # defaults
#     #===============================================================================
#     def _active_detectors_default(self):
#         detectors = []
#         path = os.path.join(paths.spectrometer_dir, 'detectors.cfg')
#         if os.path.isfile(path):
#             cfg = ConfigParser()
#             cfg.read(path)
#             for di in cfg.sections():
#                 det = Detector(label=di)
#                 detectors.append(det)
#
#         return detectors
#
#     def _new_action(self):
#         return MeasurementAction()
#
#     def _new_truncation(self):
#         return MeasurementTruncation()
#
#     def _new_termination(self):
#         return MeasurementTermination()
#
#     #===============================================================================
#     #
#     #===============================================================================
#
#     def traits_view(self):
#         multicollect_grp = VGroup(
#             Group(
#                 Item('multicollect_counts', label='Counts',
#                      tooltip='Number of data points to collect'
#                 )
#             ),
#             UItem('fit_block', editor=EnumEditor(name='fit_blocks')),
#             UItem('fit_block', style='custom',
#                   editor=InstanceEditor()),
#             #                                  UItem('active_detectors',
#             #                                        style='custom',
#             #                                        editor=TableEditor(
#             #                                         sortable=False,
#             #                                         reorderable=False,
#             #                                         columns=[
#             #                                         ObjectColumn(name='label',
#             #                                                      editable=False,
#             #                                                      label='Det.'),
#             #                                         CheckboxColumn(name='use', label='Use'),
#             #                                         ObjectColumn(name='isotope',
#             #                                                      editor=EnumEditor(name='isotopes')
#             #                                                      ),
#             #                                         ObjectColumn(name='fit',
#             #                                                      editor=EnumEditor(values=[NULL_STR] + FIT_TYPES)
#             #                                                      ),
#
#
#             #                                                                    ])
#             #                                        ),
#
#             label='Multicollect',
#             show_border=True
#         )
#         baseline_grp = Group(
#             Item('baseline_before', label='Baselines at Start'),
#             Item('baseline_after', label='Baselines at End'),
#             Item('baseline_counts',
#                  tooltip='Number of baseline data points to collect',
#                  label='Counts'),
#             Item('baseline_detector', label='Detector'),
#             Item('baseline_settling_time',
#                  label='Delay (s)',
#                  tooltip='Wait "Delay" seconds after setting magnet to baseline position'
#             ),
#             Item('baseline_mass', label='Mass'),
#             label='Baseline',
#             show_border=True
#         )
#
#         peak_center_grp = Group(
#             Item('peak_center_before', label='Peak Center at Start'),
#             Item('peak_center_after', label='Peak Center at End'),
#             Item('peak_center_detector',
#                  label='Detector',
#                  enabled_when='peak_center_before or peak_center_after'
#             ),
#             Item('peak_center_isotope',
#                  label='Isotope',
#                  enabled_when='peak_center_before or peak_center_after'
#             ),
#             label='Peak Center',
#             show_border=True)
#
#         equilibration_grp = Group(
#             Item('eq_time', label='Time (s)'),
#             Item('eq_outlet', label='Ion Pump Valve'),
#             Item('eq_delay', label='Delay (s)',
#                  tooltip='Wait "Delay" seconds before opening the Inlet Valve'
#             ),
#             Item('eq_inlet', label='Inlet Valve'),
#             label='Equilibration',
#             show_border=True
#         )
#
#         peak_hop_group = VGroup(
#             Group(
#                 Item('ncycles'),
#                 Item('baseline_ncycles')),
#             HGroup(Spring(springy=False, width=28),
#                    Label('position'), Spring(springy=False, width=10),
#                    Label('Detectors'), Spring(springy=False, width=188),
#                    Label('counts'),
#                    spring),
#             UItem('hops', editor=ListEditor(style='custom',
#                                             editor=InstanceEditor())),
#             label='Peak Hop',
#             visible_when='use_peak_hop',
#             show_border=True
#         )
#
#         action_editor = TableEditor(columns=[
#             CheckboxColumn(name='use', width=20),
#             ObjectColumn(name='key',
#                          label='Key'),
#             ObjectColumn(name='comparator',
#                          label='Comp.'),
#             ObjectColumn(name='criterion',
#                          label='Crit.'),
#             ObjectColumn(name='start_count',
#                          label='Start'),
#             #                                       ObjectColumn(name='frequency',
#             #                                                    label='Freq.'
#             #                                                    ),
#             CheckboxColumn(name='resume',
#                            label='Resume'),
#         ],
#                                     deletable=True,
#                                     row_factory=self._new_action
#         )
#
#         truncation_editor = TableEditor(columns=[
#             CheckboxColumn(name='use', width=20),
#             ObjectColumn(name='key',
#                          label='Key'),
#             ObjectColumn(name='comparator',
#                          label='Comp.'),
#             ObjectColumn(name='criterion',
#                          label='Crit.'),
#             ObjectColumn(name='start_count',
#                          label='Start'),
#         ],
#                                         deletable=True,
#                                         row_factory=self._new_truncation
#         )
#
#         termination_editor = TableEditor(columns=[
#             CheckboxColumn(name='use', width=20),
#             ObjectColumn(name='key',
#                          label='Key'),
#             ObjectColumn(name='comparator',
#                          label='Comp.'),
#             ObjectColumn(name='criterion',
#                          label='Crit.'),
#             ObjectColumn(name='start_count',
#                          label='Start'),
#         ],
#                                          deletable=True,
#                                          row_factory=self._new_termination
#         )
#
#         cond_grp = VGroup(
#             Group(
#                 UItem(
#                     'actions', editor=action_editor,
#                     style='custom'
#                 ), label='Actions'),
#             Group(
#                 UItem(
#                     'truncations', editor=truncation_editor,
#                     style='custom'
#                 ), label='Truncations'),
#             Group(
#                 UItem(
#                     'terminations', editor=termination_editor,
#                     style='custom'
#                 ), label='Terminations'),
#             label='Conditions'
#         )
#
#         v = View(VGroup(
#             Item('use_peak_hop'),
#             peak_hop_group,
#             Group(
#                 multicollect_grp,
#                 cond_grp,
#                 baseline_grp,
#                 peak_center_grp,
#                 equilibration_grp,
#                 layout='tabbed',
#                 visible_when='not use_peak_hop'
#             ),
#         )
#         )
#         return v
#
# #============= EOF =============================================
#
# '''
#     @on_trait_change('active_detectors:[use, fit, isotope]')
#     def _update_active_detectors(self, obj, name, new):
#         dets = self.active_detectors
#
#         if name == 'isotope':
#             if new != NULL_STR:
#                 for di in dets:
#                     if not di == obj:
#                         di.isotope = NULL_STR
#                 self._modify_body('multicollect_detector', obj.label)
#                 self._modify_body('multicollect_isotope', obj.isotope)
#             return
#
# #        s = ''
# #        if name == 'use':
# #            if not new and obj.isotope != NULL_STR:
# #                fd = next((a for a in self.active_detectors if a.use), None)
# #                fd.isotope = obj.isotope
# #
# #            attr = 'label'
# #            param = 'active_detectors'
# #        else:
# #            attr = 'fit'
# #            param = 'fits'
# #
# #        new = []
# #        for di in dets:
# #            if di.use:
# #                new.append((
# #                            getattr(di, 'label'),
# #                            getattr(di, 'fit')
# #                            ))
#
#         ad, fs = zip(*[(di.label, di.fit)
#                        for di in dets if di.use])
#         fs = list(fs)
#         for i, fi in enumerate(fs):
#             if fi.endswith('SEM'):
#                 fs[i] = 'average_SEM'
#             elif fi.endswith('SD'):
#                 fs[i] = 'average_SD'
#
#         for new, name in ((ad, 'active_detectors'),
#                           (fs, 'fits')):
#             if len(new) == 1:
#                 s = "'{}',".format(new[0])
#             else:
#                 s = ','.join(map("'{}'".format, new))
#
#                 self._modify_body(name, '({})'.format(s))
# '''
#

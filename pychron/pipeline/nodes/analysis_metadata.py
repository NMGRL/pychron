# # ===============================================================================
# # Copyright 2015 Jake Ross
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
# from itertools import groupby
#
# from traits.api import HasTraits, Str, Bool, Float
# from traitsui.api import View, UItem, Item, VGroup, HGroup
# # ============= standard library imports ========================
# # ============= local library imports  ==========================
#
# from pychron.pipeline.nodes.data import DVCNode
#
#
# class AnalysisMetadataOption(HasTraits):
#     sample = Str(analysis=True)
#     material = Str(analysis=True)
#     project = Str(analysis=True)
#     comment = Str(analysis=True)
#     weight = Float(extraction=True)
#     identifier = Float(identifier=True)
#     aliquot = Float(identifier=True)
#
#     sample_enabled = Bool(False)
#     material_enabled = Bool(False)
#     project_enabled = Bool(False)
#     comment_enabled = Bool(False)
#     weight_enabled = Bool(False)
#     identifier_enabled = Bool(False)
#     aliquot_enabled = Bool(False)
#
#     def traits_view(self):
#         v = View(VGroup(HGroup(Item('sample_enabled', label='Sample'),
#                                UItem('sample', enabled_when='sample_enabled')),
#                         HGroup(Item('material_enabled', label='Material'),
#                                UItem('material', enabled_when='material_enabled')),
#                         HGroup(Item('project_enabled', label='Project'),
#                                UItem('project', enabled_when='project_enabled')),
#                         HGroup(Item('comment_enabled', label='Comment'),
#                                UItem('comment', enabled_when='comment_enabled')),
#                         HGroup(Item('weight_enabled', label='Weight (mg)'),
#                                UItem('weight', enabled_when='weight_enabled'))),
#                  buttons=['OK', 'Cancel'])
#         return v
#
#     def get_edit_dict(self):
#         am = {k: getattr(self, k) for k in self.traits(analysis=True) if getattr(self, '{}_enabled'.format(k))}
#         ext = {k: getattr(self, k) for k in self.traits(extraction=True) if getattr(self, '{}_enabled'.format(k))}
#         idn = {k: getattr(self, k) for k in self.traits(identifier=True) if getattr(self, '{}_enabled'.format(k))}
#         return am, ext, idn
#
#
# class AnalysisMetadataNode(DVCNode):
#     options_klass = AnalysisMetadataOption
#     name = 'Analysis Metadata'
#
#     def configure(self, *args, **kw):
#         if self.unknowns:
#             unk = self.unknowns[0]
#             self.options.sample = unk.sample
#             self.options.material = unk.material
#             self.options.project = unk.project
#             self.options.comment = unk.comment
#             self.options.weight = unk.weight
#             self.options.identifier = unk.identifier
#             self.options.aliquot = unk.aliquot
#
#         return super(AnalysisMetadataNode, self).configure(*args, **kw)
#
#     def run(self, state):
#         dvc = self.dvc
#
#         am_dict, ext_dict, idn_dict = self.options.get_edit_dict()
#         if am_dict or ext_dict or idn_dict:
#             def key(xi):
#                 return xi.repository_identifier
#
#             for repo_id, ans in groupby(sorted(self.unknowns, key=key), key=key):
#
#                 dvc.pull_repository(repo_id)
#                 for ai in self.unknowns:
#                     dvc.analysis_metadata_edit(ai.uuid, ai.record_id, ai.repository_identifier, am_dict, ext_dict,
#                                                idn_dict)
#
#                 dvc.repository_commit(repo_id, 'Analysis Metadata edits')
#
# # ============= EOF =============================================

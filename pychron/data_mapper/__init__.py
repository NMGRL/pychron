# ===============================================================================
# Copyright 2016 Jake Ross
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

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
# from pychron.entry.dvc_import.model import DVCImporterModel
# from pychron.entry.dvc_import.view import DVCImporterView


from __future__ import absolute_import
def do_import_irradiation(dvc, sources, default_source=None):
    from pychron.data_mapper.view import DVCIrradiationImporterView, DVCAnalysisImporterView
    from pychron.data_mapper.model import DVCIrradiationImporterModel, DVCAnalysisImporterModel
    from pychron.envisage.view_util import open_view

    model = DVCIrradiationImporterModel(dvc=dvc, sources=sources)
    # model.source = next((k for k, v in sources.iteritems() if v == default_source), None)
    view = DVCIrradiationImporterView(model=model)
    info = open_view(view)
    return info.result


def do_import_analyses(dvc, sources):
    from pychron.data_mapper.view import DVCIrradiationImporterView, DVCAnalysisImporterView
    from pychron.data_mapper.model import DVCIrradiationImporterModel, DVCAnalysisImporterModel
    from pychron.envisage.view_util import open_view

    model = DVCAnalysisImporterModel(dvc=dvc, sources=sources)

    # model.source = next((k for k, v in sources.iteritems() if v == default_source), None)
    # model.source = sources.keys()[0]

    model.repository_identifier = 'test'
    model.extract_device = 'USGSVSC_Laser'
    model.mass_spectrometer = 'USGSVSC_Noblesse'
    model.principal_investigator = 'USGSVSC'

    view = DVCAnalysisImporterView(model=model)
    info = open_view(view)
    return info.result

# ============= EOF =============================================

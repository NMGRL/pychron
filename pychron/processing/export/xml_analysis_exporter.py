# ===============================================================================
# Copyright 2014 Jake Ross
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
import base64
import struct

from traits.api import Instance


#============= standard library imports ========================
import os
#============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
from pychron.processing.export.destinations import XMLDestination
from pychron.processing.export.export_spec import ExportSpec
from pychron.processing.export.exporter import Exporter


class XMLAnalysisExporter(Exporter):
    destination = Instance(XMLDestination, ())

    def __init__(self, *args, **kw):
        super(XMLAnalysisExporter, self).__init__(*args, **kw)
        from pychron.core.xml.xml_parser import XMLParser

        xmlp = XMLParser()
        self._parser = xmlp

    def set_destination(self, destination):
        self.destination = destination

    def add(self, spec):
        if not isinstance(spec, ExportSpec):
            s = ExportSpec()
            s.load_record(spec)
            spec = s

        self._make_xml_analysis(self._parser, spec)
        return True

    def export(self):
        if os.path.isdir(os.path.dirname(self.destination.destination)):
            self._parser.save(self.destination.destination)

    def _make_timeblob(self, t, v):
        blob = ''
        for ti, vi in zip(t, v):
            blob += struct.pack('>ff', float(vi), float(ti))
        return blob

    def _make_xml_analysis(self, xmlp, spec):
        xmlp.add('Encoding', 'RFC3548-Base64', None)
        xmlp.add('Endian', 'big', None)
        an = xmlp.add('analysis', '', None)
        meta = xmlp.add('metadata', '', an)
        xmlp.add('Labnumber', spec.labnumber, meta)
        xmlp.add('Aliquot', spec.aliquot, meta)
        xmlp.add('Step', spec.step, meta)

        irrad = xmlp.add('Irradiation','', meta)
        xmlp.add('name', spec.irradiation, irrad)
        xmlp.add('level', spec.level, irrad)
        xmlp.add('position', spec.irradiation_position, irrad)
        chron = xmlp.add('chronology','',irrad)
        for power, start, end in spec.chron_dosages:
            dose =xmlp.add('dose', '', chron)
            xmlp.add('power', power, dose)
            xmlp.add('start', start, dose)
            xmlp.add('end', end, dose)

        pr = xmlp.add('production_ratios', '', irrad)
        xmlp.add('production_name', spec.production_name, pr)
        for d in (spec.production_ratios, spec.interference_corrections):
            for pname, pv in d.iteritems():
                pp = xmlp.add(pname, '', pr)
                xmlp.add('value',nominal_value(pv), pp)
                xmlp.add('error',std_dev(pv), pp)

        for isotope in spec.isotopes.itervalues():
            isok = isotope.name
            det = isotope.detector
            sfit = isotope.fit

            isotag = xmlp.add(isok,'', an)

            xmlp.add('detector', det, isotag)
            xmlp.add('fit', sfit, isotag)
            xmlp.add('intercept_value', nominal_value(isotope.uvalue), isotag)
            xmlp.add('intercept_error', std_dev(isotope.uvalue), isotag)

            baseline=isotope.baseline
            xmlp.add('baseline_value', nominal_value(baseline.uvalue), isotag)
            xmlp.add('baseline_error', std_dev(baseline.uvalue), isotag)

            blank=isotope.blank
            xmlp.add('blank_value', nominal_value(blank.uvalue), isotag)
            xmlp.add('blank_error', std_dev(blank.uvalue), isotag)

            datatag = xmlp.add('raw','', isotag)

            xmlp.add('signal',
                     base64.b64encode(self._make_timeblob(isotope.offset_xs,
                                                          isotope.ys)), datatag)

            xmlp.add('baseline',
                     base64.b64encode(self._make_timeblob(baseline.xs,
                                                          baseline.ys)), datatag)


#============= EOF =============================================




from pychron.core.xml.xml_parser import pprint_xml

__author__ = 'ross'

import unittest

INIT_XML = '''<?xml version='1.0' encoding='ASCII'?>
<root>
<!--            <klass>RemoteNewportMotionController</klass> -->
  <globals>
    <use_ipc>True</use_ipc>
    <ignore_initialization_warnings>True</ignore_initialization_warnings>
    <ignore_initialization_questions>False</ignore_initialization_questions>
    <ignore_connection_warnings>true</ignore_connection_warnings>
    <experiment_debug>true</experiment_debug>
    <experiment_savedb>true</experiment_savedb>
    <video_test>false</video_test>
    <multi_user>False</multi_user>
    <use_login>False</use_login>
    <communication_simulation>True</communication_simulation>
  </globals>
  <plugins>
    <general>
      <plugin enabled="false">Experiment
        <mode>client</mode>
        <monitor enabled="false">automated_run_monitor
          <communications>
            <host>129.138.12.136</host>
            <port>1068</port>
            <kind>UDP</kind>
          </communications>
        </monitor>
        <runner>
          <communications>
            <host>129.138.12.136</host>
            <port>1068</port>
            <kind>UDP</kind>
          </communications>
        </runner>
      </plugin>
      <plugin enabled="false">Processing</plugin>
      <plugin enabled="false">MediaServer</plugin>
      <plugin enabled="false">PyScript</plugin>
      <plugin enabled="false">Video</plugin>
      <plugin enabled="false">Database</plugin>
      <plugin enabled="false">Entry</plugin>
      <plugin enabled="false">SystemMonitor</plugin>
      <plugin enabled="true">ArArConstants</plugin>

    <plugin enabled="false">Loading</plugin><plugin enabled="false">Workspace</plugin><plugin enabled="true">LabBook</plugin></general>
    <hardware>
      <plugin enabled="true">ArgusSpectrometer
        <device enabled="true">spectrometer_microcontroller
          <klass>ArgusController</klass>
        </device>
      </plugin>
      <plugin enabled="false">ExternalPipette
       <device enabled="true">apis_controller
       </device>
      </plugin>
      <plugin enabled="true">ExtractionLine
        <mode>client</mode>
        <server enabled="false">systemserver</server>
        <processor enabled="false">/tmp/hardware-extractionline</processor>
        <manager enabled="false">gauge_manager
          <device enabled="true">bone_micro_ion_controller
            <klass>MicroIonController</klass>
          </device>
          <device enabled="true">microbone_micro_ion_controller
            <klass>MicroIonController</klass>
          </device>
        </manager>
        <manager enabled="true">valve_manager
          <device enabled="true">valve_controller</device>
        </manager>
      </plugin>
      <plugin enabled="false">FusionsUV
        <device enabled="true">laser_controller
        </device>
      </plugin>

      <plugin enabled="false">FusionsCO2
        <mode>client</mode>
        <video_source>pvs://129.138.12.143:1084</video_source>
        <video_source>pvs://localhost:1084</video_source>
        <manager enabled="true">stage_manager
          <device enabled="true">stage_controller
            <required>false</required>
          </device>
        </manager>
        <device enabled="false">laser_controller
          <required>false</required>
        </device>
        <device enabled="false">fiber_light
          <required>false</required>
        </device>
      </plugin>
      <plugin enabled="false">FusionsDiode
        <processor enabled="true">/tmp/hardware-diode</processor>
        <manager enabled="true">stage_manager
          <device enabled="true">stage_controller</device>
        </manager>
        <manager enabled="true">control_module_manager
          <device enabled="true">control</device>
        </manager>
        <device enabled="true">laser_controller
          <required>false</required>
        </device>
        <device enabled="true">fiber_light
          <required>false</required>
        </device>
        <device enabled="true">temperature_controller
          <klass>WatlowEZZone</klass>
          <required>false</required>
        </device>
        <device enabled="false">pyrometer
          <required>false</required>
        </device>
        <device enabled="true">analog_power_meter
          <required>false</required>
        </device>
        <device enabled="false">chiller
          <klass>RemoteThermoRack</klass>
          <required>false</required>
        </device>
        <device enabled="false">temperature_monitor
          <required>false</required>
          <klass>DPi32TemperatureMonitor</klass>
        </device>
      </plugin>
    </hardware>
    <data>
    </data>
    <social>
      <plugin enabled="false">Email</plugin>
      <plugin enabled="false">Twitter</plugin>
    </social>
  </plugins>
</root>'''

EINIT_XML = '''<?xml version='1.0' encoding='ASCII'?>
<root> <!--
    <klass>RemoteNewportMotionController</klass>
-->
    <globals>
        <use_ipc>True</use_ipc>
        <ignore_initialization_warnings>True</ignore_initialization_warnings>
        <ignore_initialization_questions>False</ignore_initialization_questions>
        <ignore_connection_warnings>true</ignore_connection_warnings>
        <experiment_debug>true</experiment_debug>
        <experiment_savedb>true</experiment_savedb>
        <video_test>false</video_test>
        <multi_user>False</multi_user>
        <use_login>False</use_login>
        <communication_simulation>True</communication_simulation>
    </globals>
    <plugins>
        <general>
            <plugin enabled="false">Experiment
                <mode>client</mode>
                <monitor enabled="false">automated_run_monitor
                    <communications>
                        <host>129.138.12.136</host>
                        <port>1068</port>
                        <kind>UDP</kind>
                    </communications>
                </monitor>
                <runner>
                    <communications>
                        <host>129.138.12.136</host>
                        <port>1068</port>
                        <kind>UDP</kind>
                    </communications>
                </runner>
            </plugin>
            <plugin enabled="false">Processing</plugin>
            <plugin enabled="false">MediaServer</plugin>
            <plugin enabled="false">PyScript</plugin>
            <plugin enabled="false">Video</plugin>
            <plugin enabled="false">Database</plugin>
            <plugin enabled="false">Entry</plugin>
            <plugin enabled="false">SystemMonitor</plugin>
            <plugin enabled="true">ArArConstants</plugin>
            <plugin enabled="false">Loading</plugin>
            <plugin enabled="false">Workspace</plugin>
            <plugin enabled="true">LabBook</plugin>
        </general>
        <hardware>
            <plugin enabled="true">ArgusSpectrometer
                <device enabled="true">spectrometer_microcontroller
                    <klass>ArgusController</klass>
                </device>
            </plugin>
            <plugin enabled="false">ExternalPipette
                <device enabled="true">apis_controller </device>
            </plugin>
            <plugin enabled="true">ExtractionLine
                <mode>client</mode>
                <server enabled="false">systemserver</server>
                <processor enabled="false">/tmp/hardware-extractionline</processor>
                <manager enabled="false">gauge_manager
                    <device enabled="true">bone_micro_ion_controller
                        <klass>MicroIonController</klass>
                    </device>
                    <device enabled="true">microbone_micro_ion_controller
                        <klass>MicroIonController</klass>
                    </device>
                </manager>
                <manager enabled="true">valve_manager
                    <device enabled="true">valve_controller</device>
                </manager>
            </plugin>
            <plugin enabled="false">FusionsUV
                <device enabled="true">laser_controller </device>
            </plugin>
            <plugin enabled="false">FusionsCO2
                <mode>client</mode>
                <video_source>pvs://129.138.12.143:1084</video_source>
                <video_source>pvs://localhost:1084</video_source>
                <manager enabled="true">stage_manager
                    <device enabled="true">stage_controller
                        <required>false</required>
                    </device>
                </manager>
                <device enabled="false">laser_controller
                    <required>false</required>
                </device>
                <device enabled="false">fiber_light
                    <required>false</required>
                </device>
            </plugin>
            <plugin enabled="false">FusionsDiode
                <processor enabled="true">/tmp/hardware-diode</processor>
                <manager enabled="true">stage_manager
                    <device enabled="true">stage_controller</device>
                </manager>
                <manager enabled="true">control_module_manager
                    <device enabled="true">control</device>
                </manager>
                <device enabled="true">laser_controller
                    <required>false</required>
                </device>
                <device enabled="true">fiber_light
                    <required>false</required>
                </device>
                <device enabled="true">temperature_controller
                    <klass>WatlowEZZone</klass>
                    <required>false</required>
                </device>
                <device enabled="false">pyrometer
                    <required>false</required>
                </device>
                <device enabled="true">analog_power_meter
                    <required>false</required>
                </device>
                <device enabled="false">chiller
                    <klass>RemoteThermoRack</klass>
                    <required>false</required>
                </device>
                <device enabled="false">temperature_monitor
                    <required>false</required>
                    <klass>DPi32TemperatureMonitor</klass>
                </device>
            </plugin>
        </hardware>
        <data> </data>
        <social>
            <plugin enabled="false">Email</plugin>
            <plugin enabled="false">Twitter</plugin>
        </social>
    </plugins>
</root>'''


class XMLParserTestCase(unittest.TestCase):
    # def test_beautify(self):
    #
    #         tt='''<root>
    #     <a>
    #         <b>
    #         </b>
    #     </a>
    # </root>
    # '''
    #         intxt = '''<root><a><b></b></a></root>'''
    #         t= pprint_xml(intxt)
    #
    #         self.assertEqual(t, tt)
    #
    def test_pprint1(self):
        intxt = '''<root><a>1234<b>xy</b></a></root>'''
        otxt = pprint_xml(intxt)
        etxt='''<root>
    <a>1234
        <b>xy</b>
    </a>
</root>'''
        self.assertEqual(otxt, etxt)

    def test_pprint(self):
        intxt = '''<root><a><b></b></a></root>'''
        otxt = pprint_xml(intxt)
        etxt='''<root>
    <a>
        <b></b>
    </a>
</root>'''
        self.assertEqual(otxt, etxt)

    def test_pprint2(self):
        intxt = '''<root><a><b></b><c></c></a></root>'''
        otxt = pprint_xml(intxt)
        etxt='''<root>
    <a>
        <b></b>
        <c></c>
    </a>
</root>'''
        self.assertEqual(otxt, etxt)

    def test_pprint4(self):
        intxt = '''<root><a>12<b>123</b><c>1234</c></a></root>'''
        otxt = pprint_xml(intxt)
        etxt='''<root>
    <a>12
        <b>123</b>
        <c>1234</c>
    </a>
</root>'''
        self.assertEqual(otxt, etxt)

    def test_pprint5(self):
        intxt = '''<root><a enabled="false">12<b>123</b><c>1234</c></a></root>'''
        otxt = pprint_xml(intxt)
        etxt='''<root>
    <a enabled="false">12
        <b>123</b>
        <c>1234</c>
    </a>
</root>'''

        self.assertEqual(otxt, etxt)

    def test_pprint_initialization(self):
        otxt = pprint_xml(INIT_XML)
        self.assertEqual(EINIT_XML, otxt)


if __name__ == '__main__':
    unittest.main()

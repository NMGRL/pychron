Plugins
-------

Plugins are enabled/disabled in the ``setupfiles/initialization.xml`` file.

List of Plugins
~~~~~~~~~~~~~~~
* **General**

  * **Experiment** - Execute sets of automated runs.
  * **MassSpec** - Mass Spec plugin.
  * **PyScript** - Edit PyScripts; pychron's internal scripting language.
  * **ArArConstants** - List of Ar/Ar geochronology constants.
  * **Database** - SQL database interface.
  * **Loading** - Laser tray loading plugin.
  * **Pipeline** - Pychron's pipeline based processing workflow
  * **Entry** - Enter/Edit irradiation data.
  * **Workspace** - Git-enabled workspace repository.
  * **DVC** - Pychron's custom Data Version Control system.
  * **GitLab** - Private git repository hosting.
  * **GitHub** - Public git repository hosting at GitHub.com.
  * **MediaServer** - Image server/client.
  * **LabBook** - Git-enabled labbook repository.
  * **Video** - Video server/client.
  * **DashboardServer** - Publish various laboratory values.
  * **DashboardClient** - Listen to the Dashboard server.
  * **LabspyClient** - Labspy client. push updates to the labspy database.
  * **Update** - Update plugin.
  * **Image** - Use to take snapshots with a connected camera and save to file or database.
  * **IGSN** - International Geo Sample Number.
  * **Geochron** - Upload analyses to Geochron.org

* **Hardware**

  * **ExtractionLine** - Control extraction line components.
  * **ClientExtractionLine** - Remotely control extraction line components.
  * **ArgusSpectrometer** - Thermo ArgusVI plugin.
  * **HelixSpectrometer** - Thermo Helix plugin.
  * **NGXSpectrometer** - Isotopx NGX plugin.
  * **NMGRLFurnace** - NMGRL's resistance furnace plugin.
  * **ChromiumCO2** - Photon Machines Fusions CO2 control via "Chromium"
  * **FusionsCO2** - Photon Machines Fusions CO2.
  * **FusionsDiode** - Photon Machines Fusions Diode.
  * **FusionsUV** - NMGRL's custom Fusions UV.
  * **ExternalPipette** - Interface with the APIS pipette system.
  * **CanvasDesigner** - Visual editor for the Extraction Line Schematic.


* **Social**
  * **Email** - Allows pychron to send emails

Example Data Processing Initialization File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: xml

    <root>
      <globals>
      </globals>
      <plugins>
        <general>
          <plugin enabled="true">Database</plugin>
          <plugin enabled="true">Processing</plugin>
          <plugin enabled="true">ArArConstants</plugin>
          <plugin enabled="true">Entry</plugin>
          <plugin enabled="true">SystemMonitor</plugin>
        </general>
      </plugins>
    </root>


Example Experiment Initialization File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: xml

    <root>
      <globals>
      </globals>
      <plugins>
        <general>
          <plugin enabled="true">Database</plugin>
          <plugin enabled="true">Experiment</plugin>
          <plugin enabled="true">Processing</plugin>
          <plugin enabled="true">PyScript</plugin>
          <plugin enabled="true">ArArConstants</plugin>
          <plugin enabled="true">Entry</plugin>
          <plugin enabled="true">DashboardServer</plugin>
        </general>
        <hardware>
            <plugin enabled="false">Spectrometer
                <device enabled="true">spectrometer_microcontroller
                  <klass>ArgusController</klass>
                </device>
            </plugin>
            <plugin enabled="true">ExtractionLine
                <processor enabled="false">/tmp/hardware-extractionline</processor>
                <manager enabled="false">gauge_manager
                <device enabled="true">bone_micro_ion_controller
                    <klass>MicroIonController</klass>
                </device>
                <device enabled="false">microbone_micro_ion_controller
                    <klass>MicroIonController</klass>
                    <required>false</required>
                </device>
                </manager>
                <manager enabled="true">valve_manager
                    <device enabled="true">valve_controller</device>
                </manager>
                <device enabled="true">air_transducer
                    <klass>Transducer</klass>
                </device>
            </plugin>
        </hardware>
        <data>
        </data>
      </plugins>
    </root>

Example Laser Initialization File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: xml

    <root>
      <globals>
      </globals>
      <plugins>
        <general>
          <plugin enabled="true">Database</plugin>
          <plugin enabled="false">Experiment</plugin>
          <plugin enabled="true">Processing</plugin>
          <plugin enabled="false">PyScript</plugin>
          <plugin enabled="false">ArArConstants</plugin>
          <plugin enabled="false">Entry</plugin>
          <plugin enabled="false">SystemMonitor</plugin>
          <plugin enabled="true">DashboardServer</plugin>
        </general>
        <hardware>
            <plugin enabled="false">Spectrometer
                <device enabled="true">spectrometer_microcontroller
                  <klass>ArgusController</klass>
                </device>
            </plugin>
            <plugin enabled="true">ExtractionLine
                <processor enabled="false">/tmp/hardware-extractionline</processor>
                <manager enabled="false">gauge_manager
                <device enabled="true">bone_micro_ion_controller
                    <klass>MicroIonController</klass>
                </device>
                <device enabled="false">microbone_micro_ion_controller
                    <klass>MicroIonController</klass>
                    <required>false</required>
                </device>
                </manager>
                <manager enabled="true">valve_manager
                    <device enabled="true">valve_controller</device>
                </manager>
                <device enabled="true">air_transducer
                    <klass>Transducer</klass>
                </device>
            </plugin>
        </hardware>
        <data>
        </data>
        <social>
          <plugin enabled="true">Email</plugin>
          <plugin enabled="false">Twitter</plugin>
        </social>
      </plugins>
    </root>

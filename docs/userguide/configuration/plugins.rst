Plugins
---------------

Plugins are enabled/disabled in the ``setupfiles/initialization.xml`` file.

List of Plugins
~~~~~~~~~~~~~~~~~~
* **General**

  * **Database** - Access to MySQL, SQLite, PostgreSQL, etc. All database dialects supported by SQLAlchemy.
  * **Entry** - Enter information into a database. Projects, samples, labnumbers, etc.
  * **Processing** - Process Data. Make figures and tables.
  * **ArArConstants** - Constants used in Ar-Ar geochronology.
  * **SystemMonitor** - "Strip-chart" recording of laboratory conditions and processes.

* **Hardware**

  * **Experiment** - Create and execute Pychron Experiments.
  * **PyScript** - View/Edit pyscripts used for automated data collection.
  * **ExtractionLine** - View/Control a UHV extraction line.
  * **DashboardServer** - View/Publish a configurable set of parameters. Parameters are published to network and read by any connected client.
  * **Spectrometer** - View/Control a spectrometer. Currently only Thermo spectrometers with RemoteControlServer.cs are supported.

Example Data Processing Initialization File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

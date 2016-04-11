Configuring the Dashboard
============================

Setup File
----------------------------
The dashboard.xml or dashboard.yaml file defines which devices and values the dashboard should measure, display and
- if available - push to Labspy.

.. note:: Labspy is Django-based web app for displaying the laboratory status

Basic Structure
+++++++++++++++++++++

.. code-block:: xml

    <root>
        <device>DeviceName</device> <!-- name used by the dashboard for display -->
            <use>true</use> <!-- use this device -->
            <name>device_name</device> <!-- internal name. same as in initialization.xml -->
            <value>ValueName <!-- display name and name saved to labspy database -->
                <func>func_name</func> <!-- method name used by the device to get the value -->
                <period>300</period> <!-- query period in seconds or on_change -->
            </value>
            <value>ValueName <!-- display name and name saved to labspy database -->
                <func>func_name</func> <!-- method name used by the device to get the value -->
                <period>on_change</period> <!-- only trigger an update when value changes-->
                <change_threshold>0.25</change_threshold> <!-- current-value must be greater than change_threshold -->
           </value>
    </root>


dashboard.xml

.. code-block:: xml

    <root>
        <device>JanMonitor
            <use>true</use>
            <name>jan_qtegra_device</name>
            <value>JanTrapCurrent
                <func>read_trap_current</func>
                <period>on_change</period>
                <enabled>true</enabled>
                <change_threshold>0.25</change_threshold>
            </value>
            <value>JanEmission
                <func>read_emission</func>
                <period>on_change</period>
                <enabled>true</enabled>
                <change_threshold>0.25</change_threshold>
            </value>
            <value>JanDecabinTemp
                <func>read_decabin_temperature</func>
                <period>on_change</period>
                <enabled>true</enabled>
                <change_threshold>0.25</change_threshold>
            </value>
        </device>
        <device>Chiller
            <use>true</use>
            <name>chiller</name>
            <value>Coolant Temp.
                <units>F</units>
                <bind>coolant</bind>
                <func>get_coolant_out_temperature</func>
                <period>300</period>
                <enabled>true</enabled>
            </value>
        </device>
        <device>AirPressure
            <name>pneumatics</name>
            <value>Pressure
                <units>PSI</units>
                <bind>pressure</bind>
                <func>get_pressure</func>
                <period>120</period>
                <enabled>true</enabled>
                <record>false</record>
            </value>
            <use>true</use>
        </device>
        <device>AirPressure2
            <name>pneumatics2</name>
            <value>Pressure2
                <units>PSI</units>
                <bind>pressure</bind>
                <func>get_pressure</func>
                <period>120</period>
                <enabled>true</enabled>
                <record>false</record>
            </value>
            <use>true</use>
        </device>
        <device>Coldfinger
        <name>coldfinger</name>
        <use>true</use>
           <value>ColdFinger Temp.
                <bind>temperature</bind>
                <units>F</units>
                <func>read_temperature</func>
                <period>on_change</period>
                <enabled>true</enabled>
                <change_threshold>0.25</change_threshold>
            </value>
        </device>
        <device>EnvironmentalMonitor
            <name>microserver</name>
            <value>Lab Temp.
                <bind>temperature</bind>
                <units>F</units>
                <func>read_temperature</func>
                <period>60</period>
                <enabled>true</enabled>
                <change_threshold>0.25</change_threshold>
                <record>false</record>
            </value>
            <value>Lab Hum.
            <bind>humidity</bind>
                <units>%</units>
                <func>read_humidity</func>
                <period>60</period>
                <enabled>true</enabled>
                <change_threshold>0.25</change_threshold>
            </value>
            <use>true</use>
        </device>
    </root>

dashboard.yaml

.. code-block:: yaml

    - name: Chiller
      enabled: True
      device: chiller
      values:
          - name: Coolant
            period: 2
            enabled: True
    - name: AirPressure
      enabled: True
      device: pneumatics
      values:
          - name: pressure
            period: on_change
            enabled: True

    - name: BoneGauges
      enabled: True
      device: bone_micro_ion_controller
      values:
          - name: IG_pressure
            func: get_ion_pressure
            period: on_change
            enabled: True
          - name: CG1_pressure
            func: get_convectron_a_pressure
            period: on_change
            enabled: True
    - name: EnvironmentalMonitor
      enabled: True
      device: enivronmental_monitor
      values:
           - name: temperature
             func: get_temperature
             period: 10
             enabled: True
           - name: humidity
             func: get_humidity
             period: 10
             enabled: True
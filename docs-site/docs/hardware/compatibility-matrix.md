---
id: compatibility-matrix
title: Hardware Compatibility Matrix
sidebar_label: Compatibility Matrix
sidebar_position: 2
---

# Hardware Compatibility Matrix

This matrix covers every hardware category supported by Pychron as of the current `main` branch. Entries marked ⚠️ Partial have known limitations documented in the Notes column. Entries marked 🚧 Stub have class files present but no functional implementation. See the [Hardware Overview](./overview) for protocol and configuration details.

---

## Mass Spectrometers

| Device / Model | Class | Module | Protocol | Config | Status |
|---|---|---|---|---|---|
| Thermo Argus VI | `ArgusSpectrometer` | `pychron.spectrometer.thermo.spectrometer.argus` | Ethernet TCP → Qtegra | `host`, `port` | ✅ Complete |
| Thermo Helix MC+ | `HelixSpectrometer` | `pychron.spectrometer.thermo.spectrometer.helix` | Ethernet TCP → Qtegra | `host`, `port` | ✅ Complete |
| Thermo Helix Plus | `HelixPlusSpectrometer` | `pychron.spectrometer.thermo.spectrometer.helix` | Ethernet TCP → Qtegra | `host`, `port` | ✅ Complete |
| Thermo Helix SFT | `HelixSFTSpectrometer` | `pychron.spectrometer.thermo.spectrometer.helix` | Ethernet TCP → Qtegra | `host`, `port` | ✅ Complete |
| Isotopx NGX | `NGXSpectrometer` | `pychron.spectrometer.isotopx.spectrometer.ngx` | Ethernet TCP | `host`, `port` | ✅ Complete |
| Pfeiffer Quadera | `QuaderaSpectrometer` | `pychron.spectrometer.pfeiffer.spectrometer.quadera` | Ethernet | `host`, `port` | ⚠️ Partial — two method stubs (`pass`) at lines 70, 252 |
| MAP 215/216 | `MapSpectrometer` | `pychron.spectrometer.map.spectrometer` | Serial | `port` | 🚧 Stub — only `channel_select` and `magnet` defined; no plugin registered |

**Note on Thermo instruments:** Argus and Helix communicate through Qtegra's `RemoteControlServer.cs`. The hardware controller classes (`ArgusController`, `HelixController` in `pychron.hardware.thermo_spectrometer_controller`) connect to Qtegra over Ethernet and issue a `Reset` command on connect; all spectrometer commands are proxied through Qtegra.

---

## Lasers

| Device / Model | Class | Module | Protocol | Config | Status |
|---|---|---|---|---|---|
| Photon Machines (CO₂ fusion) | `FusionsCO2Manager` | `pychron.lasers.laser_managers.fusions_co2_manager` | Serial / Ethernet | `port` or `host`/`port` | ✅ Complete |
| Photon Machines (diode) | `FusionsDiodeManager` | `pychron.lasers.laser_managers.fusions_diode_manager` | Serial / Ethernet | `port` or `host`/`port` | ✅ Complete |
| Synrad CO₂ | `SynradCO2Manager` | `pychron.lasers.laser_managers.synrad_co2_manager` | Serial | `port` | ✅ Complete |
| TAP CO₂ | `TAPLaserManager` | `pychron.lasers.laser_managers.tap_laser_manager` | — | — | 🚧 Stub — class body is `pass` |
| TAP Diode | `TAPDiodeManager` | `pychron.lasers.laser_managers.tap_laser_manager` | — | — | ⚠️ Partial — only `stage_manager_id` and `configuration_dir_name` set |

---

## Furnaces

| Device / Model | Class | Module | Protocol | Config | Status |
|---|---|---|---|---|---|
| NMGRL Furnace (LabJack U3) | `NMGRLFurnaceManager` | `pychron.furnace.nmgrl.furnace_manager` | USB (LabJack) | LabJack config | ✅ Complete |
| LDEO Furnace (LabJack) | `LDEOFurnaceManager` | `pychron.furnace.ldeo.furnace_manager` | USB (LabJack) | LabJack config | ⚠️ Partial — setpoint writing commented out (line 187); temperature control not implemented (warning at `ldeo_furnace.py:159`) |

---

## Temperature Controllers

| Device / Model | Class | Module | Protocol | Config | Status |
|---|---|---|---|---|---|
| Watlow EZZone PM | `WatlowEZZone` | `pychron.hardware.watlow.watlow_ezzone` | Modbus RTU (RS-485) | `port`, `address` | ✅ Complete |
| Eurotherm Series 2000 | `Eurotherm` | `pychron.hardware.eurotherm.eurotherm` | Modbus RTU (RS-485) | `port`, `address` | ✅ Complete |
| Lakeshore Model 330 | `Model330TemperatureController` | `pychron.hardware.lakeshore.model330` | Serial / GPIB | `port` | ✅ Complete |
| Lakeshore Model 335 | `Model335TemperatureController` | `pychron.hardware.lakeshore.model335` | Serial | `port` | ✅ Complete |
| Lakeshore Model 336 | `Model336TemperatureController` | `pychron.hardware.lakeshore.model336` | Serial | `port` | ✅ Complete |
| Omega DPi32 | `DPi32TemperatureMonitor` | `pychron.hardware.temperature_monitor` | Serial RS-232 | `port`, `baud` | ✅ Complete |

---

## Vacuum Gauges

| Device / Model | Class | Module | Protocol | Config | Status |
|---|---|---|---|---|---|
| MKS Multi-Gauge Controller | `MKSController` | `pychron.hardware.gauges.mks.controller` | Serial | `port` | ✅ Complete |
| MKS SRG | `MKSSRG` | `pychron.hardware.gauges.mks.srg` | Serial | `port` | ✅ Complete |
| Granville-Phillips MicroIon | `MicroIonController` | `pychron.hardware.gauges.granville_phillips.micro_ion_controller` | Serial | `port` | ✅ Complete |
| Pfeiffer MaxiGauge | `PfeifferMaxiGaugeController` | `pychron.hardware.gauges.pfeiffer.maxi_gauge_controller` | Serial | `port` | ✅ Complete |
| Varian XGS-600 | `XGS600GaugeController` | `pychron.hardware.gauges.varian.varian_gauge_controller` | Serial | `port` | ✅ Complete |
| ADC Gauge | `ADCGaugeController` | `pychron.hardware.gauges.adc_gauge_controller` | ADC (MCC USB) | ADC config | ✅ Complete |
| U3 Gauge (LabJack U3) | `U3GaugeController` | `pychron.hardware.labjack.u3_gauge_controller` | USB (LabJack) | LabJack config | ✅ Complete |
| Pychron Remote Gauge | `PychronMicroIonController` | `pychron.hardware.gauges.granville_phillips.pychron_micro_ion_controller` | ZMQ/RPC | `host`, `port` | ✅ Complete |
| Qtegra Gauge | `QtegraGaugeController` | `pychron.hardware.gauges.qtegra.qtegra_gauge_controller` | Ethernet → Qtegra | `host`, `port` | ✅ Complete |

---

## Actuators / Valve Controllers

| Device / Model | Class | Module | Protocol | Config | Status |
|---|---|---|---|---|---|
| Agilent 34903A GP Switch | `AgilentGPActuator` | `pychron.hardware.agilent.agilent_gp_actuator` | GPIB / Ethernet | `host` or GPIB address | ✅ Complete |
| Arduino GP Actuator | `ArduinoGPActuator` | `pychron.hardware.arduino.arduino_gp_actuator` | Serial | `port` | ⚠️ Partial — first command consistently times out (TODO at line 45) |
| NGX GP Actuator | `NGXGPActuator` | `pychron.hardware.actuators.ngx_gp_actuator` | Ethernet (NGX controller) | `host`, `port` | ✅ Complete |
| NMGRL Furnace Actuator | `NMGRLFurnaceActuator` | `pychron.hardware.actuators.nmgrl_furnace_actuator` | RPC | `host`, `port` | ✅ Complete |
| ProXR Relay Actuator | `ProXRActuator` | `pychron.hardware.actuators.proxr_actuator` | Serial | `port` | ✅ Complete |
| Pychron Remote Actuator | `PychronGPActuator` | `pychron.hardware.actuators.pychron_gp_actuator` | ZMQ/RPC | `host`, `port` | ✅ Complete |
| Qtegra GP Actuator | `QtegraGPActuator` | `pychron.hardware.actuators.qtegra_gp_actuator` | Ethernet → Qtegra | `host`, `port` | ✅ Complete |
| Switch Controller | `SwitchController` | `pychron.hardware.actuators.switch_controller` | Serial | `port` | ✅ Complete |
| T4 (LabJack T4) | `T4Actuator` | `pychron.hardware.actuators.t4_actuator` | USB / Ethernet | LabJack config | ✅ Complete |
| U3 (LabJack U3) | `U3Actuator` | `pychron.hardware.actuators.u3_actuator` | USB (LabJack) | LabJack config | ✅ Complete |
| WiscAr Actuator | `WiscArGPActuator` | `pychron.hardware.actuators.wiscar_actuator` | RPC | `host`, `port` | ✅ Complete |
| Dummy Actuator | `DummyGPActuator` | `pychron.hardware.actuators.dummy_gp_actuator` | — | — | ✅ For simulation/testing |

---

## Motion Controllers / Stages

| Device / Model | Class | Module | Protocol | Config | Status |
|---|---|---|---|---|---|
| Kerr Motion Controller | `KerrMotor` | `pychron.hardware.kerr.kerr_motor` | Serial | `port` | ⚠️ Partial — home move uses velocity-profile-mode workaround (line 716) |
| Newport Motion Controller | `NewportMotionController` | `pychron.hardware.newport.newport_motion_controller` | Serial | `port` | ⚠️ Partial — `use_hack_axis=True` with displacement workaround (lines 306–319) |

---

## Ion Pumps

| Device / Model | Class | Module | Protocol | Config | Status |
|---|---|---|---|---|---|
| SPC Ion Pump Controller | `SPCIonPumpController` | `pychron.hardware.ionpump.spc_ion_pump_controller` | Serial | `port` | ✅ Complete |

---

## Turbo Pumps

| Device / Model | Class | Module | Protocol | Config | Status |
|---|---|---|---|---|---|
| Pfeiffer HiPace | `HiPace` | `pychron.hardware.turbo.hipace` | Serial | `port` | ✅ Complete |

---

## Chillers / Cooling

| Device / Model | Class | Module | Protocol | Config | Status |
|---|---|---|---|---|---|
| SS Cooling ThermoRack | `ThermoRack` | `pychron.hardware.thermorack` | Serial | `port` | ✅ Complete |
| Pychron Chiller | `PychronChiller` | `pychron.hardware.pychron_chiller` | RPC | `host`, `port` | ✅ Complete |

---

## Miscellaneous / Monitoring

| Device / Model | Class | Module | Protocol | Config | Status |
|---|---|---|---|---|---|
| Environmental Probe (Temp/Hum) | `TempHumMicroServer` | `pychron.hardware.environmental_probe` | Serial | `port` | ✅ Complete |
| Analog Power Meter | `AnalogPowerMeter` | `pychron.hardware.analog_power_meter` | ADC | ADC config | ✅ Complete |
| Air Transducer | `AirTransducer` | `pychron.hardware.transducer` | ADC | ADC config | ✅ Complete |
| RPi GPIO | `RPiGPIO` | `pychron.hardware.rpi_gpio` | GPIO (Raspberry Pi) | GPIO pin config | ✅ Complete |
| FerrupsUPS | `FerrupsUPS` | `pychron.hardware.FerrupsUPS` | Serial | `port` | ✅ Complete |
| Generic Device | `GenericDevice` | `pychron.hardware.generic_device` | Configurable | — | ✅ Base class for custom devices |

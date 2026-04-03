---
id: compatibility-matrix
title: Hardware Compatibility Matrix
sidebar_label: Compatibility Matrix
sidebar_position: 2
---

# Hardware Compatibility Matrix

This matrix covers every hardware category supported by Pychron as of the current `main` branch. It is derived from a direct audit of `pychron/hardware/`, `pychron/spectrometer/`, `pychron/lasers/`, `pychron/furnace/`, and related modules. Where limitations exist they are noted inline; see [Known Issues](#known-issues) at the bottom for items requiring attention before deployment.

## Status Legend

| Symbol | Meaning |
|---|---|
| ✓ | **Production** — fully implemented, in active use at one or more labs |
| ⚠ | **Partial** — functional for most operations but has documented gaps or workarounds |
| ✗ | **Stub** — class exists in the codebase but the body is `pass` or near-empty; not usable |
| ★ | **Lab-specific** — implemented for one institution; may require adaptation elsewhere |

---

## Mass Spectrometers

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| Thermo Scientific | Argus VI | Ethernet TCP → Qtegra | ✓ | All commands proxied through Qtegra `RemoteControlServer`. Issues a `Reset` on connect. Class: `ArgusSpectrometer` |
| Thermo Scientific | Helix MC+ | Ethernet TCP → Qtegra | ✓ | Same Qtegra proxy pattern as Argus. Class: `HelixSpectrometer` |
| Thermo Scientific | Helix SFT | Ethernet TCP → Qtegra | ✓ | Dedicated `HelixSFTSpectrometerManager`. Class: `HelixSFTSpectrometer` |
| Isotopx | NGX | Ethernet TCP (custom ASCII) | ✓ | Requires username/password authentication on connect. Command lock and retry logic present for valve-state queries; intermittent drop-outs are handled by retry but should be monitored. Class: `NGXSpectrometer` |
| Pfeiffer Vacuum | Quadera | Serial/Ethernet | ⚠ | Spectrometer logic (magnet, detector, source) implemented, but hardware controller class `QuaderaController` is a stub (`pass`). Communication layer not functional. Class: `QuaderaSpectrometer` |
| GV Instruments | MAP 215/216 | Serial | ✗ | Only `channel_select` and `magnet` defined. No plugin registration. Appears to be legacy/incomplete. Class: `MapSpectrometer` |

---

## Laser Systems

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| Photon Machines | Fusions CO₂ | Serial or Ethernet | ✓ | Full power calibration via polynomial coefficients; ADC1 power reading. Class: `FusionsCO2LogicBoard` |
| Photon Machines | Fusions Diode | Serial or Ethernet | ✓ | Integrates Watlow temperature control and Kerr motor stage. Class: `FusionsDiodeLogicBoard` |
| Photon Machines | Fusions UV | Serial | ✓ | Adds Kerr-driven nitrogen flow control (`NitrogenFlower`). Class: `FusionsUVLogicBoard` |
| Synrad | CO₂ | Serial (via Agilent) | ✓ | Power set via `AgilentDAC`; enable/disable via `AgilentGPActuator` on address 120. Class: `SynradCO2Manager` |
| UC2000 | Nd:YAG (frequency-doubled) | Serial | ✓ | SCPI-like protocol. Class: `UC2000` |
| OsTech | Diode | Serial | ★ | NMGRL-specific. Class: `OsTechLaserController` |
| ATL | Laser Control Unit | Serial | ★ | Fusions UV accessory. Class: `ATLLaserControlUnit` |
| TAP | CO₂ | — | ✗ | Class body is `pass`. No communication, power, or stage control implemented. Class: `TAPLaserManager` |
| TAP | Diode | Zaber (Ethernet) | ⚠ | Stage control via Zaber motion controller. Laser power control not implemented. Class: `TAPDiodeManager` |

---

## Furnace Systems

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| NMGRL (in-house) | Resistance furnace | USB (LabJack U3) + Serial (Eurotherm) | ✓ | Temperature via Eurotherm 818/3504 PID; sample feeder and funnel via stepper motors; camera and recorder integrated. Class: `NMGRLFurnaceManager` |
| LDEO (in-house) | LabJack U3 furnace | USB (LabJack U3, I2C DAC) | ⚠ | Setpoint write executes I2C calls but temperature control loop is not closed — `"Temperature control not implemented"` warning fires at runtime (`ldeo_furnace.py:159`). Calibration loaded from I2C EEPROM (address 0x50). Class: `LDEOFurnaceManager` |
| Thermo Scientific | Furnace | Qtegra RPC + Serial | ⚠ | Temperature control via Qtegra proxy; sample feeder (`ThermoFurnaceFeeder`) is minimal. Class: `ThermoFurnaceController` |
| USGS Reston | In-house furnace | — | ★ | Minimal implementation for USGS Reston lab only. Class: `RestonFurnaceManager` |

---

## Extraction Line Valve Actuators

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| Agilent | 34903A GP switch | GPIB or Ethernet | ✓ | Primary actuator for multi-valve extraction lines. Class: `AgilentGPActuator` |
| Arduino | GP actuator | Serial | ⚠ | First command after connect consistently times out (TODO at `arduino_gp_actuator.py:45`). Subsequent commands work normally. |
| Isotopx | NGX controller | Ethernet | ✓ | Valve control routed through NGX spectrometer controller. Class: `NGXGPActuator` |
| MCC | USB DAQ relay | USB | ✓ | Relay output via MCC USB hardware. Class: `MCCGPActuator` |
| NCD | ProXR relay | Ethernet | ✓ | HTTP-style commands to ProXR module. Class: `ProXRActuator` |
| NMGRL (in-house) | Furnace actuator | RPC | ★ | Controls NMGRL furnace sample loader remotely. Class: `NMGRLFurnaceActuator` |
| LabJack | T4 Pro | USB or Ethernet | ✓ | GPIO relay output. Class: `T4Actuator` |
| LabJack | U3 | USB | ✓ | GPIO relay output. Class: `U3Actuator` |
| Thermo | Qtegra proxy | Ethernet → Qtegra | ✓ | Valve commands proxied through Qtegra. Class: `QtegraGPActuator` |
| PLC2000 | Modbus relay | Modbus RTU | ✓ | Modbus coil writes for relay control. Class: `PLC2000GPActuator` |
| Pychron | Remote actuator | ZMQ/RPC | ✓ | Connects to a remote Pychron instance. Class: `PychronGPActuator` |
| WiscAr | In-house | RPC | ★ | University of Wisconsin–Madison lab specific. Class: `WiscArGPActuator` |
| — | Switch Controller | Serial | ✓ | Generic ASCII serial relay board. Class: `SwitchController` |
| — | Dummy actuator | — | ✓ | Simulation and testing only. Class: `DummyGPActuator` |

---

## Vacuum Gauges

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| MKS Instruments | Multi-Gauge controller | Serial | ✓ | ASCII command format `@dd command;FF`. Multi-channel; power on/off per channel. Class: `MKSController` |
| MKS Instruments | Spinning Rotor Gauge (SRG) | Serial | ✓ | Class: `MKSSRG` |
| Granville-Phillips | MicroIon controller | Serial | ✓ | Multiple variants: standard, headless, Qtegra proxy, Pychron remote. Class: `MicroIonController` |
| Pfeiffer Vacuum | MaxiGauge | Serial (Modbus RS-485) | ✓ | Class: `PfeifferMaxiGaugeController` |
| Varian | XGS-600 | Serial SCPI | ✓ | Class: `XGS600GaugeController` |
| Inficon | IGC100 | Serial SCPI | ✓ | Class: `IGC100GaugeController` |
| PLC2000 | Modbus gauge/heater | Modbus RTU or TCP | ✓ | Combined heater and gauge controller. Class: `PLC2000GaugeController` |
| LabJack | U3 ADC gauge | USB | ✓ | Reads pressure via U3 analog input. Class: `U3GaugeController` |
| Thermo | Qtegra proxy | Ethernet → Qtegra | ✓ | Reads gauge values through Qtegra. Class: `QtegraGaugeController` |
| — | ADC gauge (generic) | Analog (MCC USB / ADC) | ✓ | Generic ADC-backed gauge reading. Class: `ADCGaugeController` |

---

## Ion Pumps and Turbomolecular Pumps

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| SPC | Ion pump controller | Serial | ✓ | On/off control; current/voltage monitoring. Class: `SPCIonPumpController` |
| TerraNova | Ion pump controller | Serial | ✓ | Class: `TerraNovaIonPumpController` |
| Pfeiffer Vacuum | HiPace turbomolecular pump | Serial (Modbus-like) | ✓ | On/off control; rotation speed monitoring. Class: `HiPace` |

---

## Temperature Controllers

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| Watlow | EZZone PM / PM6 / F4 | Modbus RTU or Standard ASCII | ✓ | Dual protocol (`StandardProtocol` and `ModbusProtocol`). Used in Fusions Diode and furnace systems. Class: `WatlowEZZone` |
| Eurotherm | 818 | Serial (Modbus RTU) | ✓ | Used in NMGRL furnace. Class: `Eurotherm818` |
| Eurotherm | 2408 / 3504 | Serial (Modbus RTU) | ✓ | Multi-zone controllers. Class: `Eurotherm` |
| Lakeshore | Model 325 | Serial or GPIB | ✓ | Dual-zone cryogenic. Class: `Model325TemperatureController` |
| Lakeshore | Model 330 | Serial or GPIB | ✓ | Class: `Model330TemperatureController` |
| Lakeshore | Model 331 | Serial or GPIB | ✓ | Class: `Model331TemperatureController` |
| Lakeshore | Model 335 | Serial | ✓ | Class: `Model335TemperatureController` |
| Lakeshore | Model 336 | Serial | ✓ | Class: `Model336TemperatureController` |
| Scientific Instruments | SI9700 | Serial | ✓ | Cryogenic/liquid helium controller. Class: `SI9700Controller` |
| Omega | DPi32 temperature monitor | Serial RS-232 | ✓ | Read-only temperature monitor. Class: `DPi32TemperatureMonitor` |
| AQUA | Temperature controller | Serial | ✓ | Class: `AquaController` |

---

## Pyrometers

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| Micro-Epsilon | IR thermometer | Serial | ✓ | Used in Fusions laser systems. Class: `MicroEpsilonPyrometer` |
| Mikron | GA140 | Serial | ✓ | Infrared pyrometer for high-temperature measurement. Class: `MikronGA140Pyrometer` |
| — | ADC-based pyrometer | Analog (ADC) | ✓ | Generic pyrometer via analog voltage input. Class: `PyrometerTemperatureMonitor` |

---

## Motion Controllers

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| Aerotech | — | Serial (proprietary) | ✓ | Multi-axis motion controller. Class: `AerotechMotionController` |
| Newport | ESP301 / ESP302 | Serial ASCII | ⚠ | `use_hack_axis=True` workaround active: uses displacement-based positioning instead of native axis commands (`newport_motion_controller.py:306–319`). Class: `NewportMotionController` |
| Zaber Technologies | Linear stages | Serial (binary or ASCII) | ✓ | Legacy binary protocol and modern ASCII protocol both supported. Class: `ZaberMotionController` |
| Thorlabs | Kinesis | USB (Kinesis SDK) | ✓ | Class: `KinesisMotionController` |
| Schneider Electric | MDrive | Serial (MDrive ASCII) | ✓ | Stepper motor controllers. Headless variant available. Class: `MDriveMotor` |
| Photon Machines | Kerr microcontroller | Serial (proprietary) | ✓ | Internal stage controller for Fusions laser systems. Home move uses velocity-profile-mode workaround (`kerr_motor.py:716`). Classes: `KerrMotor`, `KerrMicrocontroller` |

---

## Data Acquisition

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| Agilent / Keysight | 34970A multiplexer / DAC | GPIB or Ethernet | ✓ | Multi-channel with polynomial channel-mapping equations. Classes: `AgilentMultiplexer`, `AgilentDAC`, `AgilentDMM` |
| Agilent / Keysight | U2351A | GPIB or Ethernet | ✓ | Modular DAQ. Class: `U2351A` |
| LabJack | U3 / U3-LV | USB | ✓ | Multi-channel ADC, GPIO, I2C, SPI, timers. Classes: `U3LV`, `HeadlessU3LV` |
| LabJack | T4 Pro | USB or Ethernet | ✓ | Successor to U3; higher resolution ADC. Class: `T4` |
| Measurement Computing | USB DAQ (MCC) | USB | ✓ | DAQmx-compatible interface. Class: `MccCommunicator` |
| NCD | ProXR ADC | Ethernet | ✓ | ADC expansion for ProXR relay modules. Class: `ProXRADC` |
| Keithley | ADC | Serial or GPIB | ✓ | SCPI-based. Class: `KeithleyADC` |
| Omega | ADC | Serial | ✓ | Class: `OmegaADC` |

---

## Environmental and Lab Monitoring

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| — | TempHum MicroServer | Ethernet | ✓ | Standalone Ethernet sensor for lab temperature and humidity. Class: `TempHumMicroServer` |
| — | DHT11 | GPIO (Raspberry Pi) | ✓ | Direct-read temperature and humidity via GPIO. Class: `DHT11` |
| — | Air transducer | Analog (ADC) | ✓ | Pressure transducer via ADC input. Class: `AirTransducer` |
| — | Thermocouple transducer | Analog (ADC) | ✓ | Thermocouple voltage via ADC. Class: `ThermocoupleTransducer` |
| — | Analog power meter | ADC | ✓ | Laser power monitoring via analog voltage. Class: `AnalogPowerMeter` |
| Eaton / Powerware | Ferrups UPS | Serial | ✓ | Uninterruptible power supply monitoring. Class: `FerrupsUPS` |
| — | Bakeout PLC | Modbus RTU | ✓ | Modbus-based bakeout heater controller. Class: `BakeoutPLC` |
| — | Pneumatics controller | Modbus | ✓ | Polynomial-mapped pressure/output control. Class: `Pneumatics` |
| SS Cooling | ThermoRack | Serial | ✓ | Rack-mount chiller controller. Class: `ThermoRack` |
| — | Pychron chiller | RPC | ✓ | Remote chiller connected via Pychron RPC. Class: `PychronChiller` |
| Raspberry Pi | GPIO | GPIO | ✓ | General-purpose digital I/O. Class: `RPiGPIO` |

---

## Sample Handling

| Manufacturer | Model | Protocol | Status | Notes |
|---|---|---|---|---|
| NMGRL (in-house) | Furnace feeder / funnel | GPIO (motor) + Serial | ★ | Stepper motor-driven sample drop into NMGRL resistance furnace. Classes: `NMGRLFurnaceFeeder`, `NMGRLFurnaceFunnel` |
| — | Rotary dumper (Arduino) | Serial | ★ | Arduino-controlled rotary sample dumper. Class: `RotaryDumper` |
| — | Sample changer | RPC / Extraction line | ✓ | Integrates with the valve network and extraction line state machine. Class: `SampleChanger` |
| Photon Machines | Fiber light controller | GPIO / Serial / USB | ✓ | Illumination for stage camera. Variants: U3 (LabJack), Arduino. Class: `FiberLight` |

---

## Communication Protocols

This table summarises the protocols Pychron uses and the Python library that implements each one.

| Protocol | Library | Typical Use |
|---|---|---|
| Serial RS-232 / RS-485 | `pyserial` | Temperature controllers, gauges, laser logic boards, motion controllers |
| Ethernet TCP | `socket` / `requests` | Spectrometer proxy (Qtegra), NGX, Agilent DAQ, remote actuators |
| GPIB / IEEE-488 | `PyVISA` + NI-VISA | Agilent instruments, LakeShore controllers |
| Modbus RTU (Serial) | `pymodbus` | Watlow, Eurotherm, PLC2000, Pfeiffer gauges |
| Modbus TCP | `pymodbus` | PLC2000 in networked configurations |
| USB (LabJack) | `LabJackPython` | LabJack U3 and T4 for ADC, GPIO, I2C |
| USB (MCC) | MCC Universal Library | MCC DAQ cards for relay and analog I/O |
| USB (Kinesis) | Thorlabs Kinesis SDK | Thorlabs motion stages (Windows only) |
| ZMQ PUB/SUB | `pyzmq` | Dashboard data stream; inter-process instrument broadcasts |
| Pychron RPC | Internal (ZMQ/socket) | Cross-node hardware commands (pyExperiment → pyValve / furPi) |
| I2C | LabJack U3 (bit-bang) | LDEO furnace DAC and EEPROM (LJTick-DAC) |
| GPIO | `RPi.GPIO` | Raspberry Pi direct I/O; DHT11 sensor |

---

## Known Issues

The following are documented defects or incomplete implementations in the `main` branch. Each entry includes the relevant file so issues can be tracked to source.

- **NGX command reliability** — The NGX controller (`pychron/hardware/isotopx_spectrometer_controller.py`) uses a threading lock and retry logic for valve-state queries. Intermittent command drop-outs have been observed; they are handled silently by retry. Labs using NGX should monitor logs for repeated retry events, which may indicate a network or Ethernet adapter issue on the NGX instrument.

- **LDEO furnace temperature control not implemented** — `pychron/hardware/labjack/ldeo_furnace.py:159` emits a `"Temperature control not implemented"` warning at runtime. The I2C DAC setpoint path executes but there is no closed-loop control. The furnace can write setpoints but cannot regulate temperature autonomously.

- **Quadera spectrometer hardware controller is a stub** — `pychron/hardware/quadera_spectrometer_controller.py` contains only `pass`. The higher-level spectrometer, magnet, source, and detector classes exist, but no communication with the instrument is possible. `QuaderaSpectrometer` cannot be used in production.

- **TAP CO₂ laser class body is `pass`** — `pychron/lasers/laser_managers/tap_laser_manager.py` (`TAPLaserManager`). No power control, stage control, or communication implemented. Not deployable.

- **TAP Diode laser power control missing** — `TAPDiodeManager` (same file) has Zaber stage motion wired up but no mechanism to set or read laser power. Stage positioning works; laser output control does not.

- **Arduino actuator first-command timeout** — `pychron/hardware/arduino/arduino_gp_actuator.py:45` has a TODO noting that the first command after connection reliably times out. A workaround (send a dummy command on connect) is noted but not implemented. Labs using Arduino actuators should expect the first valve command after startup to fail.

- **MAP spectrometer is a legacy stub** — `pychron/spectrometer/map/` contains channel selection and magnet movement but no acquisition, source control, or plugin registration. Not usable with pyExperiment.

- **Newport motion controller hack axis** — `pychron/hardware/newport/newport_motion_controller.py:306–319` enables `use_hack_axis=True`, substituting a displacement-based positioning workaround for native ESP axis commands. This works for laser stages but may break for other Newport ESP301/302 configurations.

- **APIS controller partial** — `pychron/hardware/apis_controller.py` has multiple methods with `pass` bodies, including power and intensity control. Status is Partial; do not rely on power regulation through this class.

- **LDEO/Lamont furnace unit-conversion logic error** — `pychron/hardware/labjack/ldeo_furnace.py:124–126` contains `if not units == "volts" or units == "temperature"` which evaluates incorrectly due to operator precedence. Should be `if not (units == "volts" or units == "temperature")`. The bug may cause incorrect unit handling when reading temperature in some configurations.

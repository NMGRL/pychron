Hardware
---------

Make a new Device
~~~~~~~~~~~~~~~~~~

You have two options for making a new device, CoreDevice and AbstractDevice. Use CoreDevice when you are directly interfacing with a physical device.
Use AbstractDevice if you interface with the device via a secondary device. For example when you want to access a physical device with an analog output.
Lets say you want to read the analog output from a power meter. First create a PowerMeter(AbstractDevice) class than use or create a ADC(CoreDevice) class.
ADC(CoreDevice) class communicates with the Analog-to-Digital Converter device and the PowerMeter class converts the raw signal from ADC(CoreDevice) into a power value i.e. Watts


Using the AbstractDevice allows you to interface with the physical power meter using a variety of ADC's that typically will have different communication protocols. Switching ADCs
is a simple as switch the a single value in the PowerMeter(AbstractDevice)'s configuration file.
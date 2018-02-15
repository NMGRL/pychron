def set_environmentals(obj, ed):
    def func(stag, attr, device, key, default=0):
        lt = ed.get(attr, [])
        if lt:
            v = next((t['value'] for t in lt if t['device'] == device and
                      t['name'] == key), default)
            setattr(obj, stag, v)

    func('lab_temperature', 'lab_temperatures', 'EnvironmentalMonitor', 'Lab Temp.')
    func('lab_humidity', 'lab_humiditys', 'EnvironmentalMonitor', 'Lab Hum.')
    func('lab_airpressure', 'lab_pneumatics', 'AirPressure', 'Pressure')
    func('east_diffuser_temperature', 'lab_temperatures', 'RPiWeather', 'Lab Temp. 3')
    func('east_return_temperature', 'lab_temperatures', 'RPiWeather', 'Lab Temp. 4')
    func('outside_temperature', 'lab_temperatures', 'NOAA', 'Outside Temp')

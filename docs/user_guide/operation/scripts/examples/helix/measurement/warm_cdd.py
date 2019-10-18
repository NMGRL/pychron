#!Measurement
DELAY=8
DAC=4.88551
DET='CDD'

def main(outlet_valve='V'):
    """
       if this it the last run don't warm detector
       
       else
          1. protect detector. set deflection to 2000
          2. open outlet_valve
          3. wait DELAY seconds for mass spec to pump out
          4. position magnet at DAC
          5. return deflection to config value
    """
    if not is_last_run():
        info('Warming {}'.format(DET))
        
        set_deflection(DET, 2000)
        
        open(outlet_valve)
        sleep(DELAY)
        
        position_magnet(DAC, dac=True)
        set_deflection(DET)
        
    else:
        info('NOT Warming {}'.format(DET))
'''
'''
def main():
    info('Pump Microbone')
    if is_closed('A'):
        open(description=   'F')
   
    sleep(1)
    close(description=  'CO2 Laser to Roughing')
    close(description=  'Microbone to Minibone')
    open(description=   'Microbone to Turbo')
    open(description=   'Microbone to Getter NP-10H')
    open(description=   'Microbone to Getter NP-10C')
    open(description=   'Microbone to CO2 Laser')
    open(description=   'Microbone to Inlet Pipette')
    sleep(1)
    set_resource(name='CO2PumpTimeFlag', value=30)
    release('FelixMiniboneFlag')  
    release('FelixCO2Flag')
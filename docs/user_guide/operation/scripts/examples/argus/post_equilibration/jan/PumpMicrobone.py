'''
'''
def main():
    info('Pump Microbone')
    close(description="Jan Inlet")
    if is_closed('F'):
        open(description=   'Microbone to CO2 Laser')
    else:
        close(name="T", description="Microbone to CO2 Laser")
    sleep(1)
    close(description=  'CO2 Laser to Roughing')
    
    #close(description=  'Microbone to Minibone')
    
    open(description=   'Microbone to Turbo')
    open(description=   'Microbone to Getter NP-10H')
    open(description=   'Microbone to Getter NP-10C')
    #open(description=   'Microbone to CO2 Laser')
    open(description=   'Microbone to Inlet Pipette')
    sleep(1)
    
    set_resource(name='CO2PumpTimeFlag', value=30)
    release('JanCO2Flag')
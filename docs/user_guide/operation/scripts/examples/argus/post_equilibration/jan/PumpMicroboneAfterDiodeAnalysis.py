'''
'''
def main():
    info('Pump Microbone After Jan diode analysis')
    close(description="Jan Inlet")
    close(description=  'Microbone to Minibone')
    
    open(description=   'Microbone to Turbo')
    open(description=   'Microbone to Getter NP-10H')
    open(description=   'Microbone to Getter NP-10C')
    open(description=   'Microbone to CO2 Laser')
    #open(description=   'CO2 Laser to Jan')
    open(description=   'Microbone to Inlet Pipette')
    sleep(1)
    

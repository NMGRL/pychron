'''
'''

def main():
    info('Prepare for CO2 minibone analysis')
    close(description='Jan Inlet')
    close(description='CO2 Laser to Felix')
    
    open(description='Jan Ion Pump')
    open(description='Microbone to Turbo')

    close('P')
    close('Q')
    close('I')

    open(description='Microbone to Minibone')

    #prepare microbone
    
    open(description='Microbone to Inlet Pipette')
    open(description='Microbone to Getter NP-10C')
    open(description='Microbone to Getter NP-10H')
    #open(description='CO2 Laser to Jan')
    open(description='Microbone to CO2 Laser')
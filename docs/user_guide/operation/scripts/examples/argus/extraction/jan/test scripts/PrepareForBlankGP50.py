
def main():
    info('Prepare for Blank GP50 analysis')
    close(description='Jan Inlet')
    open(description='Jan Ion Pump')
    open(description='Microbone to Turbo')
    open(description='Microbone to Inlet Pipette')
    close(description='Microbone to Getter NP-10C')
    close(description='Microbone to Getter NP-10H')
    
    
    close(description='Quad Inlet')
    close(description='Minibone to Bone')
    close(description='Minibone to Turbo')
    open(description='Microbone to Minibone')

    
    close(description='CO2 Laser to Felix')
    close(description='CO2 Laser to Jan')
    close(description='Microbone to CO2 Laser')
    
    sleep(20)

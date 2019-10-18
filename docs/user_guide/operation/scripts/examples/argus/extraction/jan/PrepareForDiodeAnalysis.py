'''
'''

def main():
    info('Prepare for Diode analysis on Jan via minibone')
    close(description='Jan Inlet')
    open(description='Jan Ion Pump')
    open(description='Microbone to Inlet Pipette')
    close(description='Microbone to Minibone')
    open(description='Microbone to Getter NP-10C')
    open(description='Microbone to Getter NP-10H')
    close(description='CO2 Laser to Felix')
    close(description='CO2 Laser to Jan')
    close(description='Microbone to CO2 Laser')
    open(description='Microbone to Turbo')

    close(description="Outer Pipette 1")
    close(description="Outer Pipette 2")
    open(description='Bone to Minibone')
    open(description='Bone to Getter GP-50')
    close(description='Bone to CO2 Laser')
    open(description='Bone to Diode Laser')
    open(description='Bone to Turbo')
    
    close(description='Quad Inlet')
    open(description='Minibone to Bone')
    open(description='Minibone to Turbo')
    

    

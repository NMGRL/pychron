def main():
    info('Prepare for Diode Analysis')
    close(description='Felix Inlet')
    open(description='Felix Ion Pump')
    close(description='Bone to Minibone')
    open(description='Bone to Getter GP-50')
    close(description='Bone to CO2 Laser')
    open(description='Bone to Diode Laser')
    
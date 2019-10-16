def main():
    info('Prepare for Air Shot')
    close(description='Jan Inlet')
    open(description='Jan Ion Pump')
    close(description='Minibone to Bone')
    close(description='Bone to Minibone')
    close(description='Minibone to Turbo')
    close(name="Q", description="Quad Inlet")
    open(description='Microbone to Turbo')
    open(description='Microbone to Inlet Pipette')
    open(description='Microbone to Getter NP-10C')
    open(description='Microbone to Getter NP-10H')
    close(description='Microbone to CO2 Laser')
    
'''
eqtime: 15 
'''
def main():
    info('Jan microbone and minibone blank analysis')

    if analysis_type=='blank':
        gosub('jan:WaitForMiniboneAccess')

        close(name="Q", description="Quad Inlet")
        close(name="I", description="Minibone to Bone")
        close(name="P", description="Minibone to Turbo")
        open(name="L", description="Microbone to Minibone")
        close(name="T", description="Microbone to CO2 Laser")
        close(name="K", description="Microbone to Getter NP-10C")
        close(name="M", description="Microbone to Getter NP-10H")
        open(name="S", description="Microbone to Inlet Pipette")
        sleep(duration=10.0)
        close(description='Microbone to Turbo')
        
        sleep(duration)
        sleep(cleanup)



    
'''
'''
ION_PUMP='V'
INLET = 'H'
EQTIME = 15

def main():
    info("Cocktail Pipette x1")
    gosub('extraction:felix:WaitForMiniboneAccess')
    gosub('extraction:felix:PrepareForAirShot')
    gosub('extraction:common:EvacPipette1')
    gosub('extraction:common:FillPipette1')
    gosub('extraction:felix:PrepareForAirShotExpansion')
    gosub('extraction:common:ExpandPipette1')
    #close(description='Outer Pipette 2')
    
    #equilibrate
    close(ION_PUMP)
    sleep(3)
    open(INLET)
    sleep(EQTIME)
    close(INLET)
    gosub('post_equilibration:felix_pump_air')
    sleep(10)
    close(description='Outer Pipette 1')
    
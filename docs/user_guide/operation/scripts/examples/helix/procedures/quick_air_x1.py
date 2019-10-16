'''
'''
ION_PUMP='V'
INLET = 'H'
EQTIME = 15

def main():
    info("Air Pipette x1")
    gosub('extraction:felix:WaitForMiniboneAccess')
    gosub('extraction:felix:PrepareForAirShot')
    gosub('extraction:common:EvacPipette2')
    gosub('extraction:common:FillPipette2')
    gosub('extraction:felix:PrepareForAirShotExpansion')
    gosub('extraction:common:ExpandPipette2')
    #close(description='Outer Pipette 2')
    
    #equilibrate
    close(ION_PUMP)
    sleep(3)
    open(INLET)
    sleep(EQTIME)
    close(INLET)
    gosub('post_equilibration:felix_pump_air')
    sleep(10)
    close(description='Outer Pipette 2')
    
'''
modifier: 01
eqtime: 15
'''
def main():
    info('Jan Air Script x1')
    gosub('jan:WaitForMiniboneAccess')
    gosub('jan:PrepareForAirShot')
    open('T')
    open('Q')
    gosub('jan:EvacPipette2')
    gosub('common:FillPipette2')
    gosub('jan:PrepareForAirShotExpansion')
    gosub('common:ExpandPipette2')
    #close(name="T", description="Microbone to CO2 Laser")
    close('L')
    sleep(3)
    

 
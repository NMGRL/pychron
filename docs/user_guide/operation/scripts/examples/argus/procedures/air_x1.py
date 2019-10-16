'''
modifier: 01
eqtime: 10
'''
def main():
    info('Jan Air Script x1')
    gosub('jan:WaitForMiniboneAccess')
    gosub('jan:PrepareForAirShot')
    gosub('jan:EvacPipette2')
    gosub('common:FillPipette2')
    gosub('jan:PrepareForAirShotExpansion')
    gosub('common:ExpandPipette2')
    
    #equilibrate
    close(description='Jan Ion Pump')
    sleep(3)
    open('R')
    sleep(15)
    close('R')

 
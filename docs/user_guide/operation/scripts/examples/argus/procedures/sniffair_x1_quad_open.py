'''
modifier: 02
eqtime: 8
'''
def main():
    info("Jan Air Sniff Pipette x1")
    gosub('jan:WaitForMiniboneAccess')
    gosub('jan:PrepareForAirShot')
    open(name="Q", description="Quad Inlet")
    gosub('jan:EvacPipette2')
    gosub('common:FillPipette2')
    gosub('jan:PrepareForAirShotExpansion')
    gosub('common:SniffPipette2')

    #equilibrate
    close(description='Jan Ion Pump')
    sleep(3)
    open('R')
    sleep(15)
    close('R')

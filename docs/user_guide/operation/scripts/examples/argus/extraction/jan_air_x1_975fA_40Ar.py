'''
modifier: 01
eqtime: 15
'''
def main():
    info('Jan Air Script x1')
    gosub('jan:WaitForMiniboneAccess')
    gosub('jan:PrepareForAirShot')
    open(name="Q", description="Quad Inlet")
    gosub('jan:EvacPipette2')
    gosub('common:FillPipette2')
    gosub('jan:PrepareForAirShotExpansion')
    gosub('common:ExpandPipette2')
    close(name="L", description="Microbone to Minibone")
    close(name="K", description="Microbone to Getter NP-10C")
    close(name="M", description="Microbone to Getter NP-10H")
    sleep(duration=3.0)
    
 
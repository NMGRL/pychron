'''
modifier: 03
eqtime: 10
'''
def main():
    info("Jan Cocktail Pipette x1")
    gosub('jan:WaitForMiniboneAccess')
    gosub('jan:PrepareForAirShot')
    open(name="Q", description="Quad Inlet")
    gosub('jan:EvacPipette1')
    gosub('common:FillPipette1') 
    gosub('jan:PrepareForAirShotExpansion')
    gosub('common:ExpandPipette1')
    sleep(duration=2.0)
    close(name="S", description="Microbone to Inlet Pipette")
'''
modifier: 03
eqtime: 10
'''
def main():
    info("Jan Cocktail Pipette x1")
    gosub('jan:WaitForMiniboneAccess')
    gosub('jan:PrepareForAirShot')
    gosub('jan:EvacPipette1_2')
    gosub('common:FillPipette1_2')
    gosub('jan:PrepareForAirShotExpansion')
    gosub('common:ExpandPipette1_2')

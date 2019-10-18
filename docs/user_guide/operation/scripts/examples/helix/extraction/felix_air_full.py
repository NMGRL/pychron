'''
modifier: 02
eqtime: 40
'''

def main():
    info("Air Pipette x1-4 bone only")
    gosub('felix:WaitForMiniboneAccess')
    gosub('felix:PrepareForAirShot')
    
    #open(name='N')
    open(name='Q')
    open(name='D')
    #open(name='B')
    
    gosub('common:EvacPipette2')
    gosub('common:FillPipette2')
    gosub('felix:PrepareForAirShotExpansion')
    gosub('common:ExpandPipette2')
    
    #close(name='B')
    close(name='Q')
    #close(name='E')
    #close(name='D')
    #close(name='N')
    close(description='Outer Pipette 2')
    
    

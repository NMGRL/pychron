def main():
    '''
        this script is used for pumping out the minibone in causes when Jan did not explicitly use it. For instance when running a co2 analysis
        the minibone may go static (both P and L are closed) and during post equilibration L remains closed. 
        
        Therefore this script is used to check the state of the minibone and pump it out thru the microbone if necessary. 
        It works by first checking if Felix is using the Minibone, if so then no action is taken. Otherwise the script checks if the Minibone is static
        and if so will pump it out via L and the Microbone turbo. 
        
    '''
    # is Felix using the minibone
    if get_resource_value(name='FelixMiniboneFlag'):
        info('Felix has access to Minibone')    
    else:
        # Felix is NOT using the minibone so we should take care of pumping it out
        # is Minibone to Turbo closed. only need to pump out minibone if P(Minibone to Turbo) is closed
        if is_closed('P'):
            #just for redundancy set Minibone/Bone pipette section to default state
            close('E')
            open('I')
            
            info('pumping minibone thru Valve "L" and the Microbone')
            open('L')
        
        
def main():
    info('Entering Pump minibone script')
    
    v=get_resource_value(name='JanMiniboneFlag')
    
    info('get resource value {}'.format(v))
    if get_resource_value(name='JanMiniboneFlag'):
        info('Pump minibone')
        close(description='Bone to Minibone')
        
        open(description='Microbone to Minibone')
        #open(description='Minibone to Turbo')
        
        #open(description='Quad Inlet')
        
        open(description='Minibone to Bone')
        set_resource(name='MinibonePumpTimeFlag',value=30)
        sleep(duration=15.0)
        close(description="Outer Pipette 1")
        close(description="Outer Pipette 2")
        release('JanMiniboneFlag')
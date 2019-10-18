def main():
    info('Pump after analysis')
    
    #pump out bone
    open('C')
    
    gosub('jan:PumpMicrobone')

    v=get_resource_value(name='JanMiniboneFlag')
    
    info('get resource value {}'.format(v))

    if get_resource_value(name='JanMiniboneFlag'):
        gosub('jan:PumpMinibone')

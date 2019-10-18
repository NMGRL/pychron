def main():
    info('Pump after analysis')
    gosub('jan:PumpMicrobone')

    v=get_resource_value(name='JanMiniboneFlag')
    
    info('get resource value {}'.format(v))

    if get_resource_value(name='JanMiniboneFlag'):
        gosub('jan:PumpMinibone')

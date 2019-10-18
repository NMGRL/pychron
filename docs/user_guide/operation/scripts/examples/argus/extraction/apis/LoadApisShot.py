def main(shot_name):
    # load air shot behind Microbone to Getter NP-10H
    info('extracting {}'.format(shot_name))
    #for testing just sleep a few seconds
    #sleep(5)
    # this action blocks until completed
    extract_pipette(shot_name)
    
    #isolate microbone
    close(description='Microbone to Turbo')
    close('C')

    #delay to ensure valve is closed and air shot not factionated
    sleep(2)
    
    #expand air shot to microbone
    #info('equilibrate with microbone')
    #open(description='Microbone to Getter NP-10H')
    #close('M')
    sleep(3)
    #isolate microbone ?
    #close(description='Microbone to Getter NP-10H')
    
    
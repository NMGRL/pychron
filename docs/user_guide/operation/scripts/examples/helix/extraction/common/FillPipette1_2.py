'''
'''

def main():
    info('Fill Pipettes 1 and 2')
    close(description='Outer Pipette 1')
    close(description='Outer Pipette 2')
    sleep(1)
    if analysis_type=='blank':
        info('Not filling pipettes')
    else:
        info('filling pipettes')
        open(description='Inner Pipette 1')
        open(description='Inner Pipette 2')
    sleep(15)
    close(description='Inner Pipette 1')
    close(description='Inner Pipette 2')
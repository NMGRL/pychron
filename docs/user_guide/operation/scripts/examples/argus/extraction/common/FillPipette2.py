'''
'''
def main():
    info('Fill Pipette 2')
    close(description='Outer Pipette 2')
    sleep(1)
    if analysis_type=='blank':
        info('not filling air pipette')
    else:
        info('filling air pipette')
        open(description='Inner Pipette 2')
        
    sleep(15)
    close(description='Inner Pipette 2')
    sleep(1)
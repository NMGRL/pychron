'''
'''

def main():
    info('trap in pipette')
    close(description='Bone to Minibone')
    close(description='Minibone to Bone')
    sleep(2)
    open(description='Bone to Turbo')
    sleep(15)
    close(description='Bone to Turbo')
    sleep(2)
    open(description='Bone to Minibone')

def main():
    info('Evacuate Pipette 2')
    close(description='Minibone to Turbo')
    open(description='Microbone to Minibone')
    close(description='Inner Pipette 2')
    sleep(1)
    open(description='Outer Pipette 2')
    sleep(15)
    
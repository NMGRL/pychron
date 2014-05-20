from SocketServer import BaseRequestHandler

__author__ = 'ross'

import logging

logging.basicConfig()
logger = logging.getLogger('foo')
logger.setLevel(logging.DEBUG)

cnt = 0


class APISEmulator(BaseRequestHandler):
    # def __init__(self, request, addr, server):
    #     self.request=request

    def handle(self):
        cmd = self.request.recv(1024)
        r = 'invalid command'

        logger.debug('handling cmd={}'.format(cmd))
        cmd, values = self._parse(cmd)
        cmd = 'cmd{}'.format(cmd)
        if hasattr(self, cmd):
            f = getattr(self, cmd)
            r = f(*values)
        self.request.send(str(r))

    def testCmd(self):
        return 'OK'

    def cmd100(self):
        """
        return ','.join('B1,B2,B3')
        """
        return 'B1,B2,B3'

    def cmd101(self):
        """
        List of Air run scripts available
        """
        return 'Air1,Air2,Air3'

    def cmd102(self):
        """
        Run ID of the last APIS procedure
        """
        return 'A/1-10000'

    def cmd103(self):
        """
        Pipette record* of the last APIS procedure
        """
        return '''Ar40	1.7963587e-16
Ar38	1.1405441e-19
Ar36	6.0790579e-19'''

    def cmd104(self):
        """
        APIS status: 0=Idle, 1=Pumping pipettes, 2=Loading
        pipettes, 3=Expanding pipettes, 4=Expansion complete

        """
        global cnt
        if cnt > 2:
            return '4'
        else:
            cnt += 1
            return '2'

    def cmd105(self, name):
        """
        105,<name>
        Begin processing the named blank script
        """
        global cnt
        cnt = 0
        return 'ok'

    def cmd106(self, name):
        """
        Begin processing the named air script
        """
        global cnt
        cnt = 0
        return 'ok'

    def cmd107(self):
        """
        Cancel the APIS script in progress
        """
        return 'ok'

    def cmd108(self):
        """
        Set external manifold pumping status as 'true' or 'false'
        """
        return 'ok'

    # def LoadPipette(self, a):
    #     global CNT
    #     CNT=0
    #     return 'OK'
    #
    # def PipetteReady(self):
    #     global CNT
    #     CNT=CNT+1
    #
    #     return 'OK' if CNT==3 else 'NO'

    def _parse(self, cmd):
        args = cmd.split(',')
        c = args[0]
        vs = args[1:]

        return c, vs


if __name__ == '__main__':
    import sys, os, socket
#    root='/Users/ross/Programming/git/pychron_dev'
 #   if not os.path.isdir(root):
  #      root='/Users/argonlab
    root=os.getcwd()
    while 1:
        args=root.split('/')
        if args[-2]=='git' and args[-1].startswith('pychron'):
            break
        else:
            root=os.path.dirname(root)
            
    sys.path.insert(0, root)
    from pychron.emulation_server import EmulationServer
    from pychron.external_pipette.apis_emulator import APISEmulator

    host=socket.gethostbyname(socket.gethostname())
    e = EmulationServer(host, 1080, APISEmulator)
    e.start()


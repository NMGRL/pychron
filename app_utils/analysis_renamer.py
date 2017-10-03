import os

import shutil

from pychron.experiment.utilities.identifier import make_step


class Name:
    def __init__(self, identifier, aliquot, increments):
        self.identifier = identifier
        self.aliquot = aliquot
        self.increments = increments

    def match(self, f, tag,ext='.json'):
        sdn = self.identifier[3:]
        for c, i in enumerate(range(self.increments[0], self.increments[1] + 1)):
            if f == '{}-{:02n}{}.{}{}'.format(sdn, self.aliquot, make_step(i), tag, ext):
                return c

    def make(self, idx, tag):
        sdn = self.identifier[3:]
        return '{}-{:02n}{}.{}.json'.format(sdn, self.aliquot, make_step(self.increments[0] + idx), tag)


def rename(root, src, dest):
    idn = src.identifier[:3]

    for tag in ('.data', 'blanks', 'baselines', 'extraction', 'icfactors', 'logs', 'intercepts', 'peakcenter'):
        r = os.path.join(root, idn, tag)

        ext = '.json'
        if tag == 'logs':
            t = 'logs'
            ext = '.log'
        elif tag == '.data':
            t = 'dat'
        else:
            t = tag[:4]

        for f in os.listdir(r):
            idx = src.match(f, t, ext)
            if idx is not None:
                d = dest.make(idx, t)
                print 'moving {} to {}'.format(f, d)
                shutil.move(os.path.join(r, f), os.path.join(r, d))


def main():
    root = '/Users/argonlab2/PychronDev/data/.dvc/repositories/IR986 copy'

    # src = Name('65855', 5, (5, 9))
    # dest = Name('65855', 6, (0, 4))
    # rename(root, src, dest)

    src = Name('65855', 3, (0, 4))
    dest = Name('65856', 1, (0, 4))
    rename(root, src, dest)

    src = Name('65855', 4, (0, 4))
    dest = Name('65856', 2, (0, 4))
    rename(root, src, dest)



if __name__ == '__main__':
    main()

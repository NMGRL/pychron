import json
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
            if f == '{}-{:02n}{}{}{}'.format(sdn, self.aliquot, make_step(i), tag, ext):
                return c

    def make(self, idx, tag):
        sdn = self.identifier[3:]
        return '{}-{:02n}{}.{}.json'.format(sdn, self.aliquot, make_step(self.make_increment(idx)), tag)

    def make_increment(self, idx):
        return self.increments[0]+idx


def rename(root, src, dest, dry=True):
    idn = src.identifier[:3]

    r = os.path.join(root, idn)

    for f in os.listdir(r):
        idx = src.match(f, '')
        if idx is not None:
            ad = json.load(os.path.join(r,f))

            ad['aliquot'] = dest.aliquot
            ad['increment'] = dest.make_increment(idx)
            d = dest.make(idx, '')
            print 'editing {} to {}'.format(f, d)
            if not dry:
                json.dump(ad, d)

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

        t= '.{}'.format(t)
        for f in os.listdir(r):
            idx = src.match(f, t, ext)
            if idx is not None:
                d = dest.make(idx, t)
                print 'moving {} to {}'.format(f, d)
                if not dry:
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

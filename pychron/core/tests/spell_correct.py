import unittest

from pychron.core.spell_correct import correct


class SpellCorrectTestCase(unittest.TestCase):
    def test_spell_correct1(self):
        n = correct('Fergson', ['Ferguson', 'Finagn'])
        self.assertEqual(n, 'Ferguson')

    def test_spell_correct2(self):
        n = correct('fergson', ['Ferguson', 'Finagn'])
        self.assertEqual(n, 'Ferguson')


if __name__ == '__main__':
    unittest.main()

import unittest

from keepnote.pref import Pref

class Test(unittest.TestCase):

    def test_equals(self):
        pref1 = Pref()
        pref1.get('level1', 'level2', 'key', define=True)
        pref1.set('level1', 'level2', 'key', 'value')
        pref1a = Pref()
        pref1a.get('level1', 'level2', 'key', define=True)
        pref1a.set('level1', 'level2', 'key', 'value')

        self.assertTrue(pref1 == pref1a)
        self.assertFalse(pref1 != pref1a)

        pref2 = Pref()
 
        self.assertFalse(pref1 == pref2)
        self.assertTrue(pref1 != pref2)
 
        self.assertFalse(pref1 == 'asdf')

import mock
from mock import Mock, call
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
    
    def test_is_dirty_1(self):
        pref = Pref()
        
        self.assertEquals(False, pref.is_dirty())
    
    def test_is_dirty_2(self):
        pref = Pref()
        pref.set('key', True)
        
        self.assertEquals(True, pref.is_dirty())
    
    def test_is_dirty_3(self):
        pref = Pref()
        pref.get('level1', 'level2', 'key', define=True)
        pref.set('level1', 'level2', 'key', False)
        
        self.assertEquals(True, pref.is_dirty())
    
    def test_reset_dirty(self):
        pref = Pref()
        pref.get('level1', 'level2', 'key', define=True)
        pref.set('level1', 'level2', 'key', False)
        pref.reset_dirty()
        
        self.assertEquals(False, pref.is_dirty())
    
    def test_get_change_event(self):
        pref = Pref()
        pref.get('level1', 'level2', 'key', define=True)
        handler = Mock()
        pref.change_listeners.add(handler)
 
        pref.get('level1', 'level2', 'key')
         
        handler.assert_has_calls([])
    
    def test_get_with_define_change_event(self):
        pref = Pref()
        handler = Mock()
        pref.change_listeners.add(handler)
 
        pref.get('level1', 'level2', 'key', define=True)
         
        handler.assert_has_calls([call()])
    
    def test_set_change_event(self):
        pref = Pref()
        pref.get('level1', 'level2', 'key', define=True)
        handler = Mock()
        pref.change_listeners.add(handler)

        pref.set('level1', 'level2', 'key', False)
        
        handler.assert_has_calls([call()])


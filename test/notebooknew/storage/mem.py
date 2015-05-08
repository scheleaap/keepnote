import unittest

from keepnote.notebooknew.storage.mem import *
from test.notebooknew.storage import NotebookStorageTestBase 

class InMemoryStorageTest(unittest.TestCase, NotebookStorageTestBase):
    def __init__(self, *args, **kwargs):
        super(InMemoryStorageTest, self).__init__(*args, **kwargs)
        self.storage = None
    
    def setUp(self, *args, **kwargs):
        super(InMemoryStorageTest, self).setUp(*args, **kwargs)
        self.storage = InMemoryStorage(None)
        
    def create_notebook_storage(self):
        return self.storage
    
    def test_fs_repr(self):
        s = InMemoryStorage()
        repr(s)

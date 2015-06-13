# -*- coding: utf-8 -*-

import io
import os
import StringIO as stringio
import unittest

from keepnote.notebooknew.storage import *
from test.utils import assert_file_object_equals

DEFAULT_ID = 'my_id_%s'
DEFAULT_TITLE = 'my_title'
DEFAULT_ATTRIBUTES = { 'title': DEFAULT_TITLE, 'key2': 'value2' }
CONTENT_TYPE_HTML = 'text/html'
DEFAULT_HTML_PAYLOAD_PATH = '../../../tests/data/content/index.html'
DEFAULT_HTML_PAYLOAD_NAME = os.path.basename(DEFAULT_HTML_PAYLOAD_PATH)
DEFAULT_PNG_PAYLOAD_PATH = '../../../tests/data/content/image.png'
DEFAULT_PNG_PAYLOAD_NAME = os.path.basename(DEFAULT_PNG_PAYLOAD_PATH)

class StoredNotebookTest(unittest.TestCase):
    def test_object_fields_initialized(self):
        notebook = StoredNotebook({ 'key': 'value' })

        self.assertEqual({ 'key': 'value' }, notebook.attributes)

    def test_equals(self):
        notebook1 = create_stored_notebook()
        notebook1a = create_stored_notebook()

        self.assertTrue(notebook1 == notebook1a)
        self.assertFalse(notebook1 != notebook1a)

        notebook2 = create_stored_notebook(attributes=None)

        self.assertFalse(notebook1 == notebook2)
        self.assertTrue(notebook1 != notebook2)

        self.assertFalse(notebook1 == 'asdf')

class StoredNodeTest(unittest.TestCase):
    def test_object_fields_initialized(self):
        node = StoredNode('id', 'text/html', { 'key': 'value' }, ['name'])

        self.assertEqual('id', node.node_id)
        self.assertEqual('text/html', node.content_type)
        self.assertEqual({ 'key': 'value' }, node.attributes)
        self.assertEqual(['name'], node.payload_names)

    def test_equals(self):
        node1 = create_stored_node(payload_names=['name'])
        node1a = create_stored_node(payload_names=['name'])

        self.assertTrue(node1 == node1a)
        self.assertFalse(node1 != node1a)

        node2 = create_stored_node(node_id=None)
        node3 = create_stored_node(content_type=None)
        node4 = create_stored_node(attributes=None)
        node5 = create_stored_node(payload_names=None)

        self.assertFalse(node1 == node2)
        self.assertFalse(node1 == node3)
        self.assertFalse(node1 == node4)
        self.assertFalse(node1 == node5)
        self.assertTrue(node1 != node2)
        self.assertTrue(node1 != node3)
        self.assertTrue(node1 != node4)
        self.assertTrue(node1 != node5)

        self.assertFalse(node1 == 'asdf')

class NotebookStorageTestBase(object):
    def test_add_nodes_without_payload(self):
        # Add nodes first.
        s = self.create_notebook_storage()
        id1 = add_node(s, i=1, payloads=[], payload_paths=[])
        id2 = add_node(s, i=2, payloads=[], payload_paths=[])
        
        # Then read them.
        s = self.create_notebook_storage()
        self.assertEqual(create_stored_node(i=1, payload_names=[]), s.get_node(id1))
        self.assertEqual(create_stored_node(i=2, payload_names=[]), s.get_node(id2))
 
    def test_add_node_twice(self):
        s = self.create_notebook_storage()
        add_node(s, i=1)
        with self.assertRaises(NodeAlreadyExistsError):
            add_node(s, i=1)

    def test_add_node_character_encoding_and_escaping(self):
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s, content_type=u'<äëïöüß€&ש>', attributes={ u'<äëïöüß€&ש>': u'<äëïöüß€&ש>' }, payloads=[(u'äëïöüß€ש', stringio.StringIO(u'<äëïöüß€&ש> </text>'.encode('utf-8')))], payload_paths=[])
 
        # Then read it.
        s = self.create_notebook_storage()
        self.assertEquals(create_stored_node(content_type=u'<äëïöüß€&ש>', attributes={ u'<äëïöüß€&ש>': u'<äëïöüß€&ש>' }, payload_names=[u'äëïöüß€ש']), s.get_node(id_))
    
    def test_get_node_nonexistent(self):
        s = self.create_notebook_storage()
        with self.assertRaises(NodeDoesNotExistError):
            s.get_node('node_id')
    
    def test_get_all_nodes(self):
        # Add nodes first.
        s = self.create_notebook_storage()
        add_node(s, i=1)
        add_node(s, i=2)
 
        # Then read them.
        s = self.create_notebook_storage()
        self.assertEquals([create_stored_node(i=1), create_stored_node(i=2)], list(s.get_all_nodes()))

    def test_has_node(self):
        s = self.create_notebook_storage()
        
        # Make sure the node is not there.
        self.assertFalse(s.has_node(DEFAULT_ID))
        
        add_node(s)
        
        # Then make sure it is there.
        s = self.create_notebook_storage()
        self.assertTrue(s.has_node(DEFAULT_ID))
        
    def test_remove_node(self):
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s, i='AA')
 
        # Then make sure it is there.
        s = self.create_notebook_storage()
        self.assertTrue(s.has_node(id_))
   
        # Then remove it.
        s = self.create_notebook_storage()
        s.remove_node(id_)
   
        # Then make sure it is not there.
        s = self.create_notebook_storage()
        self.assertFalse(s.has_node(id_))
        
    def test_remove_node_nonexistent(self):
        s = self.create_notebook_storage()
        with self.assertRaises(NodeDoesNotExistError):
            s.remove_node('node_id')
    
    def test_add_node_payload(self):
        s = self.create_notebook_storage()
        id_ = add_node(s, i=1)

        # Add payload first.
        with io.open(DEFAULT_HTML_PAYLOAD_PATH, mode='rb') as f:
            s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, f)
        
        # Then read the node and payload.
        s = self.create_notebook_storage()
        self.assertEqual(create_stored_node(i=1, payload_names=[DEFAULT_HTML_PAYLOAD_NAME]), s.get_node(id_))
        with io.open(DEFAULT_HTML_PAYLOAD_PATH, mode='rb') as f1:
            with s.get_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME) as f2:
                assert_file_object_equals(self, f1, f2)
    
    def test_add_node_payload_twice(self):
        s = self.create_notebook_storage()
        id_ = add_node(s, i=1)

        with io.open(DEFAULT_HTML_PAYLOAD_PATH, mode='rb') as f:
            s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, f)
        
        with self.assertRaises(PayloadAlreadyExistsError):
            with io.open(DEFAULT_HTML_PAYLOAD_PATH, mode='rb') as f:
                s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, f)
    
    def test_add_node_payload_nonexistent_node(self):
        s = self.create_notebook_storage()
        with self.assertRaises(NodeDoesNotExistError):
            s.add_node_payload('node_id', 'payload_name', None)

    def test_get_node_payload_nonexistent(self):
        s = self.create_notebook_storage()
        id_ = add_node(s, i=1)
        
        with self.assertRaises(PayloadDoesNotExistError):
            s.get_node_payload(id_, 'payload_name') 

    def test_get_node_payload_nonexistent_node(self):
        s = self.create_notebook_storage()
        with self.assertRaises(NodeDoesNotExistError):
            s.get_node_payload('node_id', 'payload_name') 

    def test_has_node_payload(self):
        s = self.create_notebook_storage()
        id_ = add_node(s, i=1)
        
        # Make sure the payload is not there.
        self.assertFalse(s.has_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME))
        
        with io.open(DEFAULT_HTML_PAYLOAD_PATH, mode='rb') as f:
            s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, f)
        
        # Then make sure it is there.
        s = self.create_notebook_storage()
        self.assertTrue(s.has_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME))

    def test_add_node_with_payloads(self):
        # Add node and payload first.
        s = self.create_notebook_storage()
        with io.open(DEFAULT_HTML_PAYLOAD_PATH, mode='rb') as f1:
            with io.open(DEFAULT_PNG_PAYLOAD_PATH, mode='rb') as f2:
                id_ = add_node(s, payloads=[(DEFAULT_HTML_PAYLOAD_NAME, f1), (DEFAULT_PNG_PAYLOAD_NAME, f2)], payload_paths=[])
        
        # Then read them.
        s = self.create_notebook_storage()
        self.assertEqual(create_stored_node(payload_names=[DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_NAME]), s.get_node(id_))
        with io.open(DEFAULT_HTML_PAYLOAD_PATH, mode='rb') as f1:
            with s.get_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME) as f2:
                assert_file_object_equals(self, f1, f2)
        with io.open(DEFAULT_PNG_PAYLOAD_PATH, mode='rb') as f1:
            with s.get_node_payload(id_, DEFAULT_PNG_PAYLOAD_NAME) as f2:
                assert_file_object_equals(self, f1, f2)
        
    def test_remove_node_payload(self):
        s = self.create_notebook_storage()
        id_ = add_node(s, i=1)
        
        # Add payload first.
        with io.open(DEFAULT_HTML_PAYLOAD_PATH, mode='rb') as f:
            s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, f)
 
        # Then make sure it is there.
        s = self.create_notebook_storage()
        self.assertTrue(s.has_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME))
   
        # Then remove it.
        s = self.create_notebook_storage()
        s.remove_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME)
   
        # Then make sure it is not there.
        s = self.create_notebook_storage()
        self.assertFalse(s.has_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME))

    def test_remove_node_payload_nonexistent(self):
        s = self.create_notebook_storage()
        id_ = add_node(s, i=1)
        
        with self.assertRaises(PayloadDoesNotExistError):
            s.remove_node_payload(id_, 'payload_name') 

    def test_remove_node_payload_nonexistent_node(self):
        s = self.create_notebook_storage()
        with self.assertRaises(NodeDoesNotExistError):
            s.remove_node_payload('node_id', 'payload_name')
    
    def test_set_node_attributes(self):
        attributes1={ 'title': 'title 1', 'version_1': 'This is only there in the first version.'}
        attributes2={ 'title': 'title 2', 'version_2': 'This is only there in the second version.'}
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s, attributes=attributes1)

        # Verify the attributes.
        s = self.create_notebook_storage()
        stored_node1=s.get_node(id_)
        self.assertEquals(attributes1, stored_node1.attributes)

        # Update the attributes.
        s = self.create_notebook_storage()
        s.set_node_attributes(node_id=id_, attributes=attributes2)

        # Then make sure it is not there.
        s = self.create_notebook_storage()
        stored_node2=s.get_node(id_)
        self.assertEquals(attributes2, stored_node2.attributes)
    
    def test_set_node_attributes_nonexistent_node(self):
        s = self.create_notebook_storage()
        with self.assertRaises(NodeDoesNotExistError):
            s.set_node_attributes('node_id', {})
    
    def test_get_notebook(self):
        s = self.create_notebook_storage()
        self.assertEqual(create_stored_notebook(attributes={}), s.get_notebook())
    
    def test_set_notebook_attributes(self):
        # Set the attributes first.
        s = self.create_notebook_storage()
        s.set_notebook_attributes(attributes=DEFAULT_ATTRIBUTES)

        # Then read them.
        s = self.create_notebook_storage()
        self.assertEqual(create_stored_notebook(), s.get_notebook())


# Utility functions

def add_node(
        notebook_storage,
        i=None,
        node_id=DEFAULT_ID,
        content_type=CONTENT_TYPE_HTML,
        attributes=DEFAULT_ATTRIBUTES,
        payloads=None,
        payload_paths=None,
        ):
    # We cannot use lists as default values in the function definition.
    if payloads is None:
        payloads = []
    if payload_paths is None:
        payload_paths = []
    
    if i is not None:
        node_id = node_id % i
    
    opened_files = []
    for payload_path in payload_paths:
        payload_name = os.path.basename(payload_path)
        opened_file = io.open(payload_path, mode='rb')
        payloads.append((payload_name, opened_file))
        opened_files.append(opened_file)
    
    notebook_storage.add_node(node_id, content_type, attributes, payloads)
    
    for opened_file in opened_files:
        opened_file.close()
    
    return node_id

def create_stored_notebook(
        attributes=DEFAULT_ATTRIBUTES,
        ):
    
    return StoredNotebook(attributes)

def create_stored_node(
        i=None,
        node_id=DEFAULT_ID,
        content_type=CONTENT_TYPE_HTML,
        attributes=DEFAULT_ATTRIBUTES,
        payload_names=None
        ):
    
    if i is not None:
        node_id = node_id % i
    if payload_names is None:
        payload_names = []
        
    return StoredNode(node_id, content_type, attributes, payload_names)

# -*- coding: utf-8 -*-

from __future__ import absolute_import
import base64
import hashlib
import io
import os
import unittest

from keepnote.notebooknew.storage import *

DEFAULT_ID = 'my_id_%s'
DEFAULT_TITLE = 'my_title'
DEFAULT_ATTRIBUTES = { 'title': DEFAULT_TITLE, 'key2': 'value2' }
CONTENT_TYPE_HTML = 'text/html'
DEFAULT_HTML_PAYLOAD_NAME = 'index.html'
DEFAULT_HTML_PAYLOAD_DATA = base64.b64decode('PCFET0NUWVBFIGh0bWw+DQoNCjxoMT5UZXN0IE5vZGU8L2gxPg0KPHA+VGhpcyBpcyBhIG5vZGUgdXNlZCBmb3IgdGVzdGluZy48L3A+DQo=')
DEFAULT_HTML_PAYLOAD_HASH = hashlib.md5(DEFAULT_HTML_PAYLOAD_DATA).hexdigest()
DEFAULT_PNG_PAYLOAD_NAME = 'image1.png'
DEFAULT_PNG_PAYLOAD_DATA = base64.b64decode('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')
DEFAULT_PNG_PAYLOAD_HASH = hashlib.md5(DEFAULT_PNG_PAYLOAD_DATA).hexdigest()
DEFAULT_JPG_PAYLOAD_NAME = 'image2.jpg'
DEFAULT_JPG_PAYLOAD_DATA = base64.b64decode('/9j/4AAQSkZJRgABAQEAYwBjAAD/4QBmRXhpZgAATU0AKgAAAAgABAEaAAUAAAABAAAAPgEbAAUAAAABAAAARgEoAAMAAAABAAMAAAExAAIAAAAQAAAATgAAAAAAAJhXAAAD6AAAmFcAAAPocGFpbnQubmV0IDQuMC41AP/bAEMAAgEBAgEBAgICAgICAgIDBQMDAwMDBgQEAwUHBgcHBwYHBwgJCwkICAoIBwcKDQoKCwwMDAwHCQ4PDQwOCwwMDP/bAEMBAgICAwMDBgMDBgwIBwgMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDP/AABEIABcAIAMBIgACEQEDEQH/xAAfAAABBQEBAQEBAQAAAAAAAAAAAQIDBAUGBwgJCgv/xAC1EAACAQMDAgQDBQUEBAAAAX0BAgMABBEFEiExQQYTUWEHInEUMoGRoQgjQrHBFVLR8CQzYnKCCQoWFxgZGiUmJygpKjQ1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4eLj5OXm5+jp6vHy8/T19vf4+fr/xAAfAQADAQEBAQEBAQEBAAAAAAAAAQIDBAUGBwgJCgv/xAC1EQACAQIEBAMEBwUEBAABAncAAQIDEQQFITEGEkFRB2FxEyIygQgUQpGhscEJIzNS8BVictEKFiQ04SXxFxgZGiYnKCkqNTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqCg4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2dri4+Tl5ufo6ery8/T19vf4+fr/2gAMAwEAAhEDEQA/APvzRNBs9S1NZJIGVMFSVzhWHC54HHBP41X0ya18T3McdosjszbREwwyg4ALbh29TgY71kfF/wCOujfDrwLfWuktJq3iiZJobHSrd/8ASLm4GNysoOVUdSzEKAQxO35q0/2bnjufhzo8kNnaabcyWRge3RgDE0YEbdBhsFTz3znPNfMYTEww04whaUtW9P6/I9DEYOdeg6s7xWiWv5rr9+5k/GO90L4R+G0i164SzuLq9gtxc+YFSPdPGPlcgqODnJGcBiOlaHhe9h8XeFo7m223drlltZ4G3m5RGKbmPHzZU52ggnPHavGP2uvib4fuNX1Dw/8A8Jhpmm+KdJsIb+ysJLFp11Nl3ypEJtp8v7ueBjD85Aq78Lv2idK1T4hxx2GnWeiNfMbS4ja5MgmUSSbGChF5OMqTg4J964q2c1vrHtWlZ6XW/wA/6R308jh9U5Lu61s9vl/TPP8A4M/ALxT4b8Mx3nie+GveMNRYzPO1/JF9gCoqIvmqCzsfn3nkECNVwqAV3ds+teBJpdQ0G4vtXvpw9mYrjUZPnVzkjc/CjKknHJPQ0UV8ZGtL2j+f6H0tSvJxV9n06Hj3xA/ZDvPiD4xt9X1fbbzSxKJE+1NOGcEgABidi42ggM3O4gjOKz4vggP2c70Xkr+JNc3N9osjFcofskygoobzJ0J3Bzkj+6OnOSis8POUua52VMXUfLB7H//Z')
DEFAULT_JPG_PAYLOAD_HASH = hashlib.md5(DEFAULT_JPG_PAYLOAD_DATA).hexdigest()

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
        node = StoredNode('id', 'text/html', { 'key': 'value' }, [StoredNodePayload('name', 'hash')])

        self.assertEqual('id', node.node_id)
        self.assertEqual('text/html', node.content_type)
        self.assertEqual({ 'key': 'value' }, node.attributes)
        self.assertEqual([StoredNodePayload('name', 'hash')], node.payloads)

    def test_equals(self):
        node1 = create_stored_node([StoredNodePayload('name', 'hash')])
        node1a = create_stored_node([StoredNodePayload('name', 'hash')])

        self.assertTrue(node1 == node1a)
        self.assertFalse(node1 != node1a)

        node2 = create_stored_node(node_id=None)
        node3 = create_stored_node(content_type=None)
        node4 = create_stored_node(attributes=None)
        node5 = create_stored_node(payloads=None)

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
        self.assertEqual(create_stored_node(i=1, payloads=[]), s.get_node(id1))
        self.assertEqual(create_stored_node(i=2, payloads=[]), s.get_node(id2))
 
    def test_add_node_twice(self):
        s = self.create_notebook_storage()
        add_node(s, i=1)
        with self.assertRaises(NodeAlreadyExistsError):
            add_node(s, i=1)

    def test_add_node_character_encoding_and_escaping(self):
        # Add node first.
        s = self.create_notebook_storage()
        payload_data = u'<äëïöüß€&ש> </text>'
        id_ = add_node(
                s,
                content_type=u'<äëïöüß€&ש>',
                attributes={ u'<äëïöüß€&ש>': u'<äëïöüß€&ש>' },
                payloads=[(u'äëïöüß€ש', io.BytesIO(payload_data.encode('utf-8')))],
                payload_paths=[]
                )
 
        # Then read it.
        s = self.create_notebook_storage()
        expected = StoredNode(
                node_id=id_,
                content_type=u'<äëïöüß€&ש>',
                attributes={ u'<äëïöüß€&ש>': u'<äëïöüß€&ש>' },
                payloads=[StoredNodePayload(u'äëïöüß€ש', hashlib.md5(payload_data.encode('utf-8')).hexdigest())]
                )
        actual = s.get_node(id_)
        self.assertEqual(expected, actual)
 
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
        self.assertEqual([create_stored_node(i=1), create_stored_node(i=2)], list(s.get_all_nodes()))

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
        s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))
        
        # Then read the node and payload.
        s = self.create_notebook_storage()
        self.assertEqual([StoredNodePayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_HASH)], s.get_node(id_).payloads)
        self.assertEqual(s.get_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME).read(), DEFAULT_HTML_PAYLOAD_DATA)
    
    def test_add_node_payload_twice(self):
        s = self.create_notebook_storage()
        id_ = add_node(s, i=1)

        s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))
        
        with self.assertRaises(PayloadAlreadyExistsError):
            s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))
    
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
        
        s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))
        
        # Then make sure it is there.
        s = self.create_notebook_storage()
        self.assertTrue(s.has_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME))

    def test_add_node_with_payloads(self):
        # Add node and payload first.
        s = self.create_notebook_storage()
        id_ = add_node(s, payloads=[
                (DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA)),
                (DEFAULT_PNG_PAYLOAD_NAME, io.BytesIO(DEFAULT_PNG_PAYLOAD_DATA))
            ], payload_paths=[])
        
        # Then read them.
        s = self.create_notebook_storage()
        self.assertEqual([
                StoredNodePayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_HASH),
                StoredNodePayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_HASH),
                ], s.get_node(id_).payloads)
        self.assertEqual(s.get_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME).read(), DEFAULT_HTML_PAYLOAD_DATA)
        self.assertEqual(s.get_node_payload(id_, DEFAULT_PNG_PAYLOAD_NAME).read(), DEFAULT_PNG_PAYLOAD_DATA)
        
    def test_remove_node_payload(self):
        s = self.create_notebook_storage()
        id_ = add_node(s, i=1)
        
        # Add payload first.
        s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))
 
        # Then make sure it is there.
        s = self.create_notebook_storage()
        self.assertTrue(s.has_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME))
   
        # Then remove it.
        s = self.create_notebook_storage()
        s.remove_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME)
   
        # Then make sure it is not there.
        s = self.create_notebook_storage()
        self.assertFalse(s.has_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME))

    def test_remove_and_add_node_payload(self):
        s = self.create_notebook_storage()
        id_ = add_node(s, i=1)
        
        # Add and remove payload first.
        s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))
        s.remove_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME)
   
        # Then add it again.
        s.add_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))
        
        # Then make sure it is there.
        self.assertTrue(s.has_node_payload(id_, DEFAULT_HTML_PAYLOAD_NAME))
        self.assertEqual(1, len(s.get_node(id_).payloads))
    
    def test_remove_node_payload_nonexistent(self):
        s = self.create_notebook_storage()
        id_ = add_node(s, i=1)
        
        with self.assertRaises(PayloadDoesNotExistError):
            s.remove_node_payload(id_, 'payload_name') 

    def test_remove_node_payload_nonexistent_node(self):
        s = self.create_notebook_storage()
        with self.assertRaises(NodeDoesNotExistError):
            s.remove_node_payload('node_id', 'payload_name')
    
    def test_get_all_nodes_with_payload(self):
        # Add nodes first.
        s = self.create_notebook_storage()
        id1 = add_node(s, i=1, payloads=[
                (DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA)),
            ], payload_paths=[])
        id2 = add_node(s, i=2, payloads=[
                (DEFAULT_PNG_PAYLOAD_NAME, io.BytesIO(DEFAULT_PNG_PAYLOAD_DATA)),
            ], payload_paths=[])
 
        # Then read them.
        s = self.create_notebook_storage()
        self.assertEqual([
                create_stored_node(i=1, payloads=[StoredNodePayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_HASH)]),
                create_stored_node(i=2, payloads=[StoredNodePayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_HASH)]),
                ],
                list(s.get_all_nodes()))
    
    def test_set_node_attributes(self):
        attributes1 = { 'title': 'title 1', 'version_1': 'This is only there in the first version.' }
        attributes2 = { 'title': 'title 2', 'version_2': 'This is only there in the second version.' }
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s, attributes=attributes1)

        # Verify the attributes.
        s = self.create_notebook_storage()
        stored_node1=s.get_node(id_)
        self.assertEqual(attributes1, stored_node1.attributes)

        # Update the attributes.
        s = self.create_notebook_storage()
        s.set_node_attributes(node_id=id_, attributes=attributes2)

        # Then make sure it is not there.
        s = self.create_notebook_storage()
        stored_node2=s.get_node(id_)
        self.assertEqual(attributes2, stored_node2.attributes)
    
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
        self.assertEqual(DEFAULT_ATTRIBUTES, s.get_notebook().attributes)
    
    def test_set_notebook_attributes_copied(self):
        attributes = { 'key': 'value' }
        
        # Set the attributes first.
        s = self.create_notebook_storage()
        s.set_notebook_attributes(attributes=attributes)
        
        # Change the local attributes object.
        attributes['key'] = 'new value'

        # Then read them.
        self.assertEqual('value', s.get_notebook().attributes['key'])
    
    def test_attributes_copied_add_node(self):
        attributes = { 'key': 'value' }
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s, attributes=attributes, payloads=[], payload_paths=[])
        
        # Change the local attributes object.
        attributes['key'] = 'new value'

        # Then read the attributes.
        self.assertEqual('value', s.get_node(id_).attributes['key'])
    
    def test_attributes_copied_set_node_attributes(self):
        attributes = { 'key': 'value' }
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s)
        s.set_node_attributes(id_, attributes)

        # Change the local attributes object.
        attributes['key'] = 'new value'
        
        # Then read the attributes.
        self.assertEqual('value', s.get_node(id_).attributes['key'])
    
    def test_attribute_type_int_add_node(self):
        value = 1
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s, attributes={ 'key': value }, payloads=[], payload_paths=[])
        
        # Then read the attribute.
        s = self.create_notebook_storage()
        self.assertEqual(value, s.get_node(id_).attributes['key'])
    
    def test_attribute_type_int_set_node_attributes(self):
        value = 1
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s)
        
        # Then set the attribute.
        s.set_node_attributes(id_, attributes={ 'key': value })

        # Then read the attribute.
        s = self.create_notebook_storage()
        self.assertEqual(value, s.get_node(id_).attributes['key'])
    
    def test_attribute_type_float_add_node(self):
        value = float(1.0)
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s, attributes={ 'key': value }, payloads=[], payload_paths=[])
        
        # Then read the attribute.
        s = self.create_notebook_storage()
        self.assertEqual(value, s.get_node(id_).attributes['key'])
    
    def test_attribute_type_float_set_node_attributes(self):
        value = float(1.0)
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s)
        
        # Then set the attribute.
        s.set_node_attributes(id_, attributes={ 'key': value })

        # Then read the attribute.
        s = self.create_notebook_storage()
        self.assertEqual(value, s.get_node(id_).attributes['key'])
    
    def test_attribute_type_dict_add_node(self):
        value = { 'subkey_string': 'value', 'subkey_int': 1, 'subkey_float': float(1.0), 'subkey_list': [], 'subkey_dict': {} }
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s, attributes={ 'key': value }, payloads=[], payload_paths=[])
        
        # Then read the attribute.
        s = self.create_notebook_storage()
        self.assertEqual(value, s.get_node(id_).attributes['key'])
    
    def test_attribute_type_dict_set_node_attributes(self):
        value = { 'subkey_string': 'value', 'subkey_int': 1, 'subkey_float': float(1.0), 'subkey_list': [], 'subkey_dict': {} }
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s)
        
        # Then set the attribute.
        s.set_node_attributes(id_, attributes={ 'key': value })

        # Then read the attribute.
        s = self.create_notebook_storage()
        self.assertEqual(value, s.get_node(id_).attributes['key'])
    
    def test_attribute_type_list_add_node(self):
        value = [ 'value', 1, float(1.0), {}, [] ]
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s, attributes={ 'key': value }, payloads=[], payload_paths=[])
        
        # Then read the attribute.
        s = self.create_notebook_storage()
        self.assertEqual(value, s.get_node(id_).attributes['key'])
    
    def test_attribute_type_list_set_node_attributes(self):
        value = [ 'value', 1, float(1.0), {}, [] ]
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s)
        
        # Then set the attribute.
        s.set_node_attributes(id_, attributes={ 'key': value })

        # Then read the attribute.
        s = self.create_notebook_storage()
        self.assertEqual(value, s.get_node(id_).attributes['key'])
    
    def test_attribute_type_none_add_node(self):
        value = None
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s, attributes={ 'key': value }, payloads=[], payload_paths=[])
        
        # Then read the attribute.
        s = self.create_notebook_storage()
        self.assertEqual(value, s.get_node(id_).attributes['key'])
    
    def test_attribute_type_none_set_node_attributes(self):
        value = None
        
        # Add node first.
        s = self.create_notebook_storage()
        id_ = add_node(s)
        
        # Then set the attribute.
        s.set_node_attributes(id_, attributes={ 'key': value })

        # Then read the attribute.
        s = self.create_notebook_storage()
        self.assertEqual(value, s.get_node(id_).attributes['key'])


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
    
    try:
        notebook_storage.add_node(node_id, content_type, attributes, payloads)
    finally:
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
        payloads=None
        ):
    
    if i is not None:
        node_id = node_id % i
    if payloads is None:
        payloads = []
        
    return StoredNode(node_id, content_type, attributes, payloads)

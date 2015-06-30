# -*- coding: utf-8 -*-

import base64
import copy
import io
import mock
from mock import Mock
import re
import unittest

from keepnote.notebooknew import *
import keepnote.notebooknew.storage as storage
import keepnote.notebooknew.storage.mem

DEFAULT_ID = 'my_id'
DEFAULT_CONTENT_TYPE = CONTENT_TYPE_HTML
DEFAULT_TITLE = 'my_title'
DEFAULT_PAYLOAD_NAMES = ['my_payload1', 'my_payload2']
DEFAULT_HTML_PAYLOAD_NAME = os.path.basename('index.html')
DEFAULT_HTML_PAYLOAD = base64.b64decode('PCFET0NUWVBFIGh0bWw+DQoNCjxoMT5UZXN0IE5vZGU8L2gxPg0KPHA+VGhpcyBpcyBhIG5vZGUgdXNlZCBmb3IgdGVzdGluZy48L3A+DQo=')
DEFAULT_PNG_PAYLOAD_NAME = os.path.basename('image1.png')
DEFAULT_PNG_PAYLOAD = base64.b64decode('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')
DEFAULT_JPG_PAYLOAD_NAME = os.path.basename('image2.jpg')
DEFAULT_JPG_PAYLOAD = base64.b64decode('/9j/4AAQSkZJRgABAQEAYwBjAAD/4QBmRXhpZgAATU0AKgAAAAgABAEaAAUAAAABAAAAPgEbAAUAAAABAAAARgEoAAMAAAABAAMAAAExAAIAAAAQAAAATgAAAAAAAJhXAAAD6AAAmFcAAAPocGFpbnQubmV0IDQuMC41AP/bAEMAAgEBAgEBAgICAgICAgIDBQMDAwMDBgQEAwUHBgcHBwYHBwgJCwkICAoIBwcKDQoKCwwMDAwHCQ4PDQwOCwwMDP/bAEMBAgICAwMDBgMDBgwIBwgMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDP/AABEIABcAIAMBIgACEQEDEQH/xAAfAAABBQEBAQEBAQAAAAAAAAAAAQIDBAUGBwgJCgv/xAC1EAACAQMDAgQDBQUEBAAAAX0BAgMABBEFEiExQQYTUWEHInEUMoGRoQgjQrHBFVLR8CQzYnKCCQoWFxgZGiUmJygpKjQ1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4eLj5OXm5+jp6vHy8/T19vf4+fr/xAAfAQADAQEBAQEBAQEBAAAAAAAAAQIDBAUGBwgJCgv/xAC1EQACAQIEBAMEBwUEBAABAncAAQIDEQQFITEGEkFRB2FxEyIygQgUQpGhscEJIzNS8BVictEKFiQ04SXxFxgZGiYnKCkqNTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqCg4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2dri4+Tl5ufo6ery8/T19vf4+fr/2gAMAwEAAhEDEQA/APvzRNBs9S1NZJIGVMFSVzhWHC54HHBP41X0ya18T3McdosjszbREwwyg4ALbh29TgY71kfF/wCOujfDrwLfWuktJq3iiZJobHSrd/8ASLm4GNysoOVUdSzEKAQxO35q0/2bnjufhzo8kNnaabcyWRge3RgDE0YEbdBhsFTz3znPNfMYTEww04whaUtW9P6/I9DEYOdeg6s7xWiWv5rr9+5k/GO90L4R+G0i164SzuLq9gtxc+YFSPdPGPlcgqODnJGcBiOlaHhe9h8XeFo7m223drlltZ4G3m5RGKbmPHzZU52ggnPHavGP2uvib4fuNX1Dw/8A8Jhpmm+KdJsIb+ysJLFp11Nl3ypEJtp8v7ueBjD85Aq78Lv2idK1T4hxx2GnWeiNfMbS4ja5MgmUSSbGChF5OMqTg4J964q2c1vrHtWlZ6XW/wA/6R308jh9U5Lu61s9vl/TPP8A4M/ALxT4b8Mx3nie+GveMNRYzPO1/JF9gCoqIvmqCzsfn3nkECNVwqAV3ds+teBJpdQ0G4vtXvpw9mYrjUZPnVzkjc/CjKknHJPQ0UV8ZGtL2j+f6H0tSvJxV9n06Hj3xA/ZDvPiD4xt9X1fbbzSxKJE+1NOGcEgABidi42ggM3O4gjOKz4vggP2c70Xkr+JNc3N9osjFcofskygoobzJ0J3Bzkj+6OnOSis8POUua52VMXUfLB7H//Z')

# The following StoredNodes and NotebookNodes have the following structure:
# root
#   child1
#     child11
#     child12
#       child121
#   child2
#     child21
ROOT_SN = StoredNode('root_id', CONTENT_TYPE_FOLDER, attributes={TITLE_ATTRIBUTE: 'root'}, payload_names=[])
CHILD1_SN = StoredNode('child1_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child1'}, payload_names=[])
CHILD11_SN = StoredNode('child11_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child11'}, payload_names=[])
CHILD12_SN = StoredNode('child12_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child12'}, payload_names=[])
CHILD121_SN = StoredNode('child121_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child12_id', TITLE_ATTRIBUTE: 'child121'}, payload_names=[])
CHILD2_SN = StoredNode('child2_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child2'}, payload_names=[])
CHILD21_SN = StoredNode('child21_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child2_id', TITLE_ATTRIBUTE: 'child21'}, payload_names=[])


class NotebookTest(unittest.TestCase):
	def test_load_notebook(self):
		"""Test loading a notebook."""
		
		# Initialize a NotebookStorage.
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the Notebook.
		self.assertEquals(False, notebook.is_dirty)
	
	def test_load_content_node(self):
		"""Test loading a content node."""
		# Initialize a NotebookStorage.
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				attributes={
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						MAIN_PAYLOAD_NAME_ATTRIBUTE: DEFAULT_HTML_PAYLOAD_NAME,
						},
				payloads=[(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD)), (DEFAULT_PNG_PAYLOAD_NAME, io.BytesIO(DEFAULT_PNG_PAYLOAD))]
				)
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		node = notebook.root
		self.assertEquals(ContentNode, node.__class__)
		self.assertEquals(DEFAULT_ID, node.node_id)
		self.assertEquals(CONTENT_TYPE_HTML, node.content_type)
		self.assertEquals(DEFAULT_TITLE, node.title)
		self.assertEquals(DEFAULT_HTML_PAYLOAD_NAME, node.main_payload_name)
		self.assertEquals([DEFAULT_PNG_PAYLOAD_NAME], node.additional_payload_names)
		self.assertEquals(False, node.is_dirty)
	
	def test_load_content_node_missing_title(self):
		"""Test loading a content node without a title."""
		
		# Initialize a NotebookStorage.
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						MAIN_PAYLOAD_NAME_ATTRIBUTE: DEFAULT_HTML_PAYLOAD_NAME,
						},
				payloads=[(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD))]
				)
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		node = notebook.root.children[0]
		self.assertEquals('', node.title)
	
	def test_load_folder_node(self):
		"""Test loading a folder node."""
		
		# Initialize a NotebookStorage.
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_FOLDER,
				attributes={
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						},
				payloads=[]
				)
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		node = notebook.root
		self.assertEquals(FolderNode, node.__class__)
		self.assertEquals(DEFAULT_ID, node.node_id)
		self.assertEquals(CONTENT_TYPE_FOLDER, node.content_type)
		self.assertEquals(DEFAULT_TITLE, node.title)
		self.assertEquals(False, node.is_dirty)
	
	def test_load_folder_node_missing_title(self):
		"""Test loading a folder node without a title."""
		
		# Initialize a NotebookStorage.
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_FOLDER,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						},
				payloads=[]
				)
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		node = notebook.root.children[0]
		self.assertEquals('', node.title)	
	
	def test_load_trash_node(self):
		"""Test loading a trash node."""
		
		# Initialize a NotebookStorage.
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_TRASH,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						},
				payloads=[]
				)
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		node = notebook.trash
		self.assertEquals(notebook.root.children[0], node)
		self.assertEquals(TrashNode, node.__class__)
		self.assertEquals(DEFAULT_ID, node.node_id)
		self.assertEquals(CONTENT_TYPE_TRASH, node.content_type)
		self.assertEquals(DEFAULT_TITLE, node.title)
		self.assertEquals(False, node.is_dirty)
	
	def test_structure_only_root(self):
		"""Test the NotebookNode structure with a just a root."""
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify notebook.root.
		self.assertEqual(ROOT_SN.node_id, notebook.root.node_id)
		self.assertEqual(None, notebook.root.parent)
		self.assertEqual([], notebook.root.children)
		
	def test_structure_two_levels(self):
		"""Test the NotebookNode structure with a root and direct children."""
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, CHILD1_SN, CHILD2_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the structure.
		child1 = notebook.root.children[0]
		child2 = notebook.root.children[1]
		self.assertEqual((CHILD1_SN.node_id, notebook.root, []), (child1.node_id, child1.parent, [node.node_id for node in child1.children]))
		self.assertEqual((CHILD2_SN.node_id, notebook.root, []), (child2.node_id, child2.parent, [node.node_id for node in child2.children]))
		
	def test_structure_multiple_levels(self):
		"""Test the NotebookNode structure with multiple levels of nodes."""
		self.maxDiff=None
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, CHILD1_SN, CHILD11_SN, CHILD12_SN, CHILD121_SN, CHILD2_SN, CHILD21_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		child1 = notebook.root.children[0]
		child11 = notebook.root.children[0].children[0]
		child12 = notebook.root.children[0].children[1]
		child121 = notebook.root.children[0].children[1].children[0]
		child2 = notebook.root.children[1]
		child21 = notebook.root.children[1].children[0]

		# Verify the ID's.
		self.assertEqual(CHILD1_SN.node_id, child1.node_id)
		self.assertEqual(CHILD11_SN.node_id, child11.node_id)
		self.assertEqual(CHILD12_SN.node_id, child12.node_id)
		self.assertEqual(CHILD121_SN.node_id, child121.node_id)
		self.assertEqual(CHILD2_SN.node_id, child2.node_id)
		self.assertEqual(CHILD21_SN.node_id, child21.node_id)
		
		# Verify the children. 
		self.assertEqual([CHILD11_SN.node_id, CHILD12_SN.node_id], [node.node_id for node in child1.children])
		self.assertEqual([], [node.node_id for node in child11.children])
		self.assertEqual([CHILD121_SN.node_id], [node.node_id for node in child12.children])
		self.assertEqual([CHILD21_SN.node_id], [node.node_id for node in child2.children])
		self.assertEqual([], [node.node_id for node in child21.children])
		
		# Verify the parents. 
		self.assertEqual(notebook.root, child1.parent)
		self.assertEqual(child1, child11.parent)
		self.assertEqual(child1, child12.parent)
		self.assertEqual(child12, child121.parent)
		self.assertEqual(notebook.root, child2.parent)
		self.assertEqual(child2, child21.parent)
		
	def test_structure_stored_nodes_postordered(self):
		"""Test the NotebookNode structure with multiple levels of nodes, if the backing NotebookStorage.get_all_nodes()
		returns the StoredNotes in another order. In this case, the order achieved when traversing the tree depth-first
		left-to-right post-order."""
		self.maxDiff=None
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [CHILD11_SN, CHILD121_SN, CHILD12_SN, CHILD1_SN, CHILD21_SN, CHILD2_SN, ROOT_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		child1 = notebook.root.children[0]
		child11 = notebook.root.children[0].children[0]
		child12 = notebook.root.children[0].children[1]
		child121 = notebook.root.children[0].children[1].children[0]
		child2 = notebook.root.children[1]
		child21 = notebook.root.children[1].children[0]

		# Verify the ID's.
		self.assertEqual(CHILD1_SN.node_id, child1.node_id)
		self.assertEqual(CHILD11_SN.node_id, child11.node_id)
		self.assertEqual(CHILD12_SN.node_id, child12.node_id)
		self.assertEqual(CHILD121_SN.node_id, child121.node_id)
		self.assertEqual(CHILD2_SN.node_id, child2.node_id)
		self.assertEqual(CHILD21_SN.node_id, child21.node_id)
		
		# Verify the children. 
		self.assertEqual([CHILD11_SN.node_id, CHILD12_SN.node_id], [node.node_id for node in child1.children])
		self.assertEqual([], [node.node_id for node in child11.children])
		self.assertEqual([CHILD121_SN.node_id], [node.node_id for node in child12.children])
		self.assertEqual([CHILD21_SN.node_id], [node.node_id for node in child2.children])
		self.assertEqual([], [node.node_id for node in child21.children])
		
		# Verify the parents. 
		self.assertEqual(notebook.root, child1.parent)
		self.assertEqual(child1, child11.parent)
		self.assertEqual(child1, child12.parent)
		self.assertEqual(child12, child121.parent)
		self.assertEqual(notebook.root, child2.parent)
		self.assertEqual(child2, child21.parent)
		
	def test_validation_two_roots(self):
		"""Test a NotebookStorage with two roots."""
		root1_sn = StoredNode('root1_id', CONTENT_TYPE_FOLDER, attributes={}, payload_names=[])
		root2_sn = StoredNode('root2_id', CONTENT_TYPE_FOLDER, attributes={}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [root1_sn, root2_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_validation_unknown_parent(self):
		"""Test a NotebookStorage with a root and a node that references an unknown parent."""
		child_sn = StoredNode('child_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'unknown_id'}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, child_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_validation_parent_is_child(self):
		"""Test a NotebookStorage with a root and a node that is its own parent."""
		child_sn = StoredNode('child_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child_id'}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, child_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_validation_cycle_no_root(self):
		"""Test a NotebookStorage with a cycle and no root."""
		cycle_node1_sn = StoredNode('cycle_node1_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node2_id'}, payload_names=[])
		cycle_node2_sn = StoredNode('cycle_node2_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node1_id'}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [cycle_node1_sn, cycle_node2_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_validation_cycle_with_root(self):
		"""Test a NotebookStorage with a root and a cycle."""
		cycle_node1_sn = StoredNode('cycle_node1_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node3_id'}, payload_names=[])
		cycle_node2_sn = StoredNode('cycle_node2_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node1_id'}, payload_names=[])
		cycle_node3_sn = StoredNode('cycle_node3_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node2_id'}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, CHILD1_SN, cycle_node1_sn, cycle_node2_sn, cycle_node3_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	# TODO: Is this really necessary?
	def test_validation_trash_not_child_of_root(self):
		"""Test a NotebookStorage with a trash that is not a child of the root node."""
		trash_sn = StoredNode('trash_id', CONTENT_TYPE_TRASH, attributes={PARENT_ID_ATTRIBUTE: CHILD1_SN.node_id}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, CHILD1_SN, trash_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_validation_two_trashes(self):
		"""Test a NotebookStorage with two trashes."""
		trash1_sn = StoredNode('trash1_id', CONTENT_TYPE_TRASH, attributes={}, payload_names=[])
		trash2_sn = StoredNode('trash2_id', CONTENT_TYPE_TRASH, attributes={}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, trash1_sn, trash2_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_root_created_in_empty_storage(self):
		"""Test if a root is created in an empty NotebookStorage."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify notebook_storage.add_node().
		notebook_storage.add_node.assert_any_call(node_id=mock.ANY, content_type=CONTENT_TYPE_FOLDER, attributes={}, payloads=[])
		
		# Verify the node.
		node = notebook.root
		self.assertEquals(CONTENT_TYPE_FOLDER, node.content_type)
		# TODO: Title?
	
	def test_trash_created_if_missing(self):
		"""Test if a trash is created in a NotebookStorage without one."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify notebook_storage.add_node().
		notebook_storage.add_node.assert_any_call(node_id=mock.ANY, content_type=CONTENT_TYPE_TRASH, attributes={PARENT_ID_ATTRIBUTE: ROOT_SN.node_id}, payloads=[])
		
		# Verify the node.
		node = notebook.trash
		self.assertEquals(CONTENT_TYPE_TRASH, node.content_type)
		# TODO: Title?
		
	def test_client_preferences(self):
		"""Test the setting and getting of Notebook client preferences."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		expected = Pref()
		self.assertEquals(expected, notebook.client_preferences)
		
		notebook.client_preferences.get('test', 'key', define=True)
		notebook.client_preferences.set('test', 'key', 'value')
		
		expected = Pref()
		expected.get('test', 'key', define=True)
		expected.set('test', 'key', 'value')
		self.assertEquals(expected, notebook.client_preferences)
			
class ContentFolderNodeTestBase(object):
	def _create_node(self, parent=None, is_dirty=True):
		raise NotImplementedError()
	
	def test_is_root_1(self):
		node = self._create_node(parent=None, is_dirty=False)
		self.assertEquals(True, node.is_root)
	
	def test_is_root_2(self):
		parent = Mock(spec=NotebookNode)
		node = self._create_node(parent=parent, is_dirty=False)
		self.assertEquals(False, node.is_root)
	
	def test_is_trash(self):
		node = self._create_node(parent=None, is_dirty=False)
		self.assertEquals(False, node.is_trash)
		
	def test_is_in_trash_1(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = False
		
		node = self._create_node(parent=parent, is_dirty=False)
		
		self.assertEquals(False, node.is_in_trash)
	
	def test_is_in_trash_2(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = True
		parent.is_in_trash = False
		
		node = self._create_node(parent=parent, is_dirty=False)
		self.assertEquals(True, node.is_in_trash)
	
	def test_is_in_trash_3(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = True
		
		node = self._create_node(parent=parent, is_dirty=False)
		
		self.assertEquals(True, node.is_in_trash)
	
	def test_is_in_trash_4(self):
		node = self._create_node(parent=None, is_dirty=False)
		
		self.assertEquals(False, node.is_in_trash)
	
	def test_delete_without_children(self):
		parent = Mock(spec=NotebookNode)
		parent.parent = None
		node = self._create_node(parent=parent, is_dirty=False)
		parent.children = [node]
		
		self.assertEquals(False, node.is_dirty)
		self.assertEquals(False, node.is_deleted_unsaved)
		node.delete()
		self.assertEquals(True, node.is_dirty)
		self.assertEquals(True, node.is_deleted_unsaved)
		self.assertEquals(False, node in parent.children)
	
	def test_delete_with_children(self):
		parent = Mock(spec=NotebookNode)
		parent.parent = None
		child1 = Mock(spec=NotebookNode)
		child2 = Mock(spec=NotebookNode)
		node = self._create_node(parent=parent, is_dirty=False)
		parent.children = [node]
		node.children = [child1, child2]
		child1.parent = node
		child2.parent = node
		
		node.delete()
		
		child1.delete.assert_called_with()
		child2.delete.assert_called_with()
# TODO: Nodig?		self.assertEquals([], node.children)
	
	def test_delete_child_fails(self):
		parent = Mock(spec=NotebookNode)
		parent.parent = None
		child = Mock(spec=NotebookNode)
		node = self._create_node(parent=parent, is_dirty=False)
		parent.children = [node]
		node.children = [child]
		child.parent = node
		child.delete.side_effect = Exception()
		
		with self.assertRaises(Exception):
			node.delete()

		self.assertEquals(False, node.is_dirty)
		self.assertEquals(False, node.is_deleted_unsaved)
		self.assertEquals(True, node in parent.children)
	
	def test_delete_if_root(self):
		child = Mock(spec=NotebookNode)
		node = self._create_node(parent=None, is_dirty=False)
		node.children = [child]
		child.parent = node
		
		with self.assertRaises(IllegalOperationError):
			node.delete()
		
		self.assertEquals(False, child.delete.called)
## TODO: Nodig?		self.assertEquals([child], node.children)
		self.assertEquals(False, node.is_dirty)
		self.assertEquals(False, node.is_deleted_unsaved)

	def test_new_content_child_node(self):
		node = self._create_node(parent=None, is_dirty=False)
		
		self.assertEquals(True, node.can_add_new_content_child_node())
		
		# Add content node.
		child = node.new_content_child_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
 				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
				)
		
		# Verify the parent.
		self.assertEquals([child], node.children)
		
		# Verify the child.
		self.assertEquals(DEFAULT_ID, child.node_id)
		self.assertEquals(CONTENT_TYPE_HTML, child.content_type)
		self.assertEquals(node, child.parent)
		self.assertEquals(DEFAULT_TITLE, child.title)
		self.assertEquals(DEFAULT_HTML_PAYLOAD_NAME, child.main_payload_name)
		self.assertEquals([DEFAULT_PNG_PAYLOAD_NAME], child.additional_payload_names)
		self.assertEquals(DEFAULT_HTML_PAYLOAD, child.get_payload(DEFAULT_HTML_PAYLOAD_NAME))
		self.assertEquals(DEFAULT_PNG_PAYLOAD, child.get_payload(DEFAULT_PNG_PAYLOAD_NAME))
		self.assertEquals(True, child.is_dirty)
	
	def test_new_content_child_node_in_trash_1(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = True
		parent.is_in_trash = False
		node = self._create_node(parent=parent, is_dirty=False)
		
		self.assertEquals(False, node.can_add_new_content_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_content_child_node(
					node_id=DEFAULT_ID,
					content_type=CONTENT_TYPE_HTML,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
	 				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
	 				)
	
	def test_new_content_child_node_in_trash_2(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = True
		node = self._create_node(parent=parent, is_dirty=False)
		
		self.assertEquals(False, node.can_add_new_content_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_content_child_node(
					node_id=DEFAULT_ID,
					content_type=CONTENT_TYPE_HTML,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
	 				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
	 				)
	
	def test_new_content_child_node_if_deleted_unsaved(self):
		parent = Mock(spec=NotebookNode)
		parent.parent = None
		parent.content_type = CONTENT_TYPE_HTML
		node = self._create_node(parent=parent, is_dirty=False)
		parent.children = [node]
		node.delete()
		
		self.assertEquals(False, node.can_add_new_content_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_content_child_node(
					node_id=DEFAULT_ID,
					content_type=CONTENT_TYPE_HTML,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
	 				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
	 				)
	
	def test_new_content_child_node_after_sibling(self):
		node = self._create_node(parent=None, is_dirty=False)
		
		child1 = node.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		child2 = node.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Add content node.
		child3 = node.new_content_child_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
 				additional_payloads=[],
 				after=child1,
				)
		
		# Verify the parent.
		self.assertEquals([child1, child3, child2], node.children)
		
	def test_new_folder_child_node(self):
		node = self._create_node(parent=None, is_dirty=False)
		
		self.assertEquals(True, node.can_add_new_folder_child_node())
		
		# Add folder node.
		child = node.new_folder_child_node(
				node_id=DEFAULT_ID,
				title=DEFAULT_TITLE,
				)
		
		# Verify the parent.
		self.assertEquals([child], node.children)
		
		# Verify the child.
		self.assertEquals(DEFAULT_ID, child.node_id)
		self.assertEquals(CONTENT_TYPE_FOLDER, child.content_type)
		self.assertEquals(node, child.parent)
		self.assertEquals(DEFAULT_TITLE, child.title)
		self.assertEquals(True, child.is_dirty)
	
	def test_new_folder_child_node_in_trash_1(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = True
		parent.is_in_trash = False
		node = self._create_node(parent=parent, is_dirty=False)
		
		self.assertEquals(False, node.can_add_new_folder_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_folder_child_node(
					node_id=DEFAULT_ID,
					title=DEFAULT_TITLE,
	 				)
	
	def test_new_folder_child_node_in_trash_2(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = True
		node = self._create_node(parent=parent, is_dirty=False)
		
		self.assertEquals(False, node.can_add_new_folder_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_folder_child_node(
					node_id=DEFAULT_ID,
					title=DEFAULT_TITLE,
	 				)
	
	def test_new_folder_child_node_if_deleted_unsaved(self):
		parent = Mock(spec=NotebookNode)
		parent.parent = None
		parent.content_type = CONTENT_TYPE_HTML
		node = self._create_node(parent=parent, is_dirty=False)
		parent.children = [node]
		node.delete()
		
		self.assertEquals(False, node.can_add_new_folder_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_folder_child_node(
					node_id=DEFAULT_ID,
					title=DEFAULT_TITLE,
	 				)
	
class ContentNodeTest(unittest.TestCase, ContentFolderNodeTestBase):
	def _create_node(
			self,
			parent=None,
			is_dirty=True,
			):
		
		node_id = new_node_id()
		content_type = DEFAULT_CONTENT_TYPE
		title = DEFAULT_TITLE
		main_payload = (DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD)
		additional_payloads = [(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)]
		
		return ContentNode(
				notebook_storage=None, #TODO
				node_id=node_id,
				content_type=content_type,
				parent=parent,
				title=title,
				main_payload=main_payload,
				additional_payloads=additional_payloads,
				is_dirty=is_dirty,
				)
	
	def test_add_additional_payload(self):
		node = ContentNode(
				notebook_storage=None,
				node_id=new_node_id(),
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_JPG_PAYLOAD_NAME],
				is_dirty=False
				)
		
		node.add_additional_payload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)
		
		self.assertEquals([DEFAULT_JPG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_NAME], node.additional_payload_names)
		self.assertEquals(DEFAULT_PNG_PAYLOAD, node.get_payload(DEFAULT_PNG_PAYLOAD_NAME))		
	
	def test_add_additional_payload_existing1(self):
		node = ContentNode(
				notebook_storage=None,
				node_id=new_node_id(),
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[],
				is_dirty=False
				)
		
		with self.assertRaises(PayloadAlreadyExistsError):
			node.add_additional_payload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD)
	
	def test_add_additional_payload_existing2(self):
		node = ContentNode(
				notebook_storage=None,
				node_id=new_node_id(),
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_PNG_PAYLOAD_NAME],
				is_dirty=False
				)
		
		with self.assertRaises(PayloadAlreadyExistsError):
			node.add_additional_payload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)
	
	def test_get_payload_from_storage(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		node = ContentNode(
				notebook_storage=notebook_storage,
				node_id=new_node_id(),
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[],
				is_dirty=False
				)

		def side_effect_get_node_payload(node_id, payload_name):
			if node_id == node.node_id and payload_name == DEFAULT_HTML_PAYLOAD_NAME:
				return io.BytesIO(DEFAULT_HTML_PAYLOAD)
			else:
				raise storage.PayloadDoesNotExistError
		notebook_storage.get_node_payload.side_effect = side_effect_get_node_payload
		
		self.assertEqual(DEFAULT_HTML_PAYLOAD, node.get_payload(DEFAULT_HTML_PAYLOAD_NAME))
		
	def test_get_payload_nonexistent(self):
		node = ContentNode(
				notebook_storage=None,
				node_id=new_node_id(),
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[],
				is_dirty=False
				)
		
		with self.assertRaises(PayloadDoesNotExistError):
			node.get_payload('unknown_name')
	
	def test_remove_additional_payload(self):
		node = ContentNode(
				notebook_storage=None,
				node_id=new_node_id(),
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[],
				is_dirty=False
				)
		
		node.add_additional_payload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		
		self.assertEquals([], node.additional_payload_names)
		with self.assertRaises(PayloadDoesNotExistError):
			node.get_payload(DEFAULT_PNG_PAYLOAD_NAME)
	
	def test_remove_additional_payload_existing_in_storage(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		node = ContentNode(
				notebook_storage=notebook_storage,
				node_id=new_node_id(),
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_PNG_PAYLOAD_NAME],
				is_dirty=False
				)

		def side_effect_get_node_payload(node_id, payload_name):
			if node_id == node.node_id and payload_name == DEFAULT_PNG_PAYLOAD_NAME:
				return io.BytesIO(DEFAULT_PNG_PAYLOAD)
			else:
				raise storage.PayloadDoesNotExistError
		notebook_storage.get_node_payload.side_effect = side_effect_get_node_payload
		
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		
		self.assertEquals([], node.additional_payload_names)
		with self.assertRaises(PayloadDoesNotExistError):
			node.get_payload(DEFAULT_PNG_PAYLOAD_NAME)
	
	def test_set_main_payload(self):
		node = ContentNode(
				notebook_storage=None,
				node_id=new_node_id(),
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[],
				is_dirty=True
				)
		
		node.set_main_payload('new payload')
		
		self.assertEquals('new payload', node.get_payload(DEFAULT_HTML_PAYLOAD_NAME))		
	
	def test_set_main_payload_existing_in_storage(self):
		node = ContentNode(
				notebook_storage=None,
				node_id=new_node_id(),
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[],
				is_dirty=False
				)
		
		node.set_main_payload('new payload')
		
		self.assertEquals('new payload', node.get_payload(DEFAULT_HTML_PAYLOAD_NAME))		
	
	def test_copy(self):
		"""Tests copying a single node without its children."""
		
		# Create the original and target nodes. The source has a child node.
		original = ContentNode(
				notebook_storage=None,
				node_id=new_node_id(),
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
				is_dirty=True
				)
		original.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target = Mock(spec=NotebookNode)
		
		# Verify the original.
		self.assertEquals(True, original.can_copy(target, with_subtree=False))
		
		# Copy the node.
		original.copy(target, with_subtree=False)
		
		# Verify the notebook, the parent and the copy.
		target.new_content_child_node.assert_called_once_with(
				node_id=mock.ANY,
				content_type=DEFAULT_CONTENT_TYPE,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
				)
	
	def test_copy_payload_in_storage(self):
		"""Tests copying a single node without its children."""
		
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the original and target nodes. The source has a child node.
		original = ContentNode(
				notebook_storage=notebook_storage,
				node_id=new_node_id(),
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_PNG_PAYLOAD_NAME],
				is_dirty=True
				)
		original.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target = Mock(spec=NotebookNode)
		
		def side_effect_get_node_payload(node_id, payload_name):
			if node_id == original.node_id and payload_name == DEFAULT_HTML_PAYLOAD_NAME:
				return io.BytesIO(DEFAULT_HTML_PAYLOAD)
			elif node_id == original.node_id and payload_name == DEFAULT_PNG_PAYLOAD_NAME:
				return io.BytesIO(DEFAULT_PNG_PAYLOAD)
			else:
				raise storage.PayloadDoesNotExistError
		notebook_storage.get_node_payload.side_effect = side_effect_get_node_payload
		
		# Verify the original.
		self.assertEquals(True, original.can_copy(target, with_subtree=False))
		
		# Copy the node.
		original.copy(target, with_subtree=False)
		
		# Verify the notebook, the parent and the copy.
		target.new_content_child_node.assert_called_once_with(
				node_id=mock.ANY,
				content_type=DEFAULT_CONTENT_TYPE,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
				)

	
	# Further tests:
	# - copy with payload in storage



# Utilities

class AnyUuidMatcher(object):
	def __init__(self):
		self.last_match = None
	
	def __eq__(self, other):
		matcher = re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', other)
		if matcher is not None:
			self.last_match = other
			return True
		else:
			return False

# -*- coding: utf-8 -*-

from mock import Mock
import re
import unittest

from keepnote.notebooknew.storage import NotebookStorage, StoredNode
from keepnote.notebooknew import *
from keepnote.notebooknew.storage.mem import InMemoryStorage

DEFAULT_ID = 'my_id'
DEFAULT_CONTENT_TYPE = CONTENT_TYPE_PAGE
DEFAULT_TITLE = 'my_title'
DEFAULT_PAYLOAD_NAMES = ['my_payload1', 'my_payload2']

# The following StoredNodes and NotebookNodes have the following structure:
# root
#   child1
#     child11
#     child12
#       child121
#   child2
#     child21
ROOT_SN = StoredNode('root_id', CONTENT_TYPE_DIR, attributes={}, payload_names=[])
CHILD1_SN = StoredNode('child1_id', CONTENT_TYPE_PAGE, attributes={PARENT_ID_ATTRIBUTE: 'root_id'}, payload_names=[])
CHILD11_SN = StoredNode('child11_id', CONTENT_TYPE_PAGE, attributes={PARENT_ID_ATTRIBUTE: 'child1_id'}, payload_names=[])
CHILD12_SN = StoredNode('child12_id', CONTENT_TYPE_PAGE, attributes={PARENT_ID_ATTRIBUTE: 'child1_id'}, payload_names=[])
CHILD121_SN = StoredNode('child121_id', CONTENT_TYPE_PAGE, attributes={PARENT_ID_ATTRIBUTE: 'child12_id'}, payload_names=[])
CHILD2_SN = StoredNode('child2_id', CONTENT_TYPE_PAGE, attributes={PARENT_ID_ATTRIBUTE: 'root_id'}, payload_names=[])
CHILD21_SN = StoredNode('child21_id', CONTENT_TYPE_PAGE, attributes={PARENT_ID_ATTRIBUTE: 'child2_id'}, payload_names=[])
ROOT_NN = NotebookNode('root_id', CONTENT_TYPE_DIR, None, [])
CHILD1_NN = NotebookNode('child1_id', CONTENT_TYPE_PAGE, ROOT_NN, [])
CHILD11_NN = NotebookNode('child11_id', CONTENT_TYPE_PAGE, CHILD1_NN, [])
CHILD12_NN = NotebookNode('child12_id', CONTENT_TYPE_PAGE, CHILD1_NN, [])
CHILD121_NN = NotebookNode('child121_id', CONTENT_TYPE_PAGE, CHILD12_NN, [])
CHILD2_NN = NotebookNode('child2_id', CONTENT_TYPE_PAGE, ROOT_NN, [])
CHILD21_NN = NotebookNode('child21_id', CONTENT_TYPE_PAGE, CHILD2_NN, [])

class NotebookTest(unittest.TestCase):
	def test_structure_only_root(self):
		"""Test the NotebookNode structure with a just a root."""
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify notebook.root.
		self.assertEqual(ROOT_NN, notebook.root)
		
	def test_structure_two_levels(self):
		"""Test the NotebookNode structure with a root and direct children."""
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, CHILD1_SN, CHILD2_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the structure.
		self.assertEqual(ROOT_NN, notebook.root)
		self.assertEqual([CHILD1_NN, CHILD2_NN], notebook.root.children)
		
	def test_structure_multiple_levels(self):
		"""Test the NotebookNode structure with multiple levels of nodes."""
		self.maxDiff=None
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, CHILD1_SN, CHILD11_SN, CHILD12_SN, CHILD121_SN, CHILD2_SN, CHILD21_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the structure.
		self.assertEqual(ROOT_NN, notebook.root)
		self.assertEqual([CHILD1_NN, CHILD2_NN], notebook.root.children)
		self.assertEqual([CHILD11_NN, CHILD12_NN], notebook.root.children[0].children)
		self.assertEqual([CHILD21_NN], notebook.root.children[1].children)
		
	def test_structure_stored_nodes_postordered(self):
		"""Test the NotebookNode structure with multiple levels of nodes, if the backing NotebookStorage.get_all_nodes()
		returns the StoredNotes in another order. In this case, the order achieved when traversing the tree depth-first
		left-to-right post-order."""
		self.maxDiff=None
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [CHILD11_SN, CHILD121_SN, CHILD12_SN, CHILD1_SN, CHILD21_SN, CHILD2_SN, ROOT_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the structure.
		self.assertEqual(ROOT_NN, notebook.root)
		self.assertEqual([CHILD1_NN, CHILD2_NN], notebook.root.children)
		self.assertEqual([CHILD11_NN, CHILD12_NN], notebook.root.children[0].children)
		self.assertEqual([CHILD21_NN], notebook.root.children[1].children)
	
	def test_validation_two_roots(self):
		"""Test a NotebookStorage with two roots."""
		root1_sn = StoredNode('root1_id', CONTENT_TYPE_DIR, attributes={}, payload_names=[])
		root2_sn = StoredNode('root2_id', CONTENT_TYPE_DIR, attributes={}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [root1_sn, root2_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_validation_unknown_parent(self):
		"""Test a NotebookStorage with a root and a node that references an unknown parent."""
		child_sn = StoredNode('child_id', CONTENT_TYPE_DIR, attributes={PARENT_ID_ATTRIBUTE: 'unknown_id'}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, child_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_validation_parent_is_child(self):
		"""Test a NotebookStorage with a root and a node that is its own parent."""
		child_sn = StoredNode('child_id', CONTENT_TYPE_DIR, attributes={PARENT_ID_ATTRIBUTE: 'child_id'}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, child_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_validation_cycle_no_root(self):
		"""Test a NotebookStorage with a cycle and no root."""
		cycle_node1_sn = StoredNode('cycle_node1_id', CONTENT_TYPE_DIR, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node2_id'}, payload_names=[])
		cycle_node2_sn = StoredNode('cycle_node2_id', CONTENT_TYPE_DIR, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node1_id'}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [cycle_node1_sn, cycle_node2_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_validation_cycle_with_root(self):
		"""Test a NotebookStorage with a root and a cycle."""
		cycle_node1_sn = StoredNode('cycle_node1_id', CONTENT_TYPE_DIR, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node3_id'}, payload_names=[])
		cycle_node2_sn = StoredNode('cycle_node2_id', CONTENT_TYPE_DIR, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node1_id'}, payload_names=[])
		cycle_node3_sn = StoredNode('cycle_node3_id', CONTENT_TYPE_DIR, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node2_id'}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, CHILD1_SN, cycle_node1_sn, cycle_node2_sn, cycle_node3_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_root_created_in_empty_storage(self):
		"""Test if a root is created in an empty NotebookStorage."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
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
		
		any_uuid_matcher = AnyUuidMatcher()
		
		# Verify notebook_storage.add_node().
		notebook_storage.add_node.assert_called_once_with(node_id=any_uuid_matcher, content_type=CONTENT_TYPE_DIR, attributes={}, payloads=[])
		
		# Verify notebook.root.
		self.assertEqual(NotebookNode(any_uuid_matcher.last_match, CONTENT_TYPE_DIR, None, []), notebook.root)

	def test_client_preferences(self):
		"""Test the setting and getting of Notebook client preferences."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
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

class NotebookNodeTest(unittest.TestCase):
	def _create_node(
			self,
			node_id=DEFAULT_ID,
			content_type=DEFAULT_CONTENT_TYPE,
			parent=None,
			payload_names=DEFAULT_PAYLOAD_NAMES,
			):
		
		return NotebookNode(node_id, content_type, parent, payload_names)
		
	def test_object_fields_initialized(self):
		parent = self._create_node()
		node = self._create_node(parent=parent)

		self.assertEqual(DEFAULT_ID, node.node_id)
		self.assertEqual(DEFAULT_CONTENT_TYPE, node.content_type)
		self.assertEqual(parent, node.parent)
		self.assertEqual(DEFAULT_PAYLOAD_NAMES, node.payload_names)

	def test_equals(self):
		parent = self._create_node()
		
		node1 = self._create_node(parent=parent)
		node1a = self._create_node(parent=parent)

		self.assertTrue(node1 == node1a)
		self.assertFalse(node1 != node1a)

		node2 = self._create_node(node_id=None, parent=parent)
		node3 = self._create_node(content_type=None, parent=parent)
		node4 = self._create_node(payload_names=None, parent=parent)
		node5 = self._create_node(parent=None)

		self.assertFalse(node1 == node2)
		self.assertFalse(node1 == node3)
		self.assertFalse(node1 == node4)
		self.assertFalse(node1 == node5)
		self.assertTrue(node1 != node2)
		self.assertTrue(node1 != node3)
		self.assertTrue(node1 != node4)
		self.assertTrue(node1 != node5)

		self.assertFalse(node1 == 'asdf')
	
	def test_add_children_without_payload(self):
		storage = InMemoryStorage()
		
		# Add nodes first.
		notebook = Notebook(storage)
		child1 = notebook.root.new_child(DEFAULT_ID + '1', DEFAULT_CONTENT_TYPE)
		child2 = notebook.root.new_child(DEFAULT_ID + '2', DEFAULT_CONTENT_TYPE)
		
		# Verify the returned NotebookNodes.
		self.assertEqual(NotebookNode(DEFAULT_ID + '1', DEFAULT_CONTENT_TYPE, notebook.root, []), child1)
		self.assertEqual(NotebookNode(DEFAULT_ID + '2', DEFAULT_CONTENT_TYPE, notebook.root, []), child2)
		
		# Verify the parent's children.
		self.assertEqual([child1, child2], notebook.root.children)
		
	
	

# Utility functions

def create_attributes(
		title=None
		):
	
	attributes = {}
	
	if title is not None:
		attributes['title'] = title
	
	return attributes

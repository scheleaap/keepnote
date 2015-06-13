# -*- coding: utf-8 -*-

import base64
import copy
import io
from mock import ANY, Mock
import re
import unittest

from keepnote.notebooknew import *
from keepnote.notebooknew.storage import NotebookStorage, StoredNode
from keepnote.notebooknew.storage.mem import InMemoryStorage
from test.notebooknew.storage import DEFAULT_HTML_PAYLOAD_NAME

DEFAULT_ID = 'my_id'
DEFAULT_CONTENT_TYPE = CONTENT_TYPE_HTML
DEFAULT_TITLE = 'my_title'
DEFAULT_PAYLOAD_NAMES = ['my_payload1', 'my_payload2']
DEFAULT_HTML_PAYLOAD_NAME = os.path.basename('index.html')
DEFAULT_HTML_PAYLOAD = base64.b64decode('PCFET0NUWVBFIGh0bWw+DQoNCjxoMT5UZXN0IE5vZGU8L2gxPg0KPHA+VGhpcyBpcyBhIG5vZGUgdXNlZCBmb3IgdGVzdGluZy48L3A+DQo=')
DEFAULT_PNG_PAYLOAD_NAME = os.path.basename('image.png')
DEFAULT_PNG_PAYLOAD = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAACAAAAArCAIAAACW3x1gAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAYdEVYdFNvZnR3YXJlAHBhaW50Lm5ldCA0LjAuNWWFMmUAAAWNSURBVFhHrZdZSJVbFMdPYC+ZFKQvolKkZWqa10pIozIaMH1QKSsVUbPBMKciCSrLsCIVnPA6oA8WXIu8ZYUQKikqVwK7zTRro5Y2mGk4nfvz7O139Zzv6Dnd+3s4rPXt/Z3/ntZa+9NodbS1td2+ffvu3bvnz58/efJkZmbmzp07a2trMU6dOlVVVbVr167g4GD6iP6moxkdHQ0PD1+yZMncuXPnzJnj7u6O7efnFxkZqRln3rx5ixcvxpg/f758z2Q0WVlZCxYsEH80Y8aMhQsXWlhYuLm5paennzlz5ty5c4WFhdglJSXNzc379++X75mM5vjx42fPnv1Lx5MnT+RjNX78+MHMEBsaGsLlt6urSzRNgSY+Pp6hSW9KLly4wBRTUlKGh4dx169fz6Tr6upEqzE069atk+Z0sFs+Pj6XLl2qqKioqak5ffo0k379+rVsNoKpAp8/f161atWRI0f+HufatWtRUVFFRUViQsbQF2CY7e3tjx8/HhkZkY90BAYGNjY2SmcCrDBTkY4akwQYF6fTyspq9uzZ0dHR7Kp4jl5oaKiw9fj586eDgwO/0jfgX4H6+vrly5c/evQIm+FnZ2d//fpVNOXl5bW0tAibkHz16hWzBPGEYCQShW2IFGCvFi1adPny5T91XL9+XTQLWH1loVn6/Pz8Y8eOJSYmiif37t1LTU0VtiFjAqz7smXLrl69SlaIi4vjqHAW+/r6ZBet1tvbW1pqIJCQkCAdA8YEWOLVq1cL//v37+ynsBX0nih7IyguLmZA0jFgTICkxgxEfA4ODuqtD9CqHKovX76sXLlS2II9e/YYvqIwJtDR0WFpaUnmERrAv1RXVwsbAgICrly5Iuzk5GRSHqsqXI6GjY3NFKEgN5k42rBhg729fWxsrLOzc0RExMQQpXXjxo1btmzhr9mhoKCggwcPkrpPnDjBmeZoyH5qSAHBp0+f3r9/P3F7FRgjTUTDhw8fPn78GBYWtl0Hp1b20C0vffRiYpKAId++fWtqapKOVktuYPWko4M/JQeTxqki/v7+HAcnJydKFi+KDlMJPHz4kP08evSo9CcI9PT03Lx5k/9l/w8dOkS1GBgYEH2QJBu6urreunUL16gAC8W/s8oTdxsBAo2VoSJxeB48eCAbDHjz5s2sWbNQNSrAaSEBUF7evn2Lyx6UlZUx/RUrVtCkuk965OTklJeXqws0NDRwkDBCQkKEAAfp8OHDlDDlgE5LZ2fn5s2bVQT6+/sZaW9vLzarLASAIBcPTWfHjh0qAklJSaQzYZNHlUJNoiUUbty4IVxTWLt2rb4AS+Hp6akcsosXL3LtEDawyZRiouHZs2fykXH27dtHBdQXSEtLKygokI4uZ9BBSSEIMILKysqlS5cibGzFCHKiXVQ6fQFqDkXtNx3c5l68eEGm5GiKViUOqEUIMFc60+H3cejAxvLinTt3xCsallVYQJRbW1u3traSM3CfP3/u4eHB0lMP2HmeKAIKHCri8Y9xyJuyYZyxi5dyLyLRc0Xkoufr68vQeCLigDXZu3cvrqHAtGgoRkq2efr0KVdHVhm7tLSU4Nq0aRMCDJOUuW3bNjKumIrpjM1AESA+Z86cuXv37tzcXIo+KfPAgQNKZNHKPVXYpjNJgCG7uLiQxUgSYG5YqTJJADi5fCJI5/9AExMT8/LlS+np7i+Ojo7379+X/n9GJVVwYbazs5v22mwiKgLA0WaHqc+EAi5XOaoCtUXvwmIKU30VUU+4wXFro6gRmSIyzEV9BqpQG6RlDqYKUALXrFkjHXMwQ0DUOHPRkFelOSW/LkAy8PLy4vNRYevWrRkZGZRlePfunej36wJczSgyXDH5vMHv7u7GBmoZQc73vq2tLV+TpHG+lsQ7ZqDV/gOanoppyROYaQAAAABJRU5ErkJggg==')

# The following StoredNodes and NotebookNodes have the following structure:
# root
#   child1
#     child11
#     child12
#       child121
#   child2
#     child21
ROOT_SN = StoredNode('root_id', CONTENT_TYPE_DIR, attributes={TITLE_ATTRIBUTE: 'root'}, payload_names=[])
CHILD1_SN = StoredNode('child1_id', CONTENT_TYPE_HTML, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child1'}, payload_names=[])
CHILD11_SN = StoredNode('child11_id', CONTENT_TYPE_HTML, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child11'}, payload_names=[])
CHILD12_SN = StoredNode('child12_id', CONTENT_TYPE_HTML, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child12'}, payload_names=[])
CHILD121_SN = StoredNode('child121_id', CONTENT_TYPE_HTML, attributes={PARENT_ID_ATTRIBUTE: 'child12_id', TITLE_ATTRIBUTE: 'child121'}, payload_names=[])
CHILD2_SN = StoredNode('child2_id', CONTENT_TYPE_HTML, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child2'}, payload_names=[])
CHILD21_SN = StoredNode('child21_id', CONTENT_TYPE_HTML, attributes={PARENT_ID_ATTRIBUTE: 'child2_id', TITLE_ATTRIBUTE: 'child21'}, payload_names=[])
#ROOT_NN = NotebookNode('root_id', CONTENT_TYPE_DIR, None, [], 'root', False)
#CHILD1_NN = NotebookNode('child1_id', CONTENT_TYPE_HTML, ROOT_NN, [], 'child1', False)
#CHILD11_NN = NotebookNode('child11_id', CONTENT_TYPE_HTML, CHILD1_NN, [], 'child11', False)
#CHILD12_NN = NotebookNode('child12_id', CONTENT_TYPE_HTML, CHILD1_NN, [], 'child12', False)
#CHILD121_NN = NotebookNode('child121_id', CONTENT_TYPE_HTML, CHILD12_NN, [], 'child121', False)
#CHILD2_NN = NotebookNode('child2_id', CONTENT_TYPE_HTML, ROOT_NN, [], 'child2', False)
#CHILD21_NN = NotebookNode('child21_id', CONTENT_TYPE_HTML, CHILD2_NN, [], 'child21', False)

class NotebookTest(unittest.TestCase):
	def test_structure_only_root(self):
		"""Test the NotebookNode structure with a just a root."""
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
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
		notebook_storage = Mock(spec=NotebookStorage)
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
		notebook_storage = Mock(spec=NotebookStorage)
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
		notebook_storage = Mock(spec=NotebookStorage)
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
			
	def test_validation_trash_not_child_of_root(self):
		"""Test a NotebookStorage with a trash that is not a child of the root node."""
		trash_sn = StoredNode('trash_id', CONTENT_TYPE_TRASH, attributes={PARENT_ID_ATTRIBUTE: CHILD1_SN.node_id}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, CHILD1_SN, trash_sn]
		
		with self.assertRaises(InvalidStructureError):
			# Initialize Notebook with the mocked NotebookStorage.
			Notebook(notebook_storage)
	
	def test_validation_two_trashes(self):
		"""Test a NotebookStorage with two trashes."""
		trash1_sn = StoredNode('trash1_id', CONTENT_TYPE_TRASH, attributes={}, payload_names=[])
		trash2_sn = StoredNode('trash2_id', CONTENT_TYPE_TRASH, attributes={}, payload_names=[])
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, trash1_sn, trash2_sn]
		
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
		
		# Verify notebook_storage.add_node().
		any_uuid_matcher = AnyUuidMatcher()
		notebook_storage.add_node.assert_called_once_with(node_id=any_uuid_matcher, content_type=CONTENT_TYPE_DIR, attributes={}, payloads=[])
		
		# Verify the node.
		node = notebook.root
		self.assertEquals(any_uuid_matcher.last_match, node.node_id)
		self.assertEquals(CONTENT_TYPE_DIR, node.content_type)
		self.assertEquals([], node.payload_names)
		# TODO: Title?
	
	def test_trash_created_if_missing(self):
		"""Test if a trash is created in a NotebookStorage without one."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify notebook_storage.add_node().
		any_uuid_matcher = AnyUuidMatcher()
		notebook_storage.add_node.assert_called_once_with(node_id=any_uuid_matcher, content_type=CONTENT_TYPE_TRASH, attributes={PARENT_ID_ATTRIBUTE: ROOT_SN.node_id}, payloads=[])
		
		# Verify the node.
		node = notebook.trash
		self.assertEquals(any_uuid_matcher.last_match, node.node_id)
		self.assertEquals(CONTENT_TYPE_TRASH, node.content_type)
		self.assertEquals([], node.payload_names)
		# TODO: Title?
		
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
		
	def test_load_notebook(self):
		"""Test loading a notebook."""
		
		# Initialize a NotebookStorage.
		notebook_storage = InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the Notebook.
		self.assertEquals(False, notebook.is_dirty)
		
	def test_load_content_node(self):
		"""Test loading a content node."""
		
		# Initialize a NotebookStorage.
		notebook_storage = InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						MAIN_PAYLOAD_NAME_ATTRIBUTE: DEFAULT_HTML_PAYLOAD_NAME,
						},
				payloads=[(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD)), (DEFAULT_PNG_PAYLOAD_NAME, io.BytesIO(DEFAULT_PNG_PAYLOAD))]
				)
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		node = notebook.root.children[0]
		self.assertEquals(DEFAULT_ID, node.node_id)
		self.assertEquals(CONTENT_TYPE_HTML, node.content_type)
		self.assertEquals([DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_NAME], node.payload_names)
		self.assertEquals(DEFAULT_TITLE, node.title)
		self.assertEquals(DEFAULT_HTML_PAYLOAD_NAME, node.main_payload_name)
		self.assertEquals(False, node.is_dirty)
	
	def test_load_content_node_missing_title(self):
		"""Test loading a content node without a title."""
		
		# Initialize a NotebookStorage.
		notebook_storage = InMemoryStorage()
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
		notebook_storage = InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_FOLDER,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						},
				)
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		node = notebook.root.children[0]
		self.assertEquals(DEFAULT_ID, node.node_id)
		self.assertEquals(CONTENT_TYPE_HTML, node.content_type)
		self.assertEquals(DEFAULT_TITLE, node.title)
		self.assertEquals(False, node.is_dirty)
	
	def test_load_folder_node_missing_title(self):
		"""Test loading a folder node without a title."""
		
		# Initialize a NotebookStorage.
		notebook_storage = InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_FOLDER,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						},
				)
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		node = notebook.root.children[0]
		self.assertEquals('', node.title)
	
	def test_load_trash_node(self):
		"""Test loading a trash node."""
		
		# Initialize a NotebookStorage.
		notebook_storage = InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_TRASH,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						},
				)
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		self.assertEquals(DEFAULT_ID, notebook.trash.node_id)
		self.assertEquals(CONTENT_TYPE_TRASH, notebook.trash.content_type)
		self.assertEquals(DEFAULT_TITLE, notebook.trash.title)
		self.assertEquals(False, notebook.trash.is_dirty)
		self.assertEquals(notebook.trash, notebook.root.children[0])
	
	def test_save_order(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN]
		
		# Add nodes first.
		notebook = Notebook(notebook_storage)
		child1 = notebook.root.new_content_child_node(node_id=CHILD1_NN.node_id, content_type=CHILD1_NN.content_type, title=CHILD1_NN.title, main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD), additional_payloads=[])
		child11 = child1.new_content_child_node(node_id=CHILD11_NN.node_id, content_type=CHILD11_NN.content_type, title=CHILD11_NN.title, main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD), additional_payloads=[])
		child12 = child1.new_content_child_node(node_id=CHILD12_NN.node_id, content_type=CHILD12_NN.content_type, title=CHILD12_NN.title, main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD), additional_payloads=[])
		child121 = child12.new_content_child_node(node_id=CHILD121_NN.node_id, content_type=CHILD121_NN.content_type, title=CHILD121_NN.title, main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD), additional_payloads=[])
		child2 = notebook.root.new_content_child_node(node_id=CHILD2_NN.node_id, content_type=CHILD2_NN.content_type, title=CHILD2_NN.title, main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD), additional_payloads=[])
		child21 = child2.new_content_child_node(node_id=CHILD21_NN.node_id, content_type=CHILD21_NN.content_type, title=CHILD21_NN.title, main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD), additional_payloads=[])
		
		# Verify the notebook.
		self.assertEquals(True, notebook.is_dirty)
		
		# Verify that no nodes were stored yet.
		self.assertFalse(notebook_storage.add_node.called)
		
		# Save the notebook.
		notebook.save()
		
		# Verify that the nodes were stored in the proper order.
		self.assertEquals(6, notebook_storage.add_node.call_count)
		# TODO: HIER BEZIG:
		# - de node IDs extraheren, om zo de volgorde te controleren:
		#   121 voor 12
		#   12 voor 1
		#   11 voor 1
		#   21 voor 2
		#notebook_storage.add_node.call_list_args
		#
		#notebook_storage.add_node.assert_any_call(
		#		node_id=DEFAULT_ID, content_type=ANY, attributes=ANY, payloads=ANY])
		self.assertEquals(True, False)
		
		# Verify the notebook.
		self.assertEquals(False, notebook.is_dirty)
	
	def test_delete_order(self)

# TODO: HIER BEZIG:
#	aan alle tests ook TRASH toevoegen
#	CHILD2 naar TRASH hernoemen en CHILD21 naar TRASH_CHILD1?
#	notebook_storage.get_all_nodes.return_value = [ROOT_SN, TRASH_SN, TRASH_CHILD_SN]

class RootContentFolderNodeTestBase(object):
	def _get_notebook_and_node(self):
		raise NotImplementedError()
	
	def test_new_content_child_node_and_save(self):
		notebook, parent = self._get_notebook_and_node()
		
		# Verify the notebook and the parent node.
		self.assertEquals(False, notebook.is_dirty)
		self.assertEquals(True, parent.can_add_new_content_child_node())
		
		# Add content node.
		node = parent.new_content_child_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
 				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
				)
		
		# Verify the notebook.
		self.assertEquals(True, notebook.is_dirty)
		
		# Verify the node.
		self.assertEquals(DEFAULT_ID, node.node_id)
		self.assertEquals(CONTENT_TYPE_HTML, node.content_type)
		self.assertEquals(DEFAULT_HTML_PAYLOAD_NAME, node.main_payload_name)
		self.assertEquals([DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_NAME], node.payload_names)
		self.assertEquals(DEFAULT_HTML_PAYLOAD, node.get_payload(DEFAULT_HTML_PAYLOAD_NAME))
		self.assertEquals(DEFAULT_PNG_PAYLOAD, node.get_payload(DEFAULT_PNG_PAYLOAD_NAME))
		self.assertEquals(DEFAULT_TITLE, node.title)
		self.assertEquals(True, node.is_dirty)
		
		# Verify that the node was not stored yet.
		self.assertFalse(notebook_storage.add_node.called)
		
		# Save the notebook.
		notebook.save()
		
		# Verify that the node was stored.
		self.assertEquals(1, notebook_storage.add_node.call_count)
		notebook_storage.add_node.assert_any_call(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				attributes={
						PARENT_ID_ATTRIBUTE: parent.node_id,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						MAIN_PAYLOAD_NAME_ATTRIBUTE: DEFAULT_HTML_PAYLOAD_NAME,
						},
				payloads=[(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD)), (DEFAULT_PNG_PAYLOAD_NAME, io.BytesIO(DEFAULT_PNG_PAYLOAD))]
				)
		
		# Verify the notebook and the node.
		self.assertEquals(False, notebook.is_dirty)
		self.assertEquals(False, node.is_dirty)
	
	def test_new_folder_child_node_and_save(self):
		notebook, parent = self._get_notebook_and_node()
		
		# Verify the notebook and the parent node.
		self.assertEquals(False, notebook.is_dirty)
		self.assertEquals(True, parent.can_add_new_folder_child_node())
		
		# Add folder node.
		node = parent.new_folder_child_node(
				node_id=DEFAULT_ID,
				title=DEFAULT_TITLE,
				)
		
		# Verify the notebook.
		self.assertEquals(True, notebook.is_dirty)
		
		# Verify the node.
		self.assertEquals(DEFAULT_ID, node.node_id)
		self.assertEquals(CONTENT_TYPE_FOLDER, node.content_type)
		self.assertEquals(DEFAULT_TITLE, node.title)
		self.assertEquals(True, node.is_dirty)
		
		# Verify that the node was not stored yet.
		self.assertFalse(notebook_storage.add_node.called)
		
		# Save the notebook.
		notebook.save()
		
		# Verify that the node was stored.
		self.assertEquals(1, notebook_storage.add_node.call_count)
		notebook_storage.add_node.assert_any_call(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_FOLDER,
				attributes={
						PARENT_ID_ATTRIBUTE: parent.node_id,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						},
				payloads=[],
				)
		
		# Verify the notebook and the node.
		self.assertEquals(False, notebook.is_dirty)
		self.assertEquals(False, node.is_dirty)
#TODO: Bij de tests hierboven ook controleren dat de nieuwe node in .children zit
	
	def test_copy_and_save(self):
		"""Tests copying a single node without its children and saving the notebook."""
		notebook, original = self._get_notebook_and_node()
		
		# Make sure that the node to be copied has a child node and create a target node.
		original.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the notebook and the original.
		self.assertEquals(False, notebook.is_dirty)
		self.assertEquals(True, original.can_copy(target, with_subtree=False))
		
		# Copy the node.
		copy = original.copy(target, with_subtree=False)
		
		# Verify the notebook, the parent and the copy.
		self.assertEquals(True, notebook.is_dirty)
		self.assertEquals([copy], target.children)
		self.assert_nodes_equal(original, copy, ignore=['node_id', 'children', 'is_dirty'])
		self.assertNotEquals(original.node_id, copy.node_id)
		self.assertEquals([], copy.children)
		self.assertEquals(True, node.is_dirty)
		
		# Verify that the node was not stored yet.
		self.assertFalse(notebook_storage.add_node.called)
		
		# Save the notebook.
		notebook.save()
		
		# Verify that the node was stored.
		self.assertEquals(1, notebook_storage.add_node.call_count)
		notebook_storage.add_node.assert_any_call(node_id=copy.node_id, content_type=ANY, attributes=ANY, payloads=ANY) # TODO: ANY
		
		# Verify the notebook and the node.
		self.assertEquals(False, notebook.is_dirty)
		self.assertEquals(False, node.is_dirty)
	
	def test_copy_after_sibling(self):
		"""Tests copying a node, placing it in a specified location."""
		notebook, original = self._get_notebook_and_node()
		
		# Create a target node with two children.
		target = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target_child1 = target.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target_child2 = target.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the original.
		self.assertEquals(True, original.can_copy(target, behind=target_child1, with_subtree=False))
		
		# Copy the node.
		copy = original.copy(target, behind=target_child1, with_subtree=False)
		
		# Verify the parent.
		self.assertEquals([target_child1, copy, target_child2], target.children)
	
	def test_copy_to_trash(self)
		"""Tests copying a node to the trash."""
		notebook, original = self._get_notebook_and_node()
		
		# Verify the original.
		self.assertEquals(False, original.can_copy(notebook.trash))
		
		with self.assertRaises(InvalidStructureError):
			# Copy the node.
			copy = original.copy(notebook.trash)
	
	def test_copy_to_node_in_trash(self)
		"""Tests copying a node to a node in the trash."""
		notebook, original = self._get_notebook_and_node()
		
		# Create a target node.
		target = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target.trash()
		
		# Verify the original.
		self.assertEquals(False, original.can_copy(target))
		
		with self.assertRaises(InvalidStructureError):
			# Copy the node.
			copy = original.copy(target)
	
	def test_copy_to_notebook_and_save(self):
		"""Test copying a node to another notebook."""
		notebook1, original = self._get_notebook_and_node()
		notebook2, target = self._get_notebook_and_node()
		
		# Make sure that the node to be copied has a child node.
		original.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the target notebook and the original.
		self.assertEquals(False, notebook2.is_dirty)
		self.assertEquals(True, original.can_copy(target))
		
		# Copy the node.
		copy = original.copy(target)
		
		# Verify the target notebook, the parent and the copy.
		self.assertEquals(True, notebook2.is_dirty)
		self.assertEquals([copy], target.children)
		self.assertNotEquals(original.node_id, copy.node_id)
		self.assert_nodes_equal(original, copy, ignore=['node_id', 'is_dirty'])
		self.assertEquals(True, node.is_dirty)
		
		# Verify that the node was not stored yet.
		self.assertFalse(notebook_storage.add_node.called)
		
		# Save the target notebook.
		notebook2.save()
		
		# Verify that the node was stored.
		self.assertEquals(1, notebook_storage.add_node.call_count)
		notebook_storage.add_node.assert_any_call(node_id=copy.node_id, content_type=ANY, attributes=ANY, payloads=ANY) # TODO: ANY
		
		# Verify the notebook and the node.
		self.assertEquals(False, notebook2.is_dirty)
		self.assertEquals(False, node.is_dirty)
	
	def test_copy_subtree_to_child(self)
		"""Tests copying a node with its subtree to one of its children."""
		notebook, original = self._get_notebook_and_node()
		
		# Make sure that the node to be copied has a child node.
		original.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target = original.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the original.
		self.assertEquals(False, original.can_copy(target, with_subtree=True))
		
		with self.assertRaises(InvalidStructureError):
			# Copy the node.
			copy = original.copy(target, with_subtree=True)

class ContentFolderNodeTestBase(RootContentFolderNodeTestBase):
	def test_new_content_child_node_in_trash(self):
		notebook, parent = self._get_notebook_and_node()
		
		# Move parent to trash.
		parent.move(notebook.trash)
		
		# Verify the parent node.
		self.assertEquals(False, parent.can_add_new_content_child_node())
		
		with self.assertRaises(InvalidStructureError):
			# Add content node.
			node = parent.new_content_child_node(
					node_id=DEFAULT_ID,
					content_type=CONTENT_TYPE_HTML,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
					)
	
	def test_new_folder_child_node_in_trash(self):
		notebook, parent = self._get_notebook_and_node()
		
		# Move parent to trash.
		parent.move(notebook.trash)
		
		# Verify the parent node.
		self.assertEquals(False, parent.can_add_new_folder_child_node())
		
		with self.assertRaises(InvalidStructureError):
			# Add folder node.
			node = parent.new_folder_child_node(
					node_id=DEFAULT_ID,
					title=DEFAULT_TITLE,
					)
	
	def test_delete_and_save(self)
		"""Tests deleting a node."""
		notebook, node = self._get_notebook_and_node()
		parent = node.parent
		
		# Verify the notebook and the node.
		self.assertEquals(False, notebook.is_dirty)
		self.assertEquals(True, node.can_delete())
		

		# Delete the node.
		node.delete()
		
		# Verify the notebook, the parent and the copy.
		self.assertEquals(True, notebook.is_dirty)
		self.assertEquals([], parent.children)
		self.assertEquals(None, node.parent)
		
		# Verify that the node was not deleted from storage yet.
		self.assertFalse(notebook_storage.delete_node.called)
		
		# Save the notebook.
		notebook.save()
		
		# Verify that the node was deleted.
		self.assertEquals(1, notebook_storage.delete_node.call_count)
		notebook_storage.delete_node.assert_any_call(node_id=node.node_id)
		
		# Verify the notebook and the node.
		self.assertEquals(False, notebook.is_dirty)
	
	def test_copy_subtree(self)
		"""Tests copying a node and its children."""
		notebook, original = self._get_notebook_and_node()
		
		# Make sure that the node to be copied has child nodes and create a target node.
		original_child1 = original.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		original_child11 = original_child1.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Copy the node.
		copy = original.copy(target, with_subtree=True)
		
		# Verify the copy's child.
		copy_child1 = copy.children[0]
		copy_child11 = copy_child1.children[0]
		self.assert_nodes_equal(original_child1, copy_child1, ignore=['node_id', 'children', 'is_dirty'])
		self.assert_nodes_equal(original_child11, copy_child11, ignore=['node_id', 'is_dirty'])
		self.assertNotEquals(original_child1.node_id, copy_child1.node_id)
		self.assertNotEquals(original_child11.node_id, copy_child11.node_id)
		self.assertEquals(True, copy_child1.is_dirty)
		self.assertEquals(True, copy_child11.is_dirty)
	
	def test_move_and_save(self):
		"""Tests moving a node and saving the notebook."""
		notebook, node = self._get_notebook_and_node()
		
		# Make sure that the node to be copied has a child node and create a target node.
		node.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the notebook and the original.
		self.assertEquals(False, notebook.is_dirty)
		self.assertEquals(True, original.can_move(target))
		
		# Move the node.
		node.move(target)
		
		# Verify the notebook, the parent, the target and the node.
		self.assertEquals(True, notebook.is_dirty)
		self.assertEquals([], parent.children)
		self.assertEquals([node], target.children)
		self.assertEquals(True, node.is_dirty)
		
		# Verify that the node was not stored yet.
		self.assertFalse(notebook_storage.add_node.called)
		
		# Save the notebook.
		notebook.save()
		
		# Verify that the node was stored.
		self.assertEquals(1, notebook_storage.add_node.call_count)
		notebook_storage.add_node.assert_any_call(node_id=node.node_id, content_type=ANY, attributes=ANY, payloads=ANY) # TODO: ANY
		
		# Verify the notebook and the node.
		self.assertEquals(False, notebook.is_dirty)
		self.assertEquals(False, node.is_dirty)
	
	def test_move_after_sibling(self):
		"""Tests moving a node, placing it in a specified location."""
		notebook, node = self._get_notebook_and_node()
		
		# Create a target node with two children.
		target = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target_child1 = target.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target_child2 = target.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the node.
		self.assertEquals(True, node.can_move(target, behind=target_child1))
		
		# Move the node.
		node.move(target, behind=target_child1)
		
		# Verify the parent.
		self.assertEquals([target_child1, node, target_child2], target.children)
	
	def test_move_to_trash(self):
		"""Tests moving a node to the trash."""
		notebook, node = self._get_notebook_and_node()
		
		# Verify the node.
		self.assertEquals(False, node.can_move(notebook.trash)
		
		with self.assertRaises(InvalidStructureError):
			# Move the node.
			node.move(target, behind=target_child1)
	
	def test_move_to_notebook_and_save(self):
		"""Test moving a node to another notebook."""
		notebook1, node = self._get_notebook_and_node()
		notebook2, target = self._get_notebook_and_node()
		
		# Make sure that the node to be copied has a child node.
		node.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the target notebook and the node.
		self.assertEquals(False, notebook2.is_dirty)
		self.assertEquals(True, node.can_move(target))
		
		# Move the node.
		node.move(target)
		
		# Verify the notebook, the parent, the target and the node.
		self.assertEquals(True, notebook2.is_dirty)
		self.assertEquals([], parent.children)
		self.assertEquals([node], target.children)
		self.assertEquals(True, node.is_dirty)
		
		# Verify that the node was not stored yet.
		self.assertFalse(notebook_storage1.delete_node.called)
		self.assertFalse(notebook_storage2.add_node.called)
		
		# Save the target notebook.
		notebook2.save()
		
		# Verify that the node was stored and deleted.
		self.assertEquals(1, notebook_storage1.delete_node.call_count)
		self.assertEquals(1, notebook_storage2.add_node.call_count)
		notebook_storage1.delete_node.assert_any_call(node_id=node.node_id)
		notebook_storage2.add_node.assert_any_call(node_id=node.node_id, content_type=ANY, attributes=ANY, payloads=ANY) # TODO: ANY
		
		# Verify the notebook and the node.
		self.assertEquals(False, notebook2.is_dirty)
		self.assertEquals(False, node.is_dirty)


class RootNodeTestBase(unittest.TestCase);
	def _get_notebook_and_node(self):
		# Initialize a NotebookStorage.
		notebook_storage = InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		return (notebook, notebook.root)
	
	def test_delete(self):
		"""Test deleting the root."""
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, TRASH_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		self.assertEquals(False, notebook.root.can_delete())
		
		with self.assertRaises(InvalidStructureError):
			# Delete the node.
			node = notebook.root.delete()
	
	def test_copy_subtree(self)
		"""Tests copying the root and its children, including the trash."""
		notebook, root = self._get_notebook_and_node()
		
		# Create a folder child node and create a target node.
		root_trash_child = root.children[0]
		root_folder_child = root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Copy the node.
		copy = root.copy(target, with_subtree=True)
		
		# Verify the copy's children.
		copy_trash_child = copy.children[0]
		self.assert_nodes_equal(root_trash_child, copy_trash_child, ignore=['node_id', 'content_type', 'is_dirty'])
		self.assertNotEquals(root_trash_child.node_id, copy_trash_child.node_id)
		self.assertEqual(CONTENT_TYPE_FOLDER, copy_trash_child.content_type
		self.assertEquals(True, copy_trash_child.is_dirty)
		
		copy_folder_child = copy.children[1]
		self.assert_nodes_equal(root_folder_child, copy_folder_child, ignore=['node_id', 'is_dirty'])
		self.assertNotEquals(root_folder_child.node_id, copy_folder_child.node_id)
		self.assertEquals(True, root_folder_child.is_dirty)
	
	def test_move(self)
		"""Tests moving the root."""
		notebook, node = self._get_notebook_and_node()
		
		# Create a target node.
		target = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the node.
		self.assertEquals(False, node.can_move(target)
		
		with self.assertRaises(InvalidStructureError):
			# Move the node.
			node.move(target)

class TrashNodeTestBase(unittest.TestCase):
	def test_new_content_child_node(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, TRASH_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the parent node.
		self.assertEquals(False, notebook.trash.can_add_new_content_child_node())
		
		with self.assertRaises(InvalidStructureError):
			# Add content node.
			node = notebook.trash.new_content_child_node(
					node_id=DEFAULT_ID,
					content_type=CONTENT_TYPE_HTML,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
					)
	
	def test_new_folder_child_node(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, TRASH_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the parent node.
		self.assertEquals(False, notebook.trash.can_add_new_folder_child_node())
		
		with self.assertRaises(InvalidStructureError):
			# Add folder node.
			node = notebook.trash.new_folder_child_node(
					node_id=DEFAULT_ID,
					title=DEFAULT_TITLE,
					)
	
	def test_delete(self):
		"""Test deleting the trash."""
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, TRASH_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		self.assertEquals(False, notebook.root.can_delete())
		
		with self.assertRaises(InvalidStructureError):
			# Delete the node.
			node = notebook.trash.delete()

TODO: HIER BEZIG
	
	def test_copy_and_save(self):
		"""Tests copying the trash node without its children and saving the notebook."""
		notebook, original = self._get_notebook_and_node()
		
		# Make sure that the node to be copied has a child node and create a target node.
		child = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		child.trash()
		target = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the notebook and the original.
		self.assertEquals(False, notebook.is_dirty)
		self.assertEquals(True, original.can_copy(target, with_subtree=False))
		
		# Copy the node.
		copy = original.copy(target, with_subtree=False)
		
		# Verify the notebook, the parent and the copy.
		self.assertEquals(True, notebook.is_dirty)
		self.assertEquals([copy], target.children)
		self.assert_nodes_equal(original, copy, ignore=['node_id', 'content_type', 'children', 'is_dirty'])
		self.assertNotEquals(original.node_id, copy.node_id)
		self.assertEquals(CONTENT_TYPE_FOLDER, copy.content_type)
		self.assertEquals([], copy.children)
		self.assertEquals(True, node.is_dirty)
		
		# Verify that the node was not stored yet.
		self.assertFalse(notebook_storage.add_node.called)
		
		# Save the notebook.
		notebook.save()
		
		# Verify that the node was stored.
		self.assertEquals(1, notebook_storage.add_node.call_count)
		notebook_storage.add_node.assert_any_call(node_id=copy.node_id, content_type=ANY, attributes=ANY, payloads=ANY) # TODO: ANY
		
		# Verify the notebook and the node.
		self.assertEquals(False, notebook.is_dirty)
		self.assertEquals(False, node.is_dirty)
	
	TODO: HIER BEZIG MET OMBOUWEN VOOR TRASH
	
	def test_copy_after_sibling(self):
		"""Tests copying a node, placing it in a specified location."""
		notebook, original = self._get_notebook_and_node()
		
		# Create a target node with two children.
		target = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target_child1 = target.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target_child2 = target.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the original.
		self.assertEquals(True, original.can_copy(target, behind=target_child1, with_subtree=False))
		
		# Copy the node.
		copy = original.copy(target, behind=target_child1, with_subtree=False)
		
		# Verify the parent.
		self.assertEquals([target_child1, copy, target_child2], target.children)
	
	def test_copy_to_trash(self)
		"""Tests copying a node to the trash."""
		notebook, original = self._get_notebook_and_node()
		
		# Verify the original.
		self.assertEquals(False, original.can_copy(notebook.trash))
		
		with self.assertRaises(InvalidStructureError):
			# Copy the node.
			copy = original.copy(notebook.trash)
	
	def test_copy_to_node_in_trash(self)
		"""Tests copying a node to a node in the trash."""
		notebook, original = self._get_notebook_and_node()
		
		# Put a node in the trash.
		deleted_node = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		deleted_node.trash()
		
		# Verify the original.
		self.assertEquals(False, original.can_copy(deleted_node))
		
		with self.assertRaises(InvalidStructureError):
			# Copy the node.
			copy = original.copy(deleted_node)
	
	def test_copy_to_notebook_and_save(self):
		"""Test copying a node to another notebook."""
		notebook1, original = self._get_notebook_and_node()
		notebook2, target = self._get_notebook_and_node()
		
		# Make sure that the node to be copied has a child node.
		original.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the target notebook and the original.
		self.assertEquals(False, notebook2.is_dirty)
		self.assertEquals(True, original.can_copy(target))
		
		# Copy the node.
		copy = original.copy(target)
		
		# Verify the target notebook, the parent and the copy.
		self.assertEquals(True, notebook2.is_dirty)
		self.assertEquals([copy], target.children)
		self.assertNotEquals(original.node_id, copy.node_id)
		self.assert_nodes_equal(original, copy, ignore=['node_id', 'is_dirty'])
		self.assertEquals(True, node.is_dirty)
		
		# Verify that the node was not stored yet.
		self.assertFalse(notebook_storage.add_node.called)
		
		# Save the target notebook.
		notebook2.save()
		
		# Verify that the node was stored.
		self.assertEquals(1, notebook_storage.add_node.call_count)
		notebook_storage.add_node.assert_any_call(node_id=copy.node_id, content_type=ANY, attributes=ANY, payloads=ANY) # TODO: ANY
		
		# Verify the notebook and the node.
		self.assertEquals(False, notebook2.is_dirty)
		self.assertEquals(False, node.is_dirty)
	
	def test_copy_subtree_to_child(self)
		"""Tests copying a node with its subtree to one of its children."""
		notebook, original = self._get_notebook_and_node()
		
		# Make sure that the node to be copied has a child node.
		original.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		target = original.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the original.
		self.assertEquals(False, original.can_copy(target, with_subtree=True))
		
		with self.assertRaises(InvalidStructureError):
			# Copy the node.
			copy = original.copy(target, with_subtree=True)


	def test_move(self):
		"""Tests moving the trash."""
		notebook, node = self._get_notebook_and_node()
		
		# Create a target node.
		target = notebook.root.new_folder_child_node(node_id=new_node_id(), title=DEFAULT_TITLE)
		
		# Verify the node.
		self.assertEquals(False, node.can_move(target)
		
		with self.assertRaises(InvalidStructureError):
			# Move the node.
			node.move(target)

class ContentNodeTest(unittest.TestCase, ContentAndFolderNodeTestBase):
	def _get_notebook_and_node(self):
		# Initialize a NotebookStorage.
		notebook_storage = InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						MAIN_PAYLOAD_NAME_ATTRIBUTE: DEFAULT_HTML_PAYLOAD_NAME,
						},
				payloads=[(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD)), (DEFAULT_PNG_PAYLOAD_NAME, io.BytesIO(DEFAULT_PNG_PAYLOAD))]
				)
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		return (notebook, notebook.root.children[0])
	
	def test_equals(self):
		def create_node(
				self,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				is_dirty=True,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				new_payloads='default',
				parent=None,
				payload_names='default',
				title=DEFAULT_TITLE,
				):
			
			if new_payloads == 'default':
				new_payloads = [(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD)]
			if payload_names == 'default':
				payload_names = DEFAULT_PAYLOAD_NAMES
			
			return ContentNode(
					node_id=node_id,
					content_type=content_type,
					is_dirty=is_dirty,
					main_payload_name=main_payload_name,
					new_payloads=new_payloads,
					parent=parent,
					payload_names=payload_names,
					title=title,
					)
		
		#TODO: OOK ALLE ATTRIBUTEN VAN NOTEBOOKNODE TESTEN
		parent = self._create_node()
		
		node1 = self._create_node(parent=parent)
		node1a = self._create_node(parent=parent)

		self.assertTrue(node1 == node1a)
		self.assertFalse(node1 != node1a)

		node2 = self._create_node(parent=parent, main_payload_name=None)
		node3 = self._create_node(parent=parent, new_payloads=None)
		node4 = self._create_node(parent=parent, payload_names=None)

		self.assertFalse(node1 == node2)
		self.assertFalse(node1 == node3)
		self.assertFalse(node1 == node4)
		self.assertTrue(node1 != node2)
		self.assertTrue(node1 != node3)
		self.assertTrue(node1 != node4)

		self.assertFalse(node1 == 'asdf')
	
	def test_get_payload_nonexistent(self)

class FolderNodeTest(unittest.TestCase, ContentAndFolderNodeTestBase):
	def _get_notebook_and_node(self):
		# Initialize a NotebookStorage.
		notebook_storage = InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_FOLDER,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						},
				payloads=[]
				)
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		return (notebook, notebook.root.children[0])
	
	def test_equals(self):
		def create_node(
				self,
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_FOLDER,
				is_dirty=True,
				parent=None,
				title=DEFAULT_TITLE,
				):
			
			return FolderNode(
					node_id=node_id,
					content_type=content_type,
					is_dirty=is_dirty,
					parent=parent,
					title=title,
					)
		
		#TODO: OOK ALLE ATTRIBUTEN VAN NOTEBOOKNODE TESTEN
		parent = self._create_node()
		
		node1 = self._create_node(parent=parent)
		node1a = self._create_node(parent=parent)

		self.assertTrue(node1 == node1a)
		self.assertFalse(node1 != node1a)

		node2 = self._create_node(parent=parent, main_payload_name=None)
		node3 = self._create_node(parent=parent, new_payloads=None)
		node4 = self._create_node(parent=parent, payload_names=None)

		self.assertFalse(node1 == node2)
		self.assertFalse(node1 == node3)
		self.assertFalse(node1 == node4)
		self.assertTrue(node1 != node2)
		self.assertTrue(node1 != node3)
		self.assertTrue(node1 != node4)

		self.assertFalse(node1 == 'asdf')


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

def copy_edit_node(
		node,
		parent='default',
		is_dirty='default',
		):
	"""Copy and modify a NotebookNode."""
	
	copied_node = copy.copy(node)
	if parent != 'default':
		copied_node.parent = parent
	if is_dirty != 'default':
		copied_node.is_dirty = is_dirty
	
	return copied_node

# -*- coding: utf-8 -*-

from datetime import datetime
import io
from pytz import utc
import unittest

from keepnote.notebooknew import Notebook, ContentNode, FolderNode, TrashNode, \
		IllegalOperationError
from keepnote.notebooknew import CONTENT_TYPE_HTML, CONTENT_TYPE_TRASH, CONTENT_TYPE_FOLDER
from keepnote.notebooknew import new_node_id
from keepnote.notebooknew.dao import *
import keepnote.notebooknew.storage as storage
from keepnote.notebooknew.storage import StoredNode, StoredNodePayload

from test.notebooknew.testutils import *

PARENT_ID_ATTRIBUTE = 'parent_id'
MAIN_PAYLOAD_NAME_ATTRIBUTE = 'main_payload_name'
TITLE_ATTRIBUTE = 'title'
CREATED_TIME_ATTRIBUTE = 'created_time'
MODIFIED_TIME_ATTRIBUTE = 'modified_time'
ORDER_ATTRIBUTE = 'order'
ICON_NORMAL_ATTRIBUTE = 'icon'
ICON_OPEN_ATTRIBUTE = 'icon_open'
TITLE_COLOR_FOREGROUND_ATTRIBUTE = 'title_fgcolor'
TITLE_COLOR_BACKGROUND_ATTRIBUTE = 'title_bgcolor'
CLIENT_PREFERENCES_ATTRIBUTE = 'client_preferences'

# The following StoredNodes and NotebookNodes have the following structure:
# root
#   child1
#     child11
#     child12
#       child121
#   child2
#     child21
ROOT_SN = StoredNode('root_id', CONTENT_TYPE_TEST, attributes={TITLE_ATTRIBUTE: 'root'}, payloads=[])
CHILD1_SN = StoredNode('child1_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child1'}, payloads=[])
CHILD11_SN = StoredNode('child11_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child11'}, payloads=[])
CHILD12_SN = StoredNode('child12_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child12'}, payloads=[])
CHILD121_SN = StoredNode('child121_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child12_id', TITLE_ATTRIBUTE: 'child121'}, payloads=[])
CHILD2_SN = StoredNode('child2_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child2'}, payloads=[])
CHILD21_SN = StoredNode('child21_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child2_id', TITLE_ATTRIBUTE: 'child21'}, payloads=[])
TRASH_SN = StoredNode('trash_id', CONTENT_TYPE_TRASH, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'trash'}, payloads=[])

def add_storage_node(notebook_storage, sn):
	notebook_storage.add_node(
			node_id=sn.node_id,
			content_type=sn.content_type,
			attributes=sn.attributes,
			payloads=[ (p.name, p.get_data()) for p in sn.payloads ]
			)
	
def datetime_to_timestamp(dt):
	# From https://docs.python.org/3.3/library/datetime.html#datetime.datetime.timestamp
	return (dt - datetime(1970, 1, 1, tzinfo=utc)).total_seconds()

class StructureTest:#(unittest.TestCase):
	def test_new_in_remote_only_root(self):
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		
		dao.sync()
		
		self.assertEqual(ROOT_SN.node_id, notebook.root.node_id)
		self.assertEqual(None, notebook.root.parent)
# TODO: Enable
# 		self.assertEqual(1, len(notebook.root.children))
# 		self.assertEqual(True, notebook.root.children[0].is_trash)
		
	def test_new_in_remote_two_levels(self):
		"""Test the NotebookNode structure with a root and direct children."""
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, CHILD1_SN)
		add_storage_node(notebook_storage, CHILD2_SN)
		add_storage_node(notebook_storage, TRASH_SN)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), TrashNodeDao() ])
		
		dao.sync()
		
		# Verify the structure.
		child1 = notebook.root.children[0]
		child2 = notebook.root.children[1]
		self.assertEqual((CHILD1_SN.node_id, notebook.root, []), (child1.node_id, child1.parent, [node.node_id for node in child1.children]))
		self.assertEqual((CHILD2_SN.node_id, notebook.root, []), (child2.node_id, child2.parent, [node.node_id for node in child2.children]))
	
	def test_new_in_remote_multiple_levels(self):
		"""Test the NotebookNode structure with multiple levels of nodes."""
		self.maxDiff=None
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, CHILD1_SN)
		add_storage_node(notebook_storage, CHILD11_SN)
		add_storage_node(notebook_storage, CHILD12_SN)
		add_storage_node(notebook_storage, CHILD121_SN)
		add_storage_node(notebook_storage, CHILD2_SN)
		add_storage_node(notebook_storage, CHILD21_SN)
		add_storage_node(notebook_storage, TRASH_SN)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), TrashNodeDao() ])
		
		dao.sync()
		
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
	
	def test_new_in_remote_storage_nodes_postordered(self):
		"""Test the NotebookNode structure with multiple levels of nodes, if the backing NotebookStorage.get_all_nodes()
		returns the StoredNotes in another order. In this case, the order achieved when traversing the tree depth-first
		left-to-right post-order."""
		self.maxDiff=None
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, TRASH_SN)
		add_storage_node(notebook_storage, CHILD21_SN)
		add_storage_node(notebook_storage, CHILD2_SN)
		add_storage_node(notebook_storage, CHILD121_SN)
		add_storage_node(notebook_storage, CHILD12_SN)
		add_storage_node(notebook_storage, CHILD11_SN)
		add_storage_node(notebook_storage, CHILD1_SN)
		add_storage_node(notebook_storage, ROOT_SN)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), TrashNodeDao() ])
		
		dao.sync()
		
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
	
	def test_new_in_remote_sync_twice(self):
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, CHILD1_SN)
		add_storage_node(notebook_storage, CHILD11_SN)
		add_storage_node(notebook_storage, CHILD2_SN)
		add_storage_node(notebook_storage, TRASH_SN)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), TrashNodeDao() ])
		
		dao.sync()
		
		old_root = notebook.root
		old_child1 = notebook.root.children[0]
		old_child11 = notebook.root.children[0].children[0]
		old_child2 = notebook.root.children[1]

		self.assertEquals(3, len(old_root.children))
		
		dao.sync()

		new_root = notebook.root
		new_child1 = notebook.root.children[0]
		new_child11 = notebook.root.children[0].children[0]
		new_child2 = notebook.root.children[1]
		
		self.assertEquals(True, old_root is new_root)
		self.assertEquals(True, old_child1 is new_child1)
		self.assertEquals(True, old_child11 is new_child11)
		self.assertEquals(True, old_child2 is new_child2)

		self.assertEquals(3, len(new_root.children))
		
	
	def test_validation_two_roots(self):
		"""Test a NotebookStorage with two roots."""
		root1_sn = StoredNode('root1_id', CONTENT_TYPE_TEST, attributes={}, payloads=[])
		root2_sn = StoredNode('root2_id', CONTENT_TYPE_TEST, attributes={}, payloads=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, root1_sn)
		add_storage_node(notebook_storage, root2_sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()
	
	def test_validation_unknown_parent(self):
		"""Test a NotebookStorage with a root and a node that references an unknown parent."""
		child_sn = StoredNode('child_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'unknown_id'}, payloads=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, child_sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()
	
	def test_validation_parent_is_node_a_child(self):
		"""Test a NotebookStorage with a root and a node that is its own parent."""
		child_sn = StoredNode('child_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child_id'}, payloads=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, child_sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()
	
	def test_validation_cycle_no_root(self):
		"""Test a NotebookStorage with a cycle and no root."""
		cycle_node1_sn = StoredNode('cycle_node1_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node2_id'}, payloads=[])
		cycle_node2_sn = StoredNode('cycle_node2_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node1_id'}, payloads=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, cycle_node1_sn)
		add_storage_node(notebook_storage, cycle_node2_sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()
	
	def test_validation_cycle_with_root(self):
		"""Test a NotebookStorage with a root and a cycle."""
		cycle_node1_sn = StoredNode('cycle_node1_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node3_id'}, payloads=[])
		cycle_node2_sn = StoredNode('cycle_node2_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node1_id'}, payloads=[])
		cycle_node3_sn = StoredNode('cycle_node3_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node2_id'}, payloads=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, CHILD1_SN)
		add_storage_node(notebook_storage, cycle_node1_sn)
		add_storage_node(notebook_storage, cycle_node2_sn)
		add_storage_node(notebook_storage, cycle_node3_sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()

	def test_validation_two_trashes(self):
		"""Test a NotebookStorage with two trashes."""
		trash1_sn = StoredNode('trash1_id', CONTENT_TYPE_TRASH, attributes={}, payloads=[])
		trash2_sn = StoredNode('trash2_id', CONTENT_TYPE_TRASH, attributes={}, payloads=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, trash1_sn)
		add_storage_node(notebook_storage, trash2_sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), TrashNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()

	def test_new_in_local_only_root(self):
		root_nn = TestNotebookNode()
		notebook = Notebook()
		notebook.root = root_nn
		notebook_storage = storage.mem.InMemoryStorage()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), TrashNodeDao() ])

		dao.sync()
		
		self.assertEqual(1, len(list(notebook_storage.get_all_nodes())))
		
		root_sn = notebook_storage.get_node(root_nn.node_id)
		self.assertEqual(False, PARENT_ID_ATTRIBUTE in root_sn.attributes)
	
	def test_new_in_local_multiple_levels(self):
		root_nn = TestNotebookNode()
		child1_nn = TestNotebookNode(parent=root_nn, add_to_parent=True)
		child11_nn = TestNotebookNode(parent=child1_nn, add_to_parent=True)
		child12_nn = TestNotebookNode(parent=child1_nn, add_to_parent=True)
		child121_nn = TestNotebookNode(parent=child12_nn, add_to_parent=True)
		child2_nn = TestNotebookNode(parent=root_nn, add_to_parent=True)
		child21_nn = TestNotebookNode(parent=child2_nn, add_to_parent=True)
		notebook = Notebook()
		notebook.root = root_nn
		notebook_storage = storage.mem.InMemoryStorage()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])

		dao.sync()
		
		self.assertEqual(7, len(list(notebook_storage.get_all_nodes())))
		
		root_sn = notebook_storage.get_node(root_nn.node_id)
		child1_sn = notebook_storage.get_node(child1_nn.node_id)
		child11_sn = notebook_storage.get_node(child11_nn.node_id)
		child12_sn = notebook_storage.get_node(child12_nn.node_id)
		child121_sn = notebook_storage.get_node(child121_nn.node_id)
		child2_sn = notebook_storage.get_node(child2_nn.node_id)
		child21_sn = notebook_storage.get_node(child21_nn.node_id)

		self.assertEqual(False, PARENT_ID_ATTRIBUTE in root_sn.attributes)
		self.assertEqual(root_nn.node_id, child1_sn.attributes[PARENT_ID_ATTRIBUTE])
		self.assertEqual(child1_nn.node_id, child11_sn.attributes[PARENT_ID_ATTRIBUTE])
		self.assertEqual(child1_nn.node_id, child12_sn.attributes[PARENT_ID_ATTRIBUTE])
		self.assertEqual(child12_nn.node_id, child121_sn.attributes[PARENT_ID_ATTRIBUTE])
		self.assertEqual(root_nn.node_id, child2_sn.attributes[PARENT_ID_ATTRIBUTE])
		self.assertEqual(child2_nn.node_id, child21_sn.attributes[PARENT_ID_ATTRIBUTE])
	
	def test_new_in_local_sync_twice(self):
		root_nn = TestNotebookNode()
		child1_nn = TestNotebookNode(parent=root_nn, add_to_parent=True)
		_child11_nn = TestNotebookNode(parent=child1_nn, add_to_parent=True)
		_child2_nn = TestNotebookNode(parent=root_nn, add_to_parent=True)
		notebook = Notebook()
		notebook.root = root_nn
		notebook_storage = storage.mem.InMemoryStorage()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		dao.sync()
		
		dao.sync()
		
		self.assertEqual(4, len(list(notebook_storage.get_all_nodes())))
	
	def test_deleted_in_local(self):
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, CHILD1_SN)
		add_storage_node(notebook_storage, CHILD2_SN)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao()])
		dao.sync()
		self.assertEqual(3, len(list(notebook_storage.get_all_nodes())))
		child2 = [child for child in notebook.root.get_children() if child.node_id == CHILD2_SN.node_id][0]
		child2.delete()
		
		dao.sync()
		
		self.assertEqual(2, len(list(notebook_storage.get_all_nodes())))
		self.assertEqual(False, notebook_storage.has_node(CHILD2_SN.node_id))
		self.assertEqual(False, notebook.has_node(CHILD2_SN.node_id, unsaved_deleted=False))
	
	@unittest.skip('TODO')
	def test_deleted_in_remote(self):
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, CHILD1_SN)
		add_storage_node(notebook_storage, CHILD2_SN)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao()])
		dao.sync()
		self.assertEqual(3, len(list(notebook._traverse_tree())))
		notebook_storage.remove_node(CHILD2_SN.node_id)
		
		dao.sync()
		
		self.assertEqual(2, len(list(notebook_storage.get_all_nodes())))
		self.assertEqual(False, notebook_storage.has_node(CHILD2_SN.node_id))
		self.assertEqual(False, notebook.has_node(CHILD2_SN.node_id))

class ContentFolderTrashNodeTest():
	def _create_storage_node(
			self,
			content_type=DEFAULT_CONTENT_TYPE,
			parent=None,
			title=DEFAULT_TITLE,
# 			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			created_timestamp=DEFAULT_CREATED_TIMESTAMP,
			modified_timestamp=DEFAULT_MODIFIED_TIMESTAMP,
			client_preferences=DEFAULT_CLIENT_PREFERENCES,
			):
		"""Creates a StoredNode of the class under test."""
		raise NotImplementedError()
		
	def _create_notebook_node(
			self,
			notebook_storage=None,
			notebook=None,
			content_type=DEFAULT_CONTENT_TYPE,
			parent=None,
			loaded_from_storage=False,
			title=DEFAULT_TITLE,
# 			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			node_id=DEFAULT,
			created_time=DEFAULT,
			modified_time=DEFAULT,
			add_to_parent=None,
			):
		"""Creates a NotebookNode of the class under test."""
		raise NotImplementedError()
	
	def _get_class_dao(self):
		"""Returns the NotebookNodeDao class for the class under test."""
		raise NotImplementedError()
	
	def test_no_changes_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(parent=root, add_to_parent=True)
		notebook_storage = ReadOnlyInMemoryStorage(storage.mem.InMemoryStorage(), read_only=False)
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ self._get_class_dao() ])
		dao.sync()
		
		notebook_storage.read_only = True
		dao.sync()
		
		# Expected: no exception
	
	def test_content_type_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(content_type=DEFAULT_CONTENT_TYPE, parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(node.content_type, notebook_storage.get_node(node.node_id).content_type)
	
	def test_content_type_new_in_remote(self):
		sn = self._create_storage_node(content_type=DEFAULT_CONTENT_TYPE, parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(sn.content_type, notebook.get_node_by_id(sn.node_id).content_type)
	
	def test_parent_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(node.parent.node_id, notebook_storage.get_node(node.node_id).attributes[PARENT_ID_ATTRIBUTE])
	
	def test_parent_changed_in_local(self):
		root = TestNotebookNode()
		other_node = TestNotebookNode(parent=root, add_to_parent=True)
		node = self._create_notebook_node(parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		dao.sync()
		
		node.move(other_node)
		dao.sync()
		
		self.assertEqual(node.parent.node_id, notebook_storage.get_node(node.node_id).attributes[PARENT_ID_ATTRIBUTE])
	
	def test_parent_new_in_remote(self):
		sn = self._create_storage_node(parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(sn.attributes[PARENT_ID_ATTRIBUTE], notebook.get_node_by_id(sn.node_id).parent.node_id)
	
	@unittest.skip('TODO')
	def test_parent_changed_in_remote(self):
		self.fail()
	
	def test_title_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(title=DEFAULT_TITLE, parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(node.title, notebook_storage.get_node(node.node_id).attributes[TITLE_ATTRIBUTE])
	
	def test_title_changed_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(title=DEFAULT_TITLE, parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		dao.sync()
		
		node.title = 'new title'
		dao.sync()
		
		self.assertEqual(node.title, notebook_storage.get_node(node.node_id).attributes[TITLE_ATTRIBUTE])
	
	def test_title_new_in_remote(self):
		sn = self._create_storage_node(title=DEFAULT_TITLE, parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(sn.attributes[TITLE_ATTRIBUTE], notebook.get_node_by_id(sn.node_id).title)
	
	@unittest.skip('TODO')
	def test_title_changed_in_remote(self):
		self.fail()
	
	@unittest.skip('TODO')
	def test_title_missing_in_remote(self):
		sn = self._create_storage_node(title=None, parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertIsNotNone(notebook.get_node_by_id(sn.node_id).title)
	
	def test_created_time_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(datetime_to_timestamp(node.created_time), notebook_storage.get_node(node.node_id).attributes[CREATED_TIME_ATTRIBUTE])
	
	def test_created_time_new_in_remote(self):
		sn = self._create_storage_node(created_timestamp=DEFAULT_CREATED_TIMESTAMP, parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(sn.attributes[CREATED_TIME_ATTRIBUTE], datetime_to_timestamp(notebook.get_node_by_id(sn.node_id).created_time))
	
	@unittest.skip('TODO')
	def test_created_time_changed_in_remote(self):
		self.fail()
	
	def test_modified_time_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(datetime_to_timestamp(node.modified_time), notebook_storage.get_node(node.node_id).attributes[MODIFIED_TIME_ATTRIBUTE])
	
	def test_modified_time_changed_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		dao.sync()
		
		node.modified_time = datetime.now(tz=utc)
		dao.sync()
		
		self.assertEqual(datetime_to_timestamp(node.modified_time), notebook_storage.get_node(node.node_id).attributes[MODIFIED_TIME_ATTRIBUTE])
	
	def test_modified_time_new_in_remote(self):
		sn = self._create_storage_node(modified_timestamp=DEFAULT_MODIFIED_TIMESTAMP, parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(sn.attributes[MODIFIED_TIME_ATTRIBUTE], datetime_to_timestamp(notebook.get_node_by_id(sn.node_id).modified_time))
	
	@unittest.skip('TODO')
	def test_modified_time_changed_in_remote(self):
		self.fail()
	
	def test_icon_normal_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(icon_normal=DEFAULT_ICON_NORMAL, parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(node.icon_normal, notebook_storage.get_node(node.node_id).attributes[ICON_NORMAL_ATTRIBUTE])
	
	def test_icon_normal_changed_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(icon_normal=DEFAULT_ICON_NORMAL, parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		dao.sync()
		
		node.icon_normal = 'icon_new.png'
		dao.sync()
		
		self.assertEqual(node.icon_normal, notebook_storage.get_node(node.node_id).attributes[ICON_NORMAL_ATTRIBUTE])
	
	def test_icon_normal_new_in_remote(self):
		sn = self._create_storage_node(icon_normal=DEFAULT_ICON_NORMAL, parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(sn.attributes[ICON_NORMAL_ATTRIBUTE], notebook.get_node_by_id(sn.node_id).icon_normal)
	
	@unittest.skip('TODO')
	def test_icon_normal_changed_in_remote(self):
		self.fail()
	
	def test_icon_open_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(icon_open=DEFAULT_ICON_OPEN, parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(node.icon_open, notebook_storage.get_node(node.node_id).attributes[ICON_OPEN_ATTRIBUTE])
	
	def test_icon_open_changed_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(icon_open=DEFAULT_ICON_OPEN, parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		dao.sync()
		
		node.icon_open = 'icon_new.png'
		dao.sync()
		
		self.assertEqual(node.icon_open, notebook_storage.get_node(node.node_id).attributes[ICON_OPEN_ATTRIBUTE])
	
	def test_icon_open_new_in_remote(self):
		sn = self._create_storage_node(icon_open=DEFAULT_ICON_OPEN, parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(sn.attributes[ICON_OPEN_ATTRIBUTE], notebook.get_node_by_id(sn.node_id).icon_open)
	
	@unittest.skip('TODO')
	def test_icon_open_changed_in_remote(self):
		self.fail()
	
	def test_title_color_foreground_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND, parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(node.title_color_foreground, notebook_storage.get_node(node.node_id).attributes[TITLE_COLOR_FOREGROUND_ATTRIBUTE])
	
	def test_title_color_foreground_changed_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND, parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		dao.sync()
		
		node.title_color_foreground = '#c0c0c0'
		dao.sync()
		
		self.assertEqual(node.title_color_foreground, notebook_storage.get_node(node.node_id).attributes[TITLE_COLOR_FOREGROUND_ATTRIBUTE])
	
	def test_title_color_foreground_new_in_remote(self):
		sn = self._create_storage_node(title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND, parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(sn.attributes[TITLE_COLOR_FOREGROUND_ATTRIBUTE], notebook.get_node_by_id(sn.node_id).title_color_foreground)
	
	@unittest.skip('TODO')
	def test_title_color_foreground_changed_in_remote(self):
		self.fail()
	
	def test_title_color_background_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND, parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(node.title_color_background, notebook_storage.get_node(node.node_id).attributes[TITLE_COLOR_BACKGROUND_ATTRIBUTE])
	
	def test_title_color_background_changed_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND, parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		dao.sync()
		
		node.title_color_background = '#c0c0c0'
		dao.sync()
		
		self.assertEqual(node.title_color_background, notebook_storage.get_node(node.node_id).attributes[TITLE_COLOR_BACKGROUND_ATTRIBUTE])
	
	def test_title_color_background_new_in_remote(self):
		sn = self._create_storage_node(title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND, parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(sn.attributes[TITLE_COLOR_BACKGROUND_ATTRIBUTE], notebook.get_node_by_id(sn.node_id).title_color_background)
	
	@unittest.skip('TODO')
	def test_title_color_background_changed_in_remote(self):
		self.fail()
	
	def test_client_preferences_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(parent=root, add_to_parent=True)
		node.client_preferences.get('test', 'key', define=True)
		node.client_preferences.set('test', 'key', 'value')
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(node.client_preferences._data, notebook_storage.get_node(node.node_id).attributes[CLIENT_PREFERENCES_ATTRIBUTE])
	
	def test_client_preferences_changed_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(parent=root, add_to_parent=True)
		node.client_preferences.get('test', 'key', define=True)
		node.client_preferences.set('test', 'key', 'value')
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		dao.sync()
		
		node.client_preferences.get('test', 'key', define=True)
		node.client_preferences.set('test', 'key', 'new value')
		dao.sync()
		
		self.assertEqual(node.client_preferences._data, notebook_storage.get_node(node.node_id).attributes[CLIENT_PREFERENCES_ATTRIBUTE])
	
	def test_client_preferences_new_in_remote(self):
		sn = self._create_storage_node(client_preferences=DEFAULT_CLIENT_PREFERENCES, parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(sn.attributes[CLIENT_PREFERENCES_ATTRIBUTE], notebook.get_node_by_id(sn.node_id).client_preferences._data)
	
	@unittest.skip('TODO')
	def test_client_preferences_changed_in_remote(self):
		self.fail()
	


class ContentNodeTest(ContentFolderTrashNodeTest, unittest.TestCase):
	def _create_storage_node(
			self,
			content_type=DEFAULT_CONTENT_TYPE,
			parent=None,
			title=DEFAULT_TITLE,
# 			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			created_timestamp=DEFAULT_CREATED_TIMESTAMP,
			modified_timestamp=DEFAULT_MODIFIED_TIMESTAMP,
			client_preferences=DEFAULT_CLIENT_PREFERENCES,
			main_payload=DEFAULT,
			additional_payloads=DEFAULT,
			):
		
		attributes = {
			MAIN_PAYLOAD_NAME_ATTRIBUTE: DEFAULT_HTML_PAYLOAD_NAME,
			TITLE_ATTRIBUTE: title,
# 			ORDER_ATTRIBUTE: order,
			ICON_NORMAL_ATTRIBUTE: icon_normal,
			ICON_OPEN_ATTRIBUTE: icon_open,
			TITLE_COLOR_FOREGROUND_ATTRIBUTE: title_color_foreground,
			TITLE_COLOR_BACKGROUND_ATTRIBUTE: title_color_background,
			CREATED_TIME_ATTRIBUTE: created_timestamp,
			MODIFIED_TIME_ATTRIBUTE: modified_timestamp,
			CLIENT_PREFERENCES_ATTRIBUTE: client_preferences,
		}
		if parent is not None:
			attributes[PARENT_ID_ATTRIBUTE] = parent.node_id
		
		if main_payload is DEFAULT:
			main_payload = StoredNodePayloadWithData(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_HASH, lambda: io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))
		if additional_payloads is DEFAULT:
			additional_payloads = [StoredNodePayloadWithData(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_HASH, lambda: io.BytesIO(DEFAULT_PNG_PAYLOAD_DATA))]
		
		node = StoredNode(
			node_id=new_node_id(),
			content_type=content_type,
			attributes=attributes,
			payloads=[main_payload] + additional_payloads,
			)
		
		return node
	
	def _create_notebook_node(
			self,
			notebook=None,
			content_type=DEFAULT_CONTENT_TYPE,
			parent=None,
			loaded_from_storage=False,
			title=DEFAULT_TITLE,
# 			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			node_id=DEFAULT,
			created_time=DEFAULT,
			modified_time=DEFAULT,
			main_payload=DEFAULT,
			additional_payloads=DEFAULT,
			add_to_parent=None,
			):
		
		if main_payload is DEFAULT:
			main_payload = TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA)
		if additional_payloads is DEFAULT:
			additional_payloads = [TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA)]
		
		if loaded_from_storage:
			if main_payload is DEFAULT:
				main_payload = None
			if additional_payloads is DEFAULT:
				additional_payloads = None
			if node_id is DEFAULT:
				node_id = new_node_id()
			if created_time is DEFAULT:
				created_time = DEFAULT_CREATED_TIME
			if modified_time is DEFAULT:
				modified_time = DEFAULT_MODIFIED_TIME
		else:
			if node_id is DEFAULT:
				node_id = None
			if created_time is DEFAULT:
				created_time = None
			if modified_time is DEFAULT:
				modified_time = None
		
		node = ContentNode(
				notebook_storage=None,
				notebook=notebook,
				content_type=content_type,
				parent=parent,
				loaded_from_storage=loaded_from_storage,
				title=title,
# 				order=order,
				icon_normal=icon_normal,
				icon_open=icon_open,
				title_color_foreground=title_color_foreground,
				title_color_background=title_color_background,
				main_payload=main_payload,
				additional_payloads=additional_payloads,
				node_id=node_id,
				created_time=created_time,
				modified_time=modified_time,
				)
		if parent is not None:
			if add_to_parent is None:
				raise IllegalOperationError('Please pass add_to_parent')
			elif add_to_parent == True:
				parent._add_child_node(node)
		return node
	
	def _get_class_dao(self):
		return ContentNodeDao()
	
	def test_load_content_node(self):
		"""Test loading a content node."""
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						MAIN_PAYLOAD_NAME_ATTRIBUTE: DEFAULT_HTML_PAYLOAD_NAME,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						CREATED_TIME_ATTRIBUTE: DEFAULT_CREATED_TIMESTAMP,
						MODIFIED_TIME_ATTRIBUTE: DEFAULT_MODIFIED_TIMESTAMP,
						ORDER_ATTRIBUTE: DEFAULT_ORDER,
						ICON_NORMAL_ATTRIBUTE: DEFAULT_ICON_NORMAL,
						ICON_OPEN_ATTRIBUTE: DEFAULT_ICON_OPEN,
						TITLE_COLOR_FOREGROUND_ATTRIBUTE: DEFAULT_TITLE_COLOR_FOREGROUND,
						TITLE_COLOR_BACKGROUND_ATTRIBUTE: DEFAULT_TITLE_COLOR_BACKGROUND,
						},
				payloads=[
						(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA)),
						(DEFAULT_PNG_PAYLOAD_NAME, io.BytesIO(DEFAULT_PNG_PAYLOAD_DATA))
						]
				)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), ContentNodeDao() ])
		
		dao.sync()
		
		# Verify the node.
		node = [child for child in notebook.root.get_children() if child.node_id == DEFAULT_ID][0]
		self.assertEqual(ContentNode, node.__class__)
# 		self.assertEqual(DEFAULT_ID, node.node_id)
# 		self.assertEqual(CONTENT_TYPE_HTML, node.content_type)
# 		self.assertEqual(DEFAULT_TITLE, node.title)
# 		self.assertEqual(DEFAULT_CREATED_TIME, node.created_time)
# 		self.assertEqual(DEFAULT_MODIFIED_TIME, node.modified_time)
# 		self.assertEqual(DEFAULT_ORDER, node.order)
# 		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
# 		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
# 		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
# 		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
# 		self.assertEqual(DEFAULT_HTML_PAYLOAD_NAME, node.main_payload_name)
# 		self.assertEqual([DEFAULT_PNG_PAYLOAD_NAME], node.additional_payload_names)
		self.assertEqual(False, node.is_dirty)
	
	def test_load_content_node_missing_payload(self):
		"""Test loading a content node without payload."""
		
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				attributes={
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						},
				payloads=[]
				)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), ContentNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()
	
	def test_load_content_node_missing_main_payload_name(self):
		"""Test loading a content node without payload."""
		
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				attributes={
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						},
				payloads=[(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))]
				)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), ContentNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()
	
	def test_load_content_node_missing_main_payload_data(self):
		"""Test loading a content node without payload."""
		
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				attributes={
						MAIN_PAYLOAD_NAME_ATTRIBUTE: DEFAULT_HTML_PAYLOAD_NAME,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						},
				payloads=[(DEFAULT_PNG_PAYLOAD_NAME, io.BytesIO(DEFAULT_PNG_PAYLOAD_DATA))]
				)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), ContentNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()
	
	def test_main_payload_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[],
				parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(node.main_payload_name, notebook_storage.get_node(node.node_id).attributes[MAIN_PAYLOAD_NAME_ATTRIBUTE])
		self.assertEqual(True, StoredNodePayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_HASH) in notebook_storage.get_node(node.node_id).payloads)
		self.assertEqual(node.payloads[DEFAULT_HTML_PAYLOAD_NAME].open().read(), notebook_storage.get_node_payload(node.node_id, DEFAULT_HTML_PAYLOAD_NAME).read())
	
	def test_main_payload_changed_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[],
				parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ self._get_class_dao() ])
		dao.sync()
		
		with node.payloads[DEFAULT_HTML_PAYLOAD_NAME].open('w') as f:
			f.write(DEFAULT_PNG_PAYLOAD_DATA)
		dao.sync()
		
		self.assertEqual(True, StoredNodePayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_HASH) in notebook_storage.get_node(node.node_id).payloads)
		self.assertEqual(node.payloads[DEFAULT_HTML_PAYLOAD_NAME].open().read(), notebook_storage.get_node_payload(node.node_id, DEFAULT_HTML_PAYLOAD_NAME).read())
	
	def test_main_payload_new_in_remote(self):
		sn = self._create_storage_node(
				main_payload=StoredNodePayloadWithData(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_HASH, lambda: io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA)),
				additional_payloads=[],
				parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(sn.attributes[MAIN_PAYLOAD_NAME_ATTRIBUTE], notebook.get_node_by_id(sn.node_id).main_payload_name)
		self.assertEqual(sn.get_payload(DEFAULT_HTML_PAYLOAD_NAME).get_data().read(), notebook.get_node_by_id(sn.node_id).payloads[DEFAULT_HTML_PAYLOAD_NAME].open(mode='r').read())
	
	@unittest.skip('TODO')
	def test_main_payload_changed_in_remote(self):
		self.fail()
	
	def test_additional_payload_new_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA), TestPayload(DEFAULT_JPG_PAYLOAD_NAME, DEFAULT_JPG_PAYLOAD_DATA)],
				parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual(node.additional_payload_names, [p.name for p in notebook_storage.get_node(node.node_id).payloads if p.name != node.main_payload_name])
		self.assertEqual(True, StoredNodePayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_HASH) in notebook_storage.get_node(node.node_id).payloads)
		self.assertEqual(True, StoredNodePayload(DEFAULT_JPG_PAYLOAD_NAME, DEFAULT_JPG_PAYLOAD_HASH) in notebook_storage.get_node(node.node_id).payloads)
		self.assertEqual(node.payloads[DEFAULT_PNG_PAYLOAD_NAME].open().read(), notebook_storage.get_node_payload(node.node_id, DEFAULT_PNG_PAYLOAD_NAME).read())
		self.assertEqual(node.payloads[DEFAULT_JPG_PAYLOAD_NAME].open().read(), notebook_storage.get_node_payload(node.node_id, DEFAULT_JPG_PAYLOAD_NAME).read())
	
	def test_additional_payload_added_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[],
				parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ self._get_class_dao() ])
		dao.sync()
		
		node.add_additional_payload(TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA))
		dao.sync()
		
		self.assertEqual(node.additional_payload_names, [p.name for p in notebook_storage.get_node(node.node_id).payloads if p.name != node.main_payload_name])
		self.assertEqual(True, StoredNodePayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_HASH) in notebook_storage.get_node(node.node_id).payloads)
		self.assertEqual(node.payloads[DEFAULT_PNG_PAYLOAD_NAME].open().read(), notebook_storage.get_node_payload(node.node_id, DEFAULT_PNG_PAYLOAD_NAME).read())
	
	def test_additional_payload_changed_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA)],
				parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ self._get_class_dao() ])
		dao.sync()
		
		with node.payloads[DEFAULT_PNG_PAYLOAD_NAME].open('w') as f:
			f.write(DEFAULT_JPG_PAYLOAD_DATA)
		dao.sync()
		
		self.assertEqual(True, StoredNodePayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_JPG_PAYLOAD_HASH) in notebook_storage.get_node(node.node_id).payloads)
		self.assertEqual(node.payloads[DEFAULT_PNG_PAYLOAD_NAME].open().read(), notebook_storage.get_node_payload(node.node_id, DEFAULT_PNG_PAYLOAD_NAME).read())
	
	def test_additional_payload_removed_in_local(self):
		root = TestNotebookNode()
		node = self._create_notebook_node(
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA)],
				parent=root, add_to_parent=True)
		notebook_storage = storage.mem.InMemoryStorage()
		notebook = Notebook()
		notebook.root = node
		dao = Dao(notebook, notebook_storage, [ self._get_class_dao() ])
		dao.sync()
		
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		dao.sync()
		
		self.assertEqual(False, StoredNodePayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_HASH) in notebook_storage.get_node(node.node_id).payloads)
	
	def test_additional_payload_new_in_remote(self):
		sn = self._create_storage_node(
				main_payload=StoredNodePayloadWithData(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_HASH, lambda: io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA)),
				additional_payloads=[
						StoredNodePayloadWithData(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_HASH, lambda: io.BytesIO(DEFAULT_PNG_PAYLOAD_DATA)),
						StoredNodePayloadWithData(DEFAULT_JPG_PAYLOAD_NAME, DEFAULT_JPG_PAYLOAD_HASH, lambda: io.BytesIO(DEFAULT_JPG_PAYLOAD_DATA))
						],
				parent=ROOT_SN)
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		add_storage_node(notebook_storage, sn)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), self._get_class_dao() ])
		
		dao.sync()
		
		self.assertEqual([DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_JPG_PAYLOAD_NAME], notebook.get_node_by_id(sn.node_id).additional_payload_names)
		self.assertEqual(sn.get_payload(DEFAULT_PNG_PAYLOAD_NAME).get_data().read(), notebook.get_node_by_id(sn.node_id).payloads[DEFAULT_PNG_PAYLOAD_NAME].open(mode='r').read())
		self.assertEqual(sn.get_payload(DEFAULT_JPG_PAYLOAD_NAME).get_data().read(), notebook.get_node_by_id(sn.node_id).payloads[DEFAULT_JPG_PAYLOAD_NAME].open(mode='r').read())
	
	@unittest.skip('TODO')
	def test_additional_payloads_added_in_remote(self):
		self.fail()
	
	@unittest.skip('TODO')
	def test_additional_payloads_changed_in_remote(self):
		self.fail()
	
	@unittest.skip('TODO')
	def test_additional_payloads_removed_in_remote(self):
		self.fail()


class ReadFromStorageWriteToMemoryPayloadTest(unittest.TestCase):
	def test_read(self):
		original_reader = lambda: io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA)
		payload = ReadFromStorageWriteToMemoryPayload(
				name=DEFAULT_HTML_PAYLOAD_NAME,
				original_reader=original_reader,
				original_md5hash=DEFAULT_HTML_PAYLOAD_HASH,
				)
		
		self.assertEqual(DEFAULT_HTML_PAYLOAD_DATA, payload.open(mode='r').read())
		self.assertEqual(DEFAULT_HTML_PAYLOAD_HASH, payload.get_md5hash())
	
	def test_write(self):
		original_reader = lambda: io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA)
		payload = ReadFromStorageWriteToMemoryPayload(
				name=DEFAULT_HTML_PAYLOAD_NAME,
				original_reader=original_reader,
				original_md5hash=DEFAULT_HTML_PAYLOAD_HASH,
				)
		
		with payload.open(mode='w') as f:
			f.write(DEFAULT_PNG_PAYLOAD_DATA)
		
		self.assertEqual(DEFAULT_PNG_PAYLOAD_DATA, payload.open(mode='r').read())
		self.assertEqual(DEFAULT_PNG_PAYLOAD_HASH, payload.get_md5hash())
	
	def test_reset(self):
		original_reader = lambda: io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA)
		payload = ReadFromStorageWriteToMemoryPayload(
				name=DEFAULT_HTML_PAYLOAD_NAME,
				original_reader=original_reader,
				original_md5hash=DEFAULT_HTML_PAYLOAD_HASH,
				)
		
		with payload.open(mode='w') as f:
			f.write(DEFAULT_PNG_PAYLOAD_DATA)
		payload.reset()
		
		self.assertEqual(DEFAULT_HTML_PAYLOAD_DATA, payload.open(mode='r').read())
		self.assertEqual(DEFAULT_HTML_PAYLOAD_HASH, payload.get_md5hash())


class FolderNodeTest:#(unittest.TestCase): # TODO
	def test_load_folder_node(self):
		"""Test loading a folder node."""
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_FOLDER,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						CREATED_TIME_ATTRIBUTE: DEFAULT_CREATED_TIMESTAMP,
						MODIFIED_TIME_ATTRIBUTE: DEFAULT_MODIFIED_TIMESTAMP,
						ORDER_ATTRIBUTE: DEFAULT_ORDER,
						ICON_NORMAL_ATTRIBUTE: DEFAULT_ICON_NORMAL,
						ICON_OPEN_ATTRIBUTE: DEFAULT_ICON_OPEN,
						TITLE_COLOR_FOREGROUND_ATTRIBUTE: DEFAULT_TITLE_COLOR_FOREGROUND,
						TITLE_COLOR_BACKGROUND_ATTRIBUTE: DEFAULT_TITLE_COLOR_BACKGROUND,
						},
				payloads=[]
				)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), FolderNodeDao() ])
		
		dao.sync()
		
		# Verify the node.
		node = [child for child in notebook.root.get_children() if child.node_id == DEFAULT_ID][0]
		self.assertEqual(FolderNode, node.__class__)
		self.assertEqual(DEFAULT_ID, node.node_id)
		self.assertEqual(CONTENT_TYPE_FOLDER, node.content_type)
		self.assertEqual(DEFAULT_TITLE, node.title)
		self.assertEqual(DEFAULT_CREATED_TIME, node.created_time)
		self.assertEqual(DEFAULT_MODIFIED_TIME, node.modified_time)
		self.assertEqual(DEFAULT_ORDER, node.order)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		self.assertEqual(False, node.is_dirty)
	
	def test_load_folder_node_missing_title(self):
		"""Test loading a folder node without a title."""
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_FOLDER,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						},
				payloads=[]
				)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), FolderNodeDao() ])
		
		dao.sync()
		
		# Verify the node.
		node = notebook.root
		self.assertIsNotNone(node.title)	
	

class TrashNodeTest:#(unittest.TestCase): # TODO
	def test_load_trash_node(self):
		"""Test loading a trash node."""
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_TRASH,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						TITLE_ATTRIBUTE: DEFAULT_TITLE,
						CREATED_TIME_ATTRIBUTE: DEFAULT_CREATED_TIMESTAMP,
						MODIFIED_TIME_ATTRIBUTE: DEFAULT_MODIFIED_TIMESTAMP,
						ORDER_ATTRIBUTE: DEFAULT_ORDER,
						ICON_NORMAL_ATTRIBUTE: DEFAULT_ICON_NORMAL,
						ICON_OPEN_ATTRIBUTE: DEFAULT_ICON_OPEN,
						TITLE_COLOR_FOREGROUND_ATTRIBUTE: DEFAULT_TITLE_COLOR_FOREGROUND,
						TITLE_COLOR_BACKGROUND_ATTRIBUTE: DEFAULT_TITLE_COLOR_BACKGROUND,
						},
				payloads=[]
				)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), TrashNodeDao() ])
		
		dao.sync()
		
		# Verify the node.
		node = notebook.trash
		self.assertEqual([child for child in notebook.root.children if child.node_id == DEFAULT_ID][0], node)
		self.assertEqual(TrashNode, node.__class__)
		self.assertEqual(DEFAULT_ID, node.node_id)
		self.assertEqual(CONTENT_TYPE_TRASH, node.content_type)
		self.assertEqual(DEFAULT_TITLE, node.title)
		self.assertEqual(DEFAULT_CREATED_TIME, node.created_time)
		self.assertEqual(DEFAULT_MODIFIED_TIME, node.modified_time)
		self.assertEqual(DEFAULT_ORDER, node.order)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		self.assertEqual(False, node.is_dirty)
	
	def test_load_trash_node_missing_title(self):
		"""Test loading a trash node without a title."""
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_storage_node(notebook_storage, ROOT_SN)
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_TRASH,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						},
				payloads=[]
				)
		notebook = Notebook()
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), TrashNodeDao() ])
		
		dao.sync()
		
		# Verify the node.
		node = notebook.root
		self.assertIsNotNone(node.title)


class TestNotebookNodeDao(NotebookNodeDao):
	def accepts(self, content_type):
		return content_type == CONTENT_TYPE_TEST
	
	def nn_to_sn(self, nn):
		attributes = {
				TITLE_ATTRIBUTE: nn.title,
				}
		if nn.parent is not None:
			attributes[PARENT_ID_ATTRIBUTE] = nn.parent.node_id
		
		return StoredNode(nn.node_id, nn.content_type, attributes, [])
	
	def sn_to_nn(self, sn, notebook_storage, notebook):
		return TestNotebookNode(
				notebook_storage=notebook_storage,
				notebook=notebook,
				parent=None,
				loaded_from_storage=True,
				title=sn.attributes[TITLE_ATTRIBUTE],
				node_id=sn.node_id,
				)

# -*- coding: utf-8 -*-

import base64
from datetime import datetime
import io
import os
from pytz import utc
import unittest

from keepnote.notebooknew import Notebook, NotebookNode, ContentNode, FolderNode, TrashNode, IllegalOperationError
from keepnote.notebooknew import CONTENT_TYPE_HTML, CONTENT_TYPE_TRASH, CONTENT_TYPE_FOLDER
from keepnote.notebooknew import new_node_id
from keepnote.notebooknew.dao import *
import keepnote.notebooknew.storage as storage
from keepnote.notebooknew.storage import StoredNode

CONTENT_TYPE_TEST = u'application/x-notebook-test-node'

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

DEFAULT=object()
DEFAULT_ID = 'my_id'
DEFAULT_CONTENT_TYPE = CONTENT_TYPE_HTML
DEFAULT_TITLE = 'my_title'
DEFAULT_CREATED_TIMESTAMP = 1012615322
DEFAULT_CREATED_TIME = datetime.fromtimestamp(DEFAULT_CREATED_TIMESTAMP, tz=utc)
DEFAULT_MODIFIED_TIMESTAMP = 1020000000
DEFAULT_MODIFIED_TIME = datetime.fromtimestamp(DEFAULT_MODIFIED_TIMESTAMP, tz=utc)
DEFAULT_ORDER = 12
DEFAULT_ICON_NORMAL = 'node_red_closed.png'
DEFAULT_ICON_OPEN = 'node_red_open.png'
DEFAULT_TITLE_COLOR_FOREGROUND = '#ffffff'
DEFAULT_TITLE_COLOR_BACKGROUND = '#ff0000'
DEFAULT_PAYLOAD_NAMES = ['my_payload1', 'my_payload2']
DEFAULT_HTML_PAYLOAD_NAME = os.path.basename('index.html')
DEFAULT_HTML_PAYLOAD = base64.b64decode('PCFET0NUWVBFIGh0bWw+DQoNCjxoMT5UZXN0IE5vZGU8L2gxPg0KPHA+VGhpcyBpcyBhIG5vZGUgdXNlZCBmb3IgdGVzdGluZy48L3A+DQo=')
DEFAULT_PNG_PAYLOAD_NAME = os.path.basename('image1.png')
DEFAULT_PNG_PAYLOAD = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAACAAAAArCAIAAACW3x1gAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAYdEVYdFNvZnR3YXJlAHBhaW50Lm5ldCA0LjAuNWWFMmUAAAWNSURBVFhHrZdZSJVbFMdPYC+ZFKQvolKkZWqa10pIozIaMH1QKSsVUbPBMKciCSrLsCIVnPA6oA8WXIu8ZYUQKikqVwK7zTRro5Y2mGk4nfvz7O139Zzv6Dnd+3s4rPXt/Z3/ntZa+9NodbS1td2+ffvu3bvnz58/efJkZmbmzp07a2trMU6dOlVVVbVr167g4GD6iP6moxkdHQ0PD1+yZMncuXPnzJnj7u6O7efnFxkZqRln3rx5ixcvxpg/f758z2Q0WVlZCxYsEH80Y8aMhQsXWlhYuLm5paennzlz5ty5c4WFhdglJSXNzc379++X75mM5vjx42fPnv1Lx5MnT+RjNX78+MHMEBsaGsLlt6urSzRNgSY+Pp6hSW9KLly4wBRTUlKGh4dx169fz6Tr6upEqzE069atk+Z0sFs+Pj6XLl2qqKioqak5ffo0k379+rVsNoKpAp8/f161atWRI0f+HufatWtRUVFFRUViQsbQF2CY7e3tjx8/HhkZkY90BAYGNjY2SmcCrDBTkY4akwQYF6fTyspq9uzZ0dHR7Kp4jl5oaKiw9fj586eDgwO/0jfgX4H6+vrly5c/evQIm+FnZ2d//fpVNOXl5bW0tAibkHz16hWzBPGEYCQShW2IFGCvFi1adPny5T91XL9+XTQLWH1loVn6/Pz8Y8eOJSYmiif37t1LTU0VtiFjAqz7smXLrl69SlaIi4vjqHAW+/r6ZBet1tvbW1pqIJCQkCAdA8YEWOLVq1cL//v37+ynsBX0nih7IyguLmZA0jFgTICkxgxEfA4ODuqtD9CqHKovX76sXLlS2II9e/YYvqIwJtDR0WFpaUnmERrAv1RXVwsbAgICrly5Iuzk5GRSHqsqXI6GjY3NFKEgN5k42rBhg729fWxsrLOzc0RExMQQpXXjxo1btmzhr9mhoKCggwcPkrpPnDjBmeZoyH5qSAHBp0+f3r9/P3F7FRgjTUTDhw8fPn78GBYWtl0Hp1b20C0vffRiYpKAId++fWtqapKOVktuYPWko4M/JQeTxqki/v7+HAcnJydKFi+KDlMJPHz4kP08evSo9CcI9PT03Lx5k/9l/w8dOkS1GBgYEH2QJBu6urreunUL16gAC8W/s8oTdxsBAo2VoSJxeB48eCAbDHjz5s2sWbNQNSrAaSEBUF7evn2Lyx6UlZUx/RUrVtCkuk965OTklJeXqws0NDRwkDBCQkKEAAfp8OHDlDDlgE5LZ2fn5s2bVQT6+/sZaW9vLzarLASAIBcPTWfHjh0qAklJSaQzYZNHlUJNoiUUbty4IVxTWLt2rb4AS+Hp6akcsosXL3LtEDawyZRiouHZs2fykXH27dtHBdQXSEtLKygokI4uZ9BBSSEIMILKysqlS5cibGzFCHKiXVQ6fQFqDkXtNx3c5l68eEGm5GiKViUOqEUIMFc60+H3cejAxvLinTt3xCsallVYQJRbW1u3traSM3CfP3/u4eHB0lMP2HmeKAIKHCri8Y9xyJuyYZyxi5dyLyLRc0Xkoufr68vQeCLigDXZu3cvrqHAtGgoRkq2efr0KVdHVhm7tLSU4Nq0aRMCDJOUuW3bNjKumIrpjM1AESA+Z86cuXv37tzcXIo+KfPAgQNKZNHKPVXYpjNJgCG7uLiQxUgSYG5YqTJJADi5fCJI5/9AExMT8/LlS+np7i+Ojo7379+X/n9GJVVwYbazs5v22mwiKgLA0WaHqc+EAi5XOaoCtUXvwmIKU30VUU+4wXFro6gRmSIyzEV9BqpQG6RlDqYKUALXrFkjHXMwQ0DUOHPRkFelOSW/LkAy8PLy4vNRYevWrRkZGZRlePfunej36wJczSgyXDH5vMHv7u7GBmoZQc73vq2tLV+TpHG+lsQ7ZqDV/gOanoppyROYaQAAAABJRU5ErkJggg==')
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
ROOT_SN = StoredNode('root_id', CONTENT_TYPE_TEST, attributes={TITLE_ATTRIBUTE: 'root'}, payload_names=[])
CHILD1_SN = StoredNode('child1_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child1'}, payload_names=[])
CHILD11_SN = StoredNode('child11_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child11'}, payload_names=[])
CHILD12_SN = StoredNode('child12_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child12'}, payload_names=[])
CHILD121_SN = StoredNode('child121_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child12_id', TITLE_ATTRIBUTE: 'child121'}, payload_names=[])
CHILD2_SN = StoredNode('child2_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child2'}, payload_names=[])
CHILD21_SN = StoredNode('child21_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child2_id', TITLE_ATTRIBUTE: 'child21'}, payload_names=[])
TRASH_SN = StoredNode('trash_id', CONTENT_TYPE_TRASH, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'trash'}, payload_names=[])

def add_stored_node(notebook_storage, sn):
	notebook_storage.add_node(
			node_id=sn.node_id,
			content_type=sn.content_type,
			attributes=sn.attributes,
			payloads=[]
			)
	
def datetime_to_timestamp(dt):
	# From https://docs.python.org/3.3/library/datetime.html#datetime.datetime.timestamp
	return (dt - datetime(1970, 1, 1, tzinfo=utc)).total_seconds()

class StructureTest(unittest.TestCase):
	def test_new_in_remote_only_root(self):
		notebook_storage = storage.mem.InMemoryStorage()
		add_stored_node(notebook_storage, ROOT_SN)
		notebook = Notebook(notebook_storage=None)
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
		add_stored_node(notebook_storage, ROOT_SN)
		add_stored_node(notebook_storage, CHILD1_SN)
		add_stored_node(notebook_storage, CHILD2_SN)
		add_stored_node(notebook_storage, TRASH_SN)
		notebook = Notebook(notebook_storage=None)
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
		add_stored_node(notebook_storage, ROOT_SN)
		add_stored_node(notebook_storage, CHILD1_SN)
		add_stored_node(notebook_storage, CHILD11_SN)
		add_stored_node(notebook_storage, CHILD12_SN)
		add_stored_node(notebook_storage, CHILD121_SN)
		add_stored_node(notebook_storage, CHILD2_SN)
		add_stored_node(notebook_storage, CHILD21_SN)
		add_stored_node(notebook_storage, TRASH_SN)
		notebook = Notebook(notebook_storage=None)
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
	
	def test_new_in_remote_stored_nodes_postordered(self):
		"""Test the NotebookNode structure with multiple levels of nodes, if the backing NotebookStorage.get_all_nodes()
		returns the StoredNotes in another order. In this case, the order achieved when traversing the tree depth-first
		left-to-right post-order."""
		self.maxDiff=None
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_stored_node(notebook_storage, TRASH_SN)
		add_stored_node(notebook_storage, CHILD21_SN)
		add_stored_node(notebook_storage, CHILD2_SN)
		add_stored_node(notebook_storage, CHILD121_SN)
		add_stored_node(notebook_storage, CHILD12_SN)
		add_stored_node(notebook_storage, CHILD11_SN)
		add_stored_node(notebook_storage, CHILD1_SN)
		add_stored_node(notebook_storage, ROOT_SN)
		notebook = Notebook(notebook_storage=None)
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
		add_stored_node(notebook_storage, ROOT_SN)
		add_stored_node(notebook_storage, CHILD1_SN)
		add_stored_node(notebook_storage, CHILD11_SN)
		add_stored_node(notebook_storage, CHILD2_SN)
		add_stored_node(notebook_storage, TRASH_SN)
		notebook = Notebook(notebook_storage=None)
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
		root1_sn = StoredNode('root1_id', CONTENT_TYPE_TEST, attributes={}, payload_names=[])
		root2_sn = StoredNode('root2_id', CONTENT_TYPE_TEST, attributes={}, payload_names=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_stored_node(notebook_storage, root1_sn)
		add_stored_node(notebook_storage, root2_sn)
		notebook = Notebook(notebook_storage=None)
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()
	
	def test_validation_unknown_parent(self):
		"""Test a NotebookStorage with a root and a node that references an unknown parent."""
		child_sn = StoredNode('child_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'unknown_id'}, payload_names=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_stored_node(notebook_storage, ROOT_SN)
		add_stored_node(notebook_storage, child_sn)
		notebook = Notebook(notebook_storage=None)
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()
	
	def test_validation_parent_is_node_a_child(self):
		"""Test a NotebookStorage with a root and a node that is its own parent."""
		child_sn = StoredNode('child_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'child_id'}, payload_names=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_stored_node(notebook_storage, ROOT_SN)
		add_stored_node(notebook_storage, child_sn)
		notebook = Notebook(notebook_storage=None)
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()
	
	def test_validation_cycle_no_root(self):
		"""Test a NotebookStorage with a cycle and no root."""
		cycle_node1_sn = StoredNode('cycle_node1_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node2_id'}, payload_names=[])
		cycle_node2_sn = StoredNode('cycle_node2_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node1_id'}, payload_names=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_stored_node(notebook_storage, cycle_node1_sn)
		add_stored_node(notebook_storage, cycle_node2_sn)
		notebook = Notebook(notebook_storage=None)
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()
	
	def test_validation_cycle_with_root(self):
		"""Test a NotebookStorage with a root and a cycle."""
		cycle_node1_sn = StoredNode('cycle_node1_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node3_id'}, payload_names=[])
		cycle_node2_sn = StoredNode('cycle_node2_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node1_id'}, payload_names=[])
		cycle_node3_sn = StoredNode('cycle_node3_id', CONTENT_TYPE_TEST, attributes={PARENT_ID_ATTRIBUTE: 'cycle_node2_id'}, payload_names=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_stored_node(notebook_storage, ROOT_SN)
		add_stored_node(notebook_storage, CHILD1_SN)
		add_stored_node(notebook_storage, cycle_node1_sn)
		add_stored_node(notebook_storage, cycle_node2_sn)
		add_stored_node(notebook_storage, cycle_node3_sn)
		notebook = Notebook(notebook_storage=None)
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()

	def test_validation_two_trashes(self):
		"""Test a NotebookStorage with two trashes."""
		trash1_sn = StoredNode('trash1_id', CONTENT_TYPE_TRASH, attributes={}, payload_names=[])
		trash2_sn = StoredNode('trash2_id', CONTENT_TYPE_TRASH, attributes={}, payload_names=[])
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_stored_node(notebook_storage, ROOT_SN)
		add_stored_node(notebook_storage, trash1_sn)
		add_stored_node(notebook_storage, trash2_sn)
		notebook = Notebook(notebook_storage=None)
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
		add_stored_node(notebook_storage, ROOT_SN)
		add_stored_node(notebook_storage, CHILD1_SN)
		add_stored_node(notebook_storage, CHILD2_SN)
		notebook = Notebook(notebook_storage=None)
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
		add_stored_node(notebook_storage, ROOT_SN)
		add_stored_node(notebook_storage, CHILD1_SN)
		add_stored_node(notebook_storage, CHILD2_SN)
		notebook = Notebook(notebook_storage=None)
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao()])
		dao.sync()
		self.assertEqual(3, len(list(notebook._traverse_tree())))
		notebook_storage.remove_node(CHILD2_SN.node_id)
		
		dao.sync()
		
		self.assertEqual(2, len(list(notebook_storage.get_all_nodes())))
		self.assertEqual(False, notebook_storage.has_node(CHILD2_SN.node_id))
		self.assertEqual(False, notebook.has_node(CHILD2_SN.node_id))

class ContentNodeTest(unittest.TestCase):
	def test_load_content_node(self):
		"""Test loading a content node."""
		notebook_storage = storage.mem.InMemoryStorage()
		add_stored_node(notebook_storage, ROOT_SN)
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
						(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD)),
						(DEFAULT_PNG_PAYLOAD_NAME, io.BytesIO(DEFAULT_PNG_PAYLOAD))
						]
				)
		notebook = Notebook(notebook_storage=None)
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), ContentNodeDao() ])
		
		dao.sync()
		
		# Verify the node.
		node = [child for child in notebook.root.get_children() if child.node_id == DEFAULT_ID][0]
		self.assertEqual(ContentNode, node.__class__)
		self.assertEqual(DEFAULT_ID, node.node_id)
		self.assertEqual(CONTENT_TYPE_HTML, node.content_type)
		self.assertEqual(DEFAULT_TITLE, node.title)
		self.assertEqual(DEFAULT_CREATED_TIME, node.created_time)
		self.assertEqual(DEFAULT_MODIFIED_TIME, node.modified_time)
		self.assertEqual(DEFAULT_ORDER, node.order)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		self.assertEqual(DEFAULT_HTML_PAYLOAD_NAME, node.main_payload_name)
		self.assertEqual([DEFAULT_PNG_PAYLOAD_NAME], node.additional_payload_names)
		self.assertEqual(False, node.is_dirty)
	
	def test_load_content_node_missing_title(self):
		"""Test loading a content node without a title."""
		
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_HTML,
				attributes={
						MAIN_PAYLOAD_NAME_ATTRIBUTE: DEFAULT_HTML_PAYLOAD_NAME,
						},
				payloads=[(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD))]
				)
		notebook = Notebook(notebook_storage=None)
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), ContentNodeDao() ])
		
		dao.sync()
		
		# Verify the node.
		node = notebook.root
		self.assertIsNotNone(node.title)
	
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
		notebook = Notebook(notebook_storage=None)
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
				payloads=[(DEFAULT_HTML_PAYLOAD_NAME, io.BytesIO(DEFAULT_HTML_PAYLOAD))]
				)
		notebook = Notebook(notebook_storage=None)
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
				payloads=[(DEFAULT_PNG_PAYLOAD_NAME, io.BytesIO(DEFAULT_PNG_PAYLOAD))]
				)
		notebook = Notebook(notebook_storage=None)
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), ContentNodeDao() ])
		
		with self.assertRaises(InvalidStructureError):
			dao.sync()


class FolderNodeTest(unittest.TestCase):
	def test_load_folder_node(self):
		"""Test loading a folder node."""
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_stored_node(notebook_storage, ROOT_SN)
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
		notebook = Notebook(notebook_storage=None)
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
		add_stored_node(notebook_storage, ROOT_SN)
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_FOLDER,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						},
				payloads=[]
				)
		notebook = Notebook(notebook_storage=None)
		dao = Dao(notebook, notebook_storage, [ TestNotebookNodeDao(), FolderNodeDao() ])
		
		dao.sync()
		
		# Verify the node.
		node = notebook.root
		self.assertIsNotNone(node.title)	
	

class TrashNodeTest(unittest.TestCase):
	def test_load_trash_node(self):
		"""Test loading a trash node."""
		
		notebook_storage = storage.mem.InMemoryStorage()
		add_stored_node(notebook_storage, ROOT_SN)
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
		notebook = Notebook(notebook_storage=None)
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
		add_stored_node(notebook_storage, ROOT_SN)
		notebook_storage.add_node(
				node_id=DEFAULT_ID,
				content_type=CONTENT_TYPE_TRASH,
				attributes={
						PARENT_ID_ATTRIBUTE: ROOT_SN.node_id,
						},
				payloads=[]
				)
		notebook = Notebook(notebook_storage=None)
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
# 				ICON_NORMAL_ATTRIBUTE: nn.icon_normal,
# 				ICON_OPEN_ATTRIBUTE: nn.icon_open,
# 				CLIENT_PREFERENCES_ATTRIBUTE: self.client_preferences._data,
				}
		if nn.parent is not None:
			attributes[PARENT_ID_ATTRIBUTE] = nn.parent.node_id
# 		if nn.created_time is not None:
# 			attributes[CREATED_TIME_ATTRIBUTE] = datetime_to_timestamp(nn.created_time)
# 		if nn.modified_time is not None:
# 			attributes[MODIFIED_TIME_ATTRIBUTE] = datetime_to_timestamp(nn.modified_time)
		
		return StoredNode(nn.node_id, nn.content_type, attributes, [])
	
	def sn_to_nn(self, sn, notebook_storage, notebook):
		return TestNotebookNode(
				notebook_storage=notebook_storage,
				notebook=notebook,
				parent=None,
				loaded_from_storage=True,
				title='',
# 				order=order,
# 				icon_normal=icon_normal,
# 				icon_open=icon_open,
# 				title_color_foreground=title_color_foreground,
# 				title_color_background=title_color_background,
				node_id=sn.node_id,
# 				created_time=created_time,
# 				modified_time=modified_time,
				)

class TestNotebookNode(NotebookNode):
	"""A testing implementation of NotebookNode."""

	def __init__(self, notebook_storage=None, notebook=None, parent=None, add_to_parent=None, loaded_from_storage=True, title=DEFAULT_TITLE, node_id=None):
		if node_id is None:
			node_id = new_node_id()
		super(TestNotebookNode, self).__init__(
				notebook_storage=notebook_storage,
				notebook=notebook,
				content_type=u'application/x-notebook-test',
				parent=parent,
				loaded_from_storage=loaded_from_storage,
				title=title,
				node_id=node_id,
				)
		
		self._is_deleted = False
		self._is_dirty = False
		self._is_in_trash = False
		
		if self.parent is not None:
			if add_to_parent is None:
				raise IllegalOperationError('Please pass add_to_parent')
			elif add_to_parent == True:
				self.parent._add_child_node(self)
	
	def delete(self):
		if self.parent is None:
			raise IllegalOperationError('Cannot delete the root node')
		for child in self._children:
			child.delete()
		self.is_deleted = True
		if NotebookNode.NEW in self._unsaved_changes:
			self.parent._remove_child_node(self)
			self._unsaved_changes.remove(NotebookNode.NEW)
		else:
			self._unsaved_changes.add(NotebookNode.DELETED)
	
	@property
	def is_dirty(self):
		return self._is_dirty
	
	@property
	def is_in_trash(self):
		return False
	
	@property
	def is_root(self):
		"""TODO"""
		raise NotImplementedError('TODO')
	
	@property
	def is_trash(self):
		return False
	
	def set_is_deleted(self, value):
		self.is_deleted = value
	
	def set_is_dirty(self, value):
		self._is_dirty = value
	
	def set_is_in_trash(self, value):
		self._is_in_trash = value

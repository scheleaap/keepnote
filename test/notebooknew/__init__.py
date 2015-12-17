
# -*- coding: utf-8 -*-
import base64
import copy
from datetime import datetime
#from hamcrest import *
import io
import mock
from mock import Mock, call
import os
from pytz import utc
import re
from time import sleep
import unittest

from keepnote.notebooknew import *
from keepnote.notebooknew import CONTENT_TYPE_HTML, CONTENT_TYPE_TRASH, CONTENT_TYPE_FOLDER
from keepnote.notebooknew import new_node_id
import keepnote.notebooknew.storage as storage
from keepnote.notebooknew.storage import StoredNode
import keepnote.notebooknew.storage.mem
from keepnote.pref import Pref
from xml.dom import NodeFilter
from ast import NodeVisitor
from lib2to3.tests.test_pytree import TestNodes
from test.notebooknew.dao import DEFAULT_CLIENT_PREFERENCES

MS = 0.001  # 1 millisecond in seconds

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
DEFAULT_CLIENT_PREFERENCES = { 'test': { 'key': 'value' }}
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
ROOT_SN = StoredNode('root_id', CONTENT_TYPE_FOLDER, attributes={TITLE_ATTRIBUTE: 'root'}, payload_names=[])
CHILD1_SN = StoredNode('child1_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child1'}, payload_names=[])
CHILD11_SN = StoredNode('child11_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child11'}, payload_names=[])
CHILD12_SN = StoredNode('child12_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child12'}, payload_names=[])
CHILD121_SN = StoredNode('child121_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child12_id', TITLE_ATTRIBUTE: 'child121'}, payload_names=[])
CHILD2_SN = StoredNode('child2_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child2'}, payload_names=[])
CHILD21_SN = StoredNode('child21_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child2_id', TITLE_ATTRIBUTE: 'child21'}, payload_names=[])
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

class NotebookTest(unittest.TestCase):
	@unittest.skip('TODO: MIGRATE')
	def test_load_notebook(self):
		"""Test loading a notebook."""
		
		# Initialize a NotebookStorage.
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		notebook_storage.add_node(TRASH_SN.node_id, TRASH_SN.content_type, TRASH_SN.attributes, [])
		
		# Initialize Notebook with the NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the Notebook.
		self.assertEqual(False, notebook.is_dirty)
	
	@unittest.skip('TODO: MIGRATE')
	def test_root_created_in_empty_storage(self):
		"""Test if a root is created if the NotebookStorage is empty."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		node = notebook.root
		self.assertIsNotNone(node)
		self.assertEqual(CONTENT_TYPE_FOLDER, node.content_type)
		
		# Verify the notebook.
		self.assertEqual(True, notebook.is_dirty) 
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.add_node.called)
	
	@unittest.skip('TODO: MIGRATE')
	def test_trash_created_if_missing(self):
		"""Test if a trash is created in a NotebookStorage without one."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN]
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		# Verify the node.
		node = notebook.trash
		self.assertEqual(CONTENT_TYPE_TRASH, node.content_type)
		self.assertEqual(notebook.root, node.parent)
		# TODO: Title?
		
		# Verify the notebook.
		self.assertEqual(True, notebook.is_dirty) 
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.add_node.called)
	
	def test_client_preferences(self):
		"""Test the setting and getting of Notebook client preferences."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		
		# Initialize Notebook with the mocked NotebookStorage.
		notebook = Notebook(notebook_storage)
		
		expected = Pref()
		self.assertEqual(expected, notebook.client_preferences)
		
		notebook.client_preferences.get('test', 'key', define=True)
		notebook.client_preferences.set('test', 'key', 'value')
		
		expected = Pref()
		expected.get('test', 'key', define=True)
		expected.set('test', 'key', 'value')
		self.assertEqual(expected, notebook.client_preferences)
	
	@unittest.skip('TODO: MIGRATE')
	def test_save_without_changes(self):
		notebook_storage = storage.mem.InMemoryStorage()
		notebook_storage.add_node(ROOT_SN.node_id, ROOT_SN.content_type, ROOT_SN.attributes, [])
		notebook_storage.add_node(TRASH_SN.node_id, TRASH_SN.content_type, TRASH_SN.attributes, [])
		notebook = Notebook(notebook_storage)
		
		self.assertEqual(False, notebook.is_dirty)
		notebook.save()
		
		self.assertEqual(2, len(list(notebook_storage.get_all_nodes())))
	
	def test_close_without_changes(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		handler = Mock()
		
		notebook = Notebook(notebook_storage)
		notebook.closing_listeners.add(handler.on_closing)
		notebook.close_listeners.add(handler.on_close)
		
		notebook.close()
		
		handler.assert_has_calls([call.on_closing(), call.on_close()])
	
	# TODO: Consider making the desktop client responsible for saving before closing.
	@unittest.skip('TODO: MIGRATE')
	def test_close_with_changes(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = [ROOT_SN, TRASH_SN]
		handler = Mock()
		root_mock = Mock()
		root_mock.handler = handler
		root_mock.notebook_storage = notebook_storage
		
		notebook = Notebook(notebook_storage)
		notebook.root.new_folder_child_node(DEFAULT_TITLE)
		notebook.closing_listeners.add(handler.on_closing)
		notebook.close_listeners.add(handler.on_close)
		
		notebook.close()
		
		root_mock.assert_has_calls([
				call.handler.on_closing(),
				call.notebook_storage.add_node(node_id=mock.ANY, content_type=mock.ANY, attributes=mock.ANY, payloads=mock.ANY),
				call.handler.on_close()
				])
	
	@unittest.skip('TODO')
	def test_node_changed_event(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		handler = Mock()
		
		notebook = Notebook(notebook_storage)
		notebook.node_changed_listeners.add(handler.on_node_change)
		
		self.fail('TODO');
	
	def get_client_event_listeners(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		notebook_storage.get_all_nodes.return_value = []
		handler = Mock()
		
		notebook = Notebook(notebook_storage)
		notebook.get_client_event_listeners("my-event").add(handler.on_event)
	
	def test_has_node(self):
		root = TestNotebookNode()
		child1 = TestNotebookNode(parent=root, add_to_parent=True)
		child11 = TestNotebookNode(parent=child1, add_to_parent=True)
		child12 = TestNotebookNode(parent=child1, add_to_parent=True)
		child121 = TestNotebookNode(parent=child12, add_to_parent=True)
		notebook = Notebook()
		notebook.root = root

		self.assertEqual(True, notebook.has_node(root.node_id))
		self.assertEqual(True, notebook.has_node(child1.node_id))
		self.assertEqual(True, notebook.has_node(child11.node_id))
		self.assertEqual(True, notebook.has_node(child12.node_id))
		self.assertEqual(True, notebook.has_node(child121.node_id))
		self.assertEqual(False, notebook.has_node('other_id'))
	
	def test_find_node_by_id(self):
		root = TestNotebookNode()
		child1 = TestNotebookNode(parent=root, add_to_parent=True)
		child11 = TestNotebookNode(parent=child1, add_to_parent=True)
		child12 = TestNotebookNode(parent=child1, add_to_parent=True)
		child121 = TestNotebookNode(parent=child12, add_to_parent=True)
		notebook = Notebook()
		notebook.root = root

		self.assertEqual(root, notebook.get_node_by_id(root.node_id))
		self.assertEqual(child1, notebook.get_node_by_id(child1.node_id))
		self.assertEqual(child11, notebook.get_node_by_id(child11.node_id))
		self.assertEqual(child12, notebook.get_node_by_id(child12.node_id))
		self.assertEqual(child121, notebook.get_node_by_id(child121.node_id))
		with self.assertRaises(NodeDoesNotExistError):
			notebook.get_node_by_id('other_id')
		

class ContentFolderTrashNodeTestBase(object):
	def _create_node(
			self,
			notebook_storage=None,
			notebook=None,
			parent=None,
			loaded_from_storage=False,
			title=DEFAULT_TITLE,
			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			client_preferences=DEFAULT_CLIENT_PREFERENCES,
			node_id=DEFAULT,
			created_time=DEFAULT,
			modified_time=DEFAULT,
			):
		"""Creates a node of the class under test."""
		raise NotImplementedError()
	
	def _assert_proper_copy_call_on_mock(self, target_mock, original, behind):
		"""Asserts that the proper method to copy a node of the class under test was invoked on a target mock object."""
		raise NotImplementedError()
	
	def _get_proper_copy_method(self, target_mock):
		"""Returns the proper method to copy a node of the class under test on a mock object."""
		raise NotImplementedError()
	
	def test_create_new_n(self):
		parent = TestNotebookNode()
		
		node = self._create_node(
				parent=parent,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				order=DEFAULT_ORDER,
				icon_normal=DEFAULT_ICON_NORMAL,
				icon_open=DEFAULT_ICON_OPEN,
				title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
				title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
				client_preferences=DEFAULT_CLIENT_PREFERENCES,
				)
		
		self.assertEqual(AnyUuidMatcher(), node.node_id)
		self.assertEqual(parent, node.parent)
# 		self.assertEqual(DEFAULT_TITLE, node.title)
# 		self.assertEqual(True, abs((datetime.now() - node.created_time).total_seconds()) < 1)
# 		self.assertEqual(node.created_time, node.modified_time)
		self.assertEqual(DEFAULT_ORDER, node.order)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		self.assertEqual(Pref(DEFAULT_CLIENT_PREFERENCES), node.client_preferences)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
		self.assertEqual(False, node.has_children())
		self.assertEqual([], node.children)
		repr(node)
		
	def test_create_from_storage_n(self):
		parent = TestNotebookNode()
		
		node = self._create_node(
				parent=parent,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				order=DEFAULT_ORDER,
				icon_normal=DEFAULT_ICON_NORMAL,
				icon_open=DEFAULT_ICON_OPEN,
				title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
				title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
				client_preferences=DEFAULT_CLIENT_PREFERENCES,
				node_id=DEFAULT_ID,
				created_time=DEFAULT_CREATED_TIME,
				modified_time=DEFAULT_MODIFIED_TIME,
				)
		
		self.assertEqual(DEFAULT_ID, node.node_id)
		self.assertEqual(parent, node.parent)
# 		self.assertEqual(DEFAULT_TITLE, node.title)
# 		self.assertEqual(DEFAULT_CREATED_TIME, node.created_time)
# 		self.assertEqual(DEFAULT_MODIFIED_TIME, node.modified_time)
		self.assertEqual(DEFAULT_ORDER, node.order)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		self.assertEqual(Pref(DEFAULT_CLIENT_PREFERENCES), node.client_preferences)
		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
		self.assertEqual(False, node.has_children())
		self.assertEqual([], node.children)
		repr(node)
	
	def test_constructor_parameters_new_n1(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			self._create_node(
					loaded_from_storage=False,
					node_id='12345',  # Must be None if not loaded from storage
					)
	
	def test_constructor_parameters_new_n2(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			self._create_node(
					loaded_from_storage=False,
					created_time=datetime.now(),  # Must be None if not loaded from storage
					)
	
	def test_constructor_parameters_new_n3(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			self._create_node(
					loaded_from_storage=False,
					modified_time=datetime.now(),  # Must be None if not loaded from storage
					)
	
	def test_constructor_parameters_from_storage_n1(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			self._create_node(
					loaded_from_storage=True,
					node_id=None,  # Must not be None if loaded from storage
					)
	
	def test_notebook_storage_attributes_parent_id(self):
		parent = TestNotebookNode()
		node = self._create_node(parent=parent)
		
		self.assertEqual(parent.node_id, node._notebook_storage_attributes[PARENT_ID_ATTRIBUTE])
	
	def test_notebook_storage_attributes_title(self):
		node = self._create_node()
		node.title = 'new title'
		
		self.assertEqual('new title', node._notebook_storage_attributes[TITLE_ATTRIBUTE])
	
	@unittest.skip('TODO Werkt niet meer en gaat sowieso weg')
	def test_notebook_storage_attributes_client_preferences(self):
		node = self._create_node()
		node.client_preferences.set('custom_value', True)
		
		self.assertEqual({ 'custom_value': True }, node._notebook_storage_attributes[CLIENT_PREFERENCES_ATTRIBUTE])
		
	def test_is_root_1(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		self.assertEqual(True, node.is_root)
	
	def test_is_root_2(self):
		parent = TestNotebookNode()
		
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_root)
	
	def test_is_node_a_child_1(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		child = TestNotebookNode(parent=node, add_to_parent=True)
		
		self.assertEqual(True, node.is_node_a_child(child))
	
	def test_is_node_a_child_2(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		child1 = TestNotebookNode(parent=node, add_to_parent=True)
		child11 = TestNotebookNode(parent=child1, add_to_parent=True)
		
		self.assertEqual(True, node.is_node_a_child(child11))
	
	def test_is_node_a_child_3(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_node_a_child(node))
	
	def test_is_node_a_child_4(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		other_node = TestNotebookNode(parent=None)
		
		self.assertEqual(False, node.is_node_a_child(other_node))
	
	def test_title_init_set_new(self):
		"""Tests setting the title of a new node."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, title=DEFAULT_TITLE, loaded_from_storage=False)
		self.assertEqual(DEFAULT_TITLE, node.title)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title.
		node.title = 'new title'
		
		self.assertEqual('new title', node.title)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		
		# Save the node.
		node.save()
		
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=mock.ANY,
				attributes=AttributeMatcher(TITLE_ATTRIBUTE, node.title),
				payloads=mock.ANY)
		self.assertEqual(False, node.is_dirty)
		
		# Save the node again.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_title_init_set_from_storage(self):
		"""Tests setting the title of a node loaded from storage."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, title=DEFAULT_TITLE, loaded_from_storage=True)
		self.assertEqual(DEFAULT_TITLE, node.title)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title.
		node.title = 'new title'
		
		self.assertEqual('new title', node.title)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		
		# Save the node.
		node.save()
		
		notebook_storage.set_node_attributes.assert_called_once_with(node.node_id, AttributeMatcher(TITLE_ATTRIBUTE, node.title))
		self.assertEqual(False, node.is_dirty)
		
		# Save the node again.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_created_time_init_new(self):
		"""Tests the created time of a new node."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, loaded_from_storage=False)
		self.assertEqual(utc, node.created_time.tzinfo)
		self.assertEqual(True, abs(utc.localize(datetime.utcnow()) - node.created_time).total_seconds() < 5)
		original_created_time = node.created_time

		# Try changing the node's created time.
		with self.assertRaises(Exception):
			node.created_time = datetime.now(tz=utc)
		
		self.assertEqual(original_created_time, node.created_time)
		self.assertEqual(True, node.is_dirty)
		
		# Save the node.
		node.save()
		
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=mock.ANY,
				attributes=AttributeMatcher(CREATED_TIME_ATTRIBUTE, datetime_to_timestamp(node.created_time)),
				payloads=mock.ANY)
		self.assertEqual(False, node.is_dirty)
		
		# Save the node again.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_created_time_init_from_storage(self):
		"""Tests the created time of a node loaded from storage."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, created_time=DEFAULT_CREATED_TIME, loaded_from_storage=True)
		self.assertEqual(utc, node.created_time.tzinfo)
		self.assertEqual(DEFAULT_CREATED_TIME, node.created_time)
		original_created_time = node.created_time

		# Try changing the node's created time.
		with self.assertRaises(Exception):
			node.created_time = datetime.now(tz=utc)

		self.assertEqual(False, node.is_dirty)
		self.assertEqual(original_created_time, node.created_time)
		
		# Change something else to save the node.
		node.title = 'new title'
		self.assertEqual(True, node.is_dirty)
		
		# Save the node.
		node.save()
		
		notebook_storage.set_node_attributes.assert_called_once_with(node.node_id, AttributeMatcher(CREATED_TIME_ATTRIBUTE, DEFAULT_CREATED_TIMESTAMP))
		self.assertEqual(False, node.is_dirty)
		
		# Save the node again.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_created_time_init_unset(self):
		"""Tests loading a node from storage without a created time."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, created_time=None, loaded_from_storage=True)
		self.assertEqual(None, node.created_time)
		
		# Change something else to save the node.
		node.title = 'new title'
		self.assertEqual(True, node.is_dirty)
		
		# Save the node.
		node.save()
		
		notebook_storage.set_node_attributes.assert_called_once_with(node.node_id, MissingAttributeMatcher(CREATED_TIME_ATTRIBUTE))
		self.assertEqual(False, node.is_dirty)
	
	def test_modified_time_init_and_save_new(self):
		"""Tests saving the modified time of a new node."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, loaded_from_storage=False)
		self.assertEqual(utc, node.modified_time.tzinfo)
		self.assertEqual(node.created_time, node.modified_time)

		# Change the node's modified time.
		new_modified_time = datetime.now(tz=utc)
		node.modified_time = new_modified_time
		
		self.assertEqual(new_modified_time, node.modified_time)
		self.assertEqual(True, node.is_dirty)
		
		# Save the node.
		node.save()
		
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=mock.ANY,
				attributes=AttributeMatcher(MODIFIED_TIME_ATTRIBUTE, datetime_to_timestamp(node.modified_time)),
				payloads=mock.ANY)
		self.assertEqual(False, node.is_dirty)
		
		# Save the node again.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_modified_time_init_and_save_from_storage(self):
		"""Tests saving the modified time of a node loaded from storage."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, modified_time=DEFAULT_MODIFIED_TIME, loaded_from_storage=True)
		self.assertEqual(utc, node.modified_time.tzinfo)
		self.assertEqual(DEFAULT_MODIFIED_TIME, node.modified_time)

		# Change the node's modified time.
		new_modified_time = datetime.now(tz=utc)
		node.modified_time = new_modified_time
		
		self.assertEqual(new_modified_time, node.modified_time)
		self.assertEqual(True, node.is_dirty)
		
		# Save the node.
		node.save()
		
		notebook_storage.set_node_attributes.assert_called_once_with(node.node_id, AttributeMatcher(MODIFIED_TIME_ATTRIBUTE, datetime_to_timestamp(new_modified_time)))
		self.assertEqual(False, node.is_dirty)
		
		# Save the node again.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_icon_normal_init_set_new(self):
		"""Tests setting the normal icon of a new node."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, icon_normal=DEFAULT_ICON_NORMAL, loaded_from_storage=False)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's normal icon.
		node.icon_normal = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_normal)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		
		# Save the node.
		node.save()
		
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=mock.ANY,
				attributes=AttributeMatcher(ICON_NORMAL_ATTRIBUTE, node.icon_normal),
				payloads=mock.ANY)
		self.assertEqual(False, node.is_dirty)
		
		# Save the node again.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_icon_normal_init_set_from_storage(self):
		"""Tests setting the normal icon of a node loaded from storage."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, icon_normal=DEFAULT_ICON_NORMAL, loaded_from_storage=True)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's normal icon.
		node.icon_normal = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_normal)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		
		# Save the node.
		node.save()
		
		notebook_storage.set_node_attributes.assert_called_once_with(node.node_id, AttributeMatcher(ICON_NORMAL_ATTRIBUTE, node.icon_normal))
		self.assertEqual(False, node.is_dirty)
		
		# Save the node again.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_icon_open_init_set_new(self):
		"""Tests setting the open icon of a new node."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, icon_open=DEFAULT_ICON_OPEN, loaded_from_storage=False)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's open icon.
		node.icon_open = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_open)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		
		# Save the node.
		node.save()
		
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=mock.ANY,
				attributes=AttributeMatcher(ICON_OPEN_ATTRIBUTE, node.icon_open),
				payloads=mock.ANY)
		self.assertEqual(False, node.is_dirty)
		
		# Save the node again.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_icon_open_init_set_from_storage(self):
		"""Tests setting the open icon of a node loaded from storage."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, icon_open=DEFAULT_ICON_OPEN, loaded_from_storage=True)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's open icon.
		node.icon_open = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_open)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		
		# Save the node.
		node.save()
		
		notebook_storage.set_node_attributes.assert_called_once_with(node.node_id, AttributeMatcher(ICON_OPEN_ATTRIBUTE, node.icon_open))
		self.assertEqual(False, node.is_dirty)
		
		# Save the node again.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_title_color_foreground_init_set_new(self):
		"""Tests setting the title foreground color of a new node."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND, loaded_from_storage=False)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title foreground color.
		node.title_color_foreground = '#c0c0c0'
		
		self.assertEqual('#c0c0c0', node.title_color_foreground)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_title_color_foreground_init_set_from_storage(self):
		"""Tests setting the title foreground of a node loaded from storage."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND, loaded_from_storage=True)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title foreground color.
		node.title_color_foreground = '#c0c0c0'
		
		self.assertEqual('#c0c0c0', node.title_color_foreground)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_title_color_open_init_set_new(self):
		"""Tests setting the title background color of a new node."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND, loaded_from_storage=False)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title background color.
		node.title_color_background = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.title_color_background)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_title_color_open_init_set_from_storage(self):
		"""Tests setting the title background color of a node loaded from storage."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND, loaded_from_storage=True)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title background color.
		node.title_color_background = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.title_color_background)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_client_preferences_init_set_new(self):
		"""Tests setting the client preferences of a new node."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, client_preferences=DEFAULT_CLIENT_PREFERENCES, loaded_from_storage=False)
		self.assertEqual(DEFAULT_CLIENT_PREFERENCES, node.client_preferences._data)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		# Change the node's client preferences.
		node.client_preferences.get('test', 'key', define=True)
		node.client_preferences.set('test', 'key', 'new value')
		
		self.assertEqual('new value', node.client_preferences.get('test', 'key'))
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		
		# Save the node.
		node.save()
		
		notebook_storage.add_node.assert_called_once_with(node_id=node.node_id, content_type=mock.ANY, attributes=AttributeMatcher(CLIENT_PREFERENCES_ATTRIBUTE, node.client_preferences._data), payloads=mock.ANY)
		self.assertEqual(False, node.is_dirty)
		
		# Save the node again.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_client_preferences_set_from_storage(self):
		"""Tests setting the client preferences of a node loaded from storage."""
		notebook_storage = Mock(spec=storage.NotebookStorage)
		node = self._create_node(notebook_storage=notebook_storage, client_preferences=DEFAULT_CLIENT_PREFERENCES, loaded_from_storage=True)
		self.assertEqual(DEFAULT_CLIENT_PREFERENCES, node.client_preferences._data)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		# Change the node's client preferences.
		node.client_preferences.get('test', 'key', define=True)
		node.client_preferences.set('test', 'key', 'new value')

		self.assertEqual('new value', node.client_preferences.get('test', 'key'))
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)

		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.set_node_attributes.assert_called_once_with(node.node_id, AttributeMatcher(CLIENT_PREFERENCES_ATTRIBUTE, node.client_preferences._data))
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	
	def test_copy_behind_sibling(self):
		# Create the original and target nodes.
		original = self._create_node(parent=None, loaded_from_storage=False)
		target = Mock(spec=NotebookNode)
		child1 = Mock(spec=NotebookNode)
		child2 = Mock(spec=NotebookNode)
		target.children = [child1, child2]
		target.parent = None
		target.is_trash = False
		target.is_in_trash = False
		
		# Copy the node.
		original.copy(target, with_subtree=False, behind=child1)
		
		self._assert_proper_copy_call_on_mock(target_mock=target, original=original, behind=child1)
	
	def test_copy_with_subtree(self):
		"""Tests copying a node and its children."""
		
		# Create the original and target nodes. The original has two child nodes.
		original = self._create_node(parent=None, loaded_from_storage=False)
		child1 = Mock(spec=NotebookNode)
		child1.parent = original
		child1.is_deleted = False
		child2 = Mock(spec=NotebookNode)
		child2.parent = original
		child2.is_deleted = False
		original._add_child_node(child1)
		original._add_child_node(child2)
		target = Mock(spec=NotebookNode)
		target.parent = None
		target.is_trash = False
		target.is_in_trash = False
		copy = Mock(spec=NotebookNode)
		def side_effect(*_args, **_kwargs):
			return copy
		self._get_proper_copy_method(target).side_effect = side_effect
		
		# Copy the node.
		original.copy(target, with_subtree=True)
		
		# Verify the children.
		child1.copy.assert_called_once_with(copy, with_subtree=True)
		child2.copy.assert_called_once_with(copy, with_subtree=True)
	
	def test_copy_with_subtree_containing_deleted_nodes(self):
		"""Tests copying a node and its children, one of which is deleted."""
		
		# Create the original and target nodes. The original has two child nodes.
		original = self._create_node(parent=None, loaded_from_storage=False)
		child1 = Mock(spec=NotebookNode)
		child1.parent = original
		child1.is_deleted = False
		child2 = Mock(spec=NotebookNode)
		child2.parent = original
		child2.is_deleted = True
		child2.is_dirty = True
		original._add_child_node(child1)
		original._add_child_node(child2)
		target = Mock(spec=NotebookNode)
		target.parent = None
		target.is_trash = False
		target.is_in_trash = False
		copy = Mock(spec=NotebookNode)
		def side_effect(*_args, **_kwargs):
			return copy
		self._get_proper_copy_method(target).side_effect = side_effect
		
		# Copy the node.
		original.copy(target, with_subtree=True)
		
		# Verify the children.
		child1.copy.assert_called_once_with(copy, with_subtree=True)
		self.assertEqual(False, child2.copy.called)
	
	def test_save_not_dirty(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node.
		node = self._create_node(notebook_storage=notebook_storage, parent=None, loaded_from_storage=True)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.add_node.called)
		self.assertEqual(False, notebook_storage.add_node_payload.called)
		self.assertEqual(False, notebook_storage.remove_node_payload.called)
	
	def test_save_new_with_dirty_parent(self):
		"""Tests saving a new node with a dirty parent."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = TestNotebookNode()
		parent.set_is_dirty(True)
		node = self._create_node(notebook_storage=notebook_storage, parent=parent, loaded_from_storage=False)
		
		with self.assertRaises(IllegalOperationError):
			# Save the node.
			node.save()
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.add_node.called)
		
		# Verify the node.
		self.assertEqual(True, node.is_dirty)
	
	def test_save_with_unsaved_deleted_children_from_storage(self):
		"""Tests saving a node with unsaved deleted children that were loaded from storage."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the children.
		node = self._create_node(notebook_storage=notebook_storage, parent=None, loaded_from_storage=False)
		child1 = TestNotebookNode(parent=node, add_to_parent=True, loaded_from_storage=True)
		child1.set_is_dirty(True)
		child1.set_is_deleted(True)
		child2 = TestNotebookNode(parent=node, add_to_parent=True, loaded_from_storage=True)
		child2.set_is_dirty(True)
		child2.set_is_deleted(True)
		
		with self.assertRaises(IllegalOperationError):
			# Save the node.
			node.save()
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.add_node.called)
		
		# Verify the node.
		self.assertEqual(True, node.is_dirty)

	
class ContentFolderNodeTestBase(ContentFolderTrashNodeTestBase):
	def test_is_trash(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		self.assertEqual(False, node.is_trash)
		
	def test_is_in_trash_1(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = False
		
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_in_trash)
	
	def test_is_in_trash_2(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = True
		parent.is_in_trash = False
		
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(True, node.is_in_trash)
	
	def test_is_in_trash_3(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = True
		
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(True, node.is_in_trash)
	
	def test_is_in_trash_4(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_in_trash)
	
	def test_set_title_if_deleted(self):
		# Create the node and the parent.
		parent = Mock(spec=NotebookNode)
		parent.parent = None
		node = self._create_node(parent=parent, loaded_from_storage=False)
		parent.children = [node]

		# Delete and set the title.
		node.delete()
		with self.assertRaises(IllegalOperationError):
			node.title = 'new title'
		
		# Verify the node.
		self.assertNotEquals('new title', node.title)
	
	def test_delete_without_children_new(self):
		parent = TestNotebookNode()
		node = self._create_node(parent=parent, loaded_from_storage=False)
		
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
		self.assertEqual(True, node.can_delete())
		node.delete()
		self.assertEqual(False, node.is_dirty)
		self.assertEqual(True, node.is_deleted)
		self.assertEqual(False, node in parent.children)
		self.assertEqual(False, node in parent.get_children(unsaved_deleted=True))
	
	def test_delete_without_children_from_storage(self):
		parent = TestNotebookNode()
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
		self.assertEqual(True, node.can_delete())
		node.delete()
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.is_deleted)
		self.assertEqual(False, node in parent.children)
		self.assertEqual(True, node in parent.get_children(unsaved_deleted=True))
	
	def test_delete_with_children(self):
		parent = TestNotebookNode()
		node = self._create_node(parent=parent, loaded_from_storage=True)
		child1 = Mock(spec=NotebookNode)
		child1.parent = node
		child2 = Mock(spec=NotebookNode)
		child2.parent = node
		node._add_child_node(child1)
		node._add_child_node(child2)
		
		node.delete()
		
		child1.delete.assert_called_with()
		child2.delete.assert_called_with()
# TODO: Nodig?		self.assertEqual([], node.children)
	
	def test_delete_child_fails(self):
		parent = TestNotebookNode()
		node = self._create_node(parent=parent, loaded_from_storage=True)
		child = Mock(spec=NotebookNode)
		child.parent = node
		child.delete.side_effect = Exception()
		node._add_child_node(child)
		
		with self.assertRaises(Exception):
			node.delete()

		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
		self.assertEqual(True, node in parent.children)
	
	def test_delete_if_root(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		child = Mock(spec=NotebookNode)
		child.parent = node
		node._add_child_node(child)
		
		self.assertEqual(False, node.can_delete())
		
		with self.assertRaises(IllegalOperationError):
			node.delete()
		
		self.assertEqual(False, child.delete.called)
## TODO: Nodig?		self.assertEqual([child], node.children)
		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
	
	def test_new_content_child_node(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		self.assertEqual(True, node.can_add_new_content_child_node())
		
		# Add content node.
		child = node.new_content_child_node(
				content_type=CONTENT_TYPE_HTML,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
				)
		
		# Verify the parent.
		self.assertEqual(True, node.has_children())
		self.assertEqual([child], node.children)
		
		# Verify the child.
		self.assertEqual(AnyUuidMatcher(), child.node_id)
		self.assertEqual(CONTENT_TYPE_HTML, child.content_type)
		self.assertEqual(node, child.parent)
		self.assertEqual(DEFAULT_TITLE, child.title)
		self.assertEqual(DEFAULT_HTML_PAYLOAD_NAME, child.main_payload_name)
		self.assertEqual([DEFAULT_PNG_PAYLOAD_NAME], child.additional_payload_names)
		self.assertEqual(DEFAULT_HTML_PAYLOAD, child.get_payload(DEFAULT_HTML_PAYLOAD_NAME))
		self.assertEqual(DEFAULT_PNG_PAYLOAD, child.get_payload(DEFAULT_PNG_PAYLOAD_NAME))
		self.assertEqual(True, child.is_dirty)
	
	def test_new_content_child_node_in_trash_1(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = True
		parent.is_in_trash = False
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.can_add_new_content_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_content_child_node(
					content_type=CONTENT_TYPE_HTML,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
					additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
					)
	
	def test_new_content_child_node_in_trash_2(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = True
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.can_add_new_content_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_content_child_node(
					content_type=CONTENT_TYPE_HTML,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
					additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
					)
	
	def test_new_content_child_node_if_deleted(self):
		parent = TestNotebookNode()
		node = self._create_node(parent=parent, loaded_from_storage=True)
		node.delete()
		
		self.assertEqual(False, node.can_add_new_content_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_content_child_node(
					content_type=CONTENT_TYPE_HTML,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
					additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
					)
	
	def test_new_content_child_node_behind_sibling(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		child1 = node.new_folder_child_node(title=DEFAULT_TITLE)
		child2 = node.new_folder_child_node(title=DEFAULT_TITLE)
		
		# Add content node.
		child3 = node.new_content_child_node(
				content_type=CONTENT_TYPE_HTML,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[],
				behind=child1,
				)
		
		# Verify the parent.
		self.assertEqual([child1, child3, child2], node.children)
	
	def test_new_content_child_node_behind_nonexistent_sibling(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		with self.assertRaises(IllegalOperationError):
			# Add content node.
			node.new_content_child_node(
					content_type=CONTENT_TYPE_HTML,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
					additional_payloads=[],
					behind=object(),
					)
		
	def test_new_folder_child_node(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		self.assertEqual(True, node.can_add_new_folder_child_node())
		
		# Add folder node.
		child = node.new_folder_child_node(title=DEFAULT_TITLE)
		
		# Verify the parent.
		self.assertEqual(True, node.has_children())
		self.assertEqual([child], node.children)
		
		# Verify the child.
		self.assertEqual(AnyUuidMatcher(), child.node_id)
		self.assertEqual(CONTENT_TYPE_FOLDER, child.content_type)
		self.assertEqual(node, child.parent)
		self.assertEqual(DEFAULT_TITLE, child.title)
		self.assertEqual(True, child.is_dirty)
	
	def test_new_folder_child_node_in_trash_1(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = True
		parent.is_in_trash = False
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.can_add_new_folder_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_folder_child_node(title=DEFAULT_TITLE)
	
	def test_new_folder_child_node_in_trash_2(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = True
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.can_add_new_folder_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_folder_child_node(title=DEFAULT_TITLE)
	
	def test_new_folder_child_node_if_deleted(self):
		parent = TestNotebookNode()
		node = self._create_node(parent=parent, loaded_from_storage=True)
		node.delete()
		
		self.assertEqual(False, node.can_add_new_folder_child_node())
		
		with self.assertRaises(IllegalOperationError):
			node.new_folder_child_node(title=DEFAULT_TITLE)
	
	def test_new_folder_child_node_behind_sibling(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		child1 = node.new_folder_child_node(title=DEFAULT_TITLE)
		child2 = node.new_folder_child_node(title=DEFAULT_TITLE)
		
		# Add folder node.
		child3 = node.new_folder_child_node(title=DEFAULT_TITLE, behind=child1)
		
		# Verify the parent.
		self.assertEqual([child1, child3, child2], node.children)
	
	def test_new_folder_child_node_behind_nonexistent_sibling(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		with self.assertRaises(IllegalOperationError):
			# Add folder node.
			node.new_folder_child_node(title=DEFAULT_TITLE, behind=object())
	
	def test_copy_if_deleted(self):
		# Create the original, parent and target nodes.
		parent = TestNotebookNode()
		original = self._create_node(parent=parent, loaded_from_storage=True)
		target = Mock(spec=NotebookNode)
		target.is_trash = False
		target.is_in_trash = False
		
		# Delete the original.
		original.delete()
		
		# Verify the original.
		self.assertEqual(False, original.can_copy(target, with_subtree=False))
		
		with self.assertRaises(IllegalOperationError):
			# Copy the node.
			original.copy(target, with_subtree=False)
		
		# Verify the target.
		self.assertEqual(False, self._get_proper_copy_method(target).called)
	
	def test_copy_to_child(self):
		"""Tests copying a single node to one of its children."""
		
		# Create the original and target nodes. The original has two child nodes.
		original = self._create_node(parent=None, loaded_from_storage=False)
		child1 = Mock(spec=NotebookNode)
		child1.parent = original
		child1.children = []
		original.children.append(child1)
		child11 = Mock(spec=NotebookNode)
		child11.parent = child1
		child11.children = []
		child1.children.append(child11)
		target = child11
		target.is_trash = False
		target.is_in_trash = False
		
		# Verify the original.
		self.assertEqual(True, original.can_copy(target, with_subtree=False))
		
		# Copy the node.
		original.copy(target, with_subtree=False)
		
		self._assert_proper_copy_call_on_mock(target_mock=target, original=original, behind=None)
	
	def test_copy_to_trash_1(self):
		# Create the original and target nodes.
		original = self._create_node(parent=None, loaded_from_storage=True)
		target = Mock(spec=NotebookNode)
		target.is_trash = True
		target.is_in_trash = False
		
		# Verify the original.
		self.assertEqual(False, original.can_copy(target, with_subtree=False))
		
		with self.assertRaises(IllegalOperationError):
			# Copy the node.
			original.copy(target, with_subtree=False)
		
		# Verify the target.
		self.assertEqual(False, self._get_proper_copy_method(target).called)
	
	def test_copy_to_trash_2(self):
		# Create the original and target nodes.
		original = self._create_node(parent=None, loaded_from_storage=True)
		target = Mock(spec=NotebookNode)
		target.is_trash = False
		target.is_in_trash = True
		
		# Verify the original.
		self.assertEqual(False, original.can_copy(target, with_subtree=False))
		
		with self.assertRaises(IllegalOperationError):
			# Copy the node.
			original.copy(target, with_subtree=False)
		
		# Verify the target.
		self.assertEqual(False, self._get_proper_copy_method(target).called)
	
	def test_copy_with_subtree_to_child(self):
		"""Tests copying a node and its children to one of its children."""
		
		# Create the original and target nodes. The original has two child nodes.
		original = self._create_node(parent=None, loaded_from_storage=True)
		child1 = original.new_folder_child_node(title=DEFAULT_TITLE)
		child1.parent = original
		child11 = Mock(spec=NotebookNode)
		child11.parent = child1
		target = child11
		target.is_trash = False
		target.is_in_trash = False
		
		# Verify the original.
		self.assertEqual(False, original.can_copy(target, with_subtree=True))
		
		with self.assertRaises(IllegalOperationError):
			# Copy the node.
			original.copy(target, with_subtree=True)
		
		# Verify the target.
		self.assertEqual(False, self._get_proper_copy_method(target).called)
	
	def test_move(self):
		"""Tests moving a node."""
		
		# Create the node and parents.
		old_parent = TestNotebookNode()
		new_parent = TestNotebookNode()
		node = self._create_node(parent=old_parent, loaded_from_storage=True)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		# Verify the node.
		self.assertEqual(True, node.can_move(new_parent))
		
		# Move the node.
		node.move(new_parent)
		
		# Verify the node and the parents.
		self.assertEqual(new_parent, node.parent)
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual([], old_parent.children)
		self.assertEqual([node], new_parent.children)
	
	def test_move_behind_sibling(self):
		"""Tests moving a node behind a sibling."""
		
		# Create the node and parents.
		old_parent = TestNotebookNode()
		new_parent = TestNotebookNode()
		child1 = TestNotebookNode(parent=new_parent, add_to_parent=True)
		child2 = TestNotebookNode(parent=new_parent, add_to_parent=True)
		node = self._create_node(parent=old_parent, loaded_from_storage=True)
		
		# Move the node.
		node.move(new_parent, behind=child1)
		
		# Verify the new parent.
		self.assertEqual([child1, node, child2], new_parent.children)
	
	def test_move_behind_nonexistent_sibling(self):
		# Create the node and parents.
		old_parent = TestNotebookNode()
		new_parent = TestNotebookNode()
		node = self._create_node(parent=old_parent, loaded_from_storage=True)
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent, behind=object())
		
		# Verify the node and the parents.
		self.assertEqual(False, node.is_dirty)
		self.assertEqual([node], old_parent.children)
		self.assertEqual([], new_parent.children)
	
	def test_move_if_deleted(self):
		"""Tests moving a node if it is deleted."""
		
		old_parent = TestNotebookNode()
		new_parent = TestNotebookNode()
		node = self._create_node(parent=old_parent, loaded_from_storage=True)
		node.delete()
		
		# Verify the node.
		self.assertEqual(False, node.can_move(new_parent))
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent)
		
		# Verify the parent.
		self.assertEqual([], new_parent.children)
	
	def test_move_root(self):
		"""Tests moving a node if it is the root."""
		
		# Create the node and parents.
		new_parent = TestNotebookNode()
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		# Verify the node.
		self.assertEqual(False, node.can_move(new_parent))
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent)
		
		# Verify the node and the parent.
		self.assertEqual(False, node.is_dirty)
		self.assertEqual([], new_parent.children)
	
	def test_move_to_child(self):
		"""Tests moving a node to one of its children."""
		
		# Create the node and parents.
		old_parent = TestNotebookNode()
		node = self._create_node(parent=old_parent, loaded_from_storage=True)
		child1 = TestNotebookNode(parent=node, add_to_parent=True)
		child11 = TestNotebookNode(parent=child1, add_to_parent=True)
		new_parent = child11
		
		# Verify the node.
		self.assertEqual(False, node.can_move(new_parent))
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent)
		
		# Verify the node and the parents.
		self.assertEqual(False, node.is_dirty)
		self.assertEqual([node], old_parent.children)
		self.assertEqual([], new_parent.children)
	
	def test_move_to_different_notebook(self):
		"""Tests moving a node to another notebook."""
		
		# Create the notebooks.
		notebook1 = Mock(spec=Notebook)
		notebook2 = Mock(spec=Notebook)
		
		# Create the node and parents.
		old_parent = Mock(spec=NotebookNode)
		node = self._create_node(notebook=notebook1, parent=old_parent, loaded_from_storage=True)
		old_parent.children = [node]
		new_parent = Mock(spec=NotebookNode)
		new_parent._notebook = notebook2
		new_parent.children = []

		# Verify the node.
		self.assertEqual(False, node.can_move(new_parent))
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent, behind=object())
		
		# Verify the node and the parents.
		self.assertEqual(False, node.is_dirty)
		self.assertEqual([node], old_parent.children)
		self.assertEqual([], new_parent.children)
	
	def test_save_delete(self):
		"""Tests saving a deleted node."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = TestNotebookNode()
		node = self._create_node(notebook_storage=notebook_storage, parent=parent, loaded_from_storage=True)
		
		# Delete the node.
		node.delete()
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.remove_node.assert_called_once_with(node.node_id)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		self.assertEqual(True, node.is_deleted)
		
		# Verify the parent.
		self.assertEqual([], parent.get_children(unsaved_deleted=True))
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.remove_node.called)
	
	def test_save_new_and_deleted(self):
		"""Tests saving a deleted node."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = Mock(spec=NotebookNode)
		parent.node_id = new_node_id()
		parent.is_dirty = False
		node = self._create_node(notebook_storage=notebook_storage, parent=parent, loaded_from_storage=False)
		parent.children = [node]
		
		# Delete the node.
		node.delete()
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.remove_node.called)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		self.assertEqual(True, node.is_deleted)
	
	def test_save_loaded_and_deleted_with_dirty_parent(self):
		"""Tests saving a loaded and deleted node with a dirty parent."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = TestNotebookNode()
		parent.set_is_dirty(True)
		node = self._create_node(notebook_storage=notebook_storage, parent=parent, loaded_from_storage=True)
		
		# Delete the node.
		node.delete()
		
		with self.assertRaises(IllegalOperationError):
			# Save the node.
			node.save()
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.add_node.called)
		
		# Verify the node.
		self.assertEqual(True, node.is_dirty)
	
	def test_save_loaded_and_deleted_with_deleted_parent(self):
		"""Tests saving a loaded and deleted node with a deleted parent."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = TestNotebookNode()
		parent.set_is_deleted(True)
		parent.set_is_dirty(True)
		node = self._create_node(notebook_storage=notebook_storage, parent=parent, loaded_from_storage=True)
		
		# Delete the node.
		node.delete()
		
		# Save the node.
		node.save()
	
	def test_save_move(self):
		"""Tests saving a moved node."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and parents.
		old_parent = TestNotebookNode()
		new_parent = TestNotebookNode()
		node = self._create_node(notebook_storage=notebook_storage, parent=old_parent, loaded_from_storage=True)
		
		# Move the node.
		node.move(new_parent)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.set_node_attributes.assert_called_once_with(node.node_id, node._notebook_storage_attributes)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
	

class ContentNodeTest(unittest.TestCase, ContentFolderNodeTestBase):
	def _create_node(
			self,
			notebook_storage=None,
			notebook=None,
			parent=None,
			loaded_from_storage=False,
			title=DEFAULT_TITLE,
			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			client_preferences=DEFAULT_CLIENT_PREFERENCES,
			node_id=DEFAULT,
			created_time=DEFAULT,
			modified_time=DEFAULT,
			main_payload=DEFAULT,
			additional_payloads=DEFAULT,
			main_payload_name=DEFAULT,
			additional_payload_names=DEFAULT,
			):
		
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
			if main_payload_name is DEFAULT:
				main_payload_name = DEFAULT_HTML_PAYLOAD_NAME
			if additional_payload_names is DEFAULT:
				additional_payload_names = [DEFAULT_PNG_PAYLOAD_NAME]
		else:
			if main_payload is DEFAULT:
				main_payload = (DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD)
			if additional_payloads is DEFAULT:
				additional_payloads = [(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)]
			if node_id is DEFAULT:
				node_id = None
			if created_time is DEFAULT:
				created_time = None
			if modified_time is DEFAULT:
				modified_time = None
			if main_payload_name is DEFAULT:
				main_payload_name = None
			if additional_payload_names is DEFAULT:
				additional_payload_names = None
		
		node = ContentNode(
				notebook_storage=notebook_storage,
				notebook=notebook,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=parent,
				loaded_from_storage=loaded_from_storage,
				title=title,
				order=order,
				icon_normal=icon_normal,
				icon_open=icon_open,
				title_color_foreground=title_color_foreground,
				title_color_background=title_color_background,
				client_preferences=client_preferences,
				main_payload=main_payload,
				additional_payloads=additional_payloads,
				node_id=node_id,
				created_time=created_time,
				modified_time=modified_time,
				main_payload_name=main_payload_name,
				additional_payload_names=additional_payload_names
				)
		if parent is not None:
			parent._add_child_node(node)
		return node
	
	def _assert_proper_copy_call_on_mock(self, target_mock, original, behind):
		target_mock.new_content_child_node.assert_called_once_with(
				content_type=original.content_type,
				title=original.title,
				main_payload=(original.main_payload_name, original.get_payload(original.main_payload_name)),
				additional_payloads=[(additional_payload_name, original.get_payload(additional_payload_name)) for additional_payload_name in original.additional_payload_names],
				behind=behind
				)
	
	def _get_proper_copy_method(self, target_mock):
		return target_mock.new_content_child_node
	
	def test_create_new_c(self):
		parent = TestNotebookNode()
		
		node = ContentNode(
				notebook_storage=None,
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=parent,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				order=DEFAULT_ORDER,
				icon_normal=DEFAULT_ICON_NORMAL,
				icon_open=DEFAULT_ICON_OPEN,
				title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
				title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
				)
		
		self.assertEqual(DEFAULT_HTML_PAYLOAD_NAME, node.main_payload_name)
		self.assertEqual([DEFAULT_PNG_PAYLOAD_NAME], node.additional_payload_names)
		self.assertEqual(DEFAULT_HTML_PAYLOAD, node.get_payload(DEFAULT_HTML_PAYLOAD_NAME))
		self.assertEqual(DEFAULT_PNG_PAYLOAD, node.get_payload(DEFAULT_PNG_PAYLOAD_NAME))
		
	def test_create_from_storage_c(self):
		parent = TestNotebookNode()
		
		node = ContentNode(
				notebook_storage=None,
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=parent,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				order=DEFAULT_ORDER,
				icon_normal=DEFAULT_ICON_NORMAL,
				icon_open=DEFAULT_ICON_OPEN,
				title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
				title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
				node_id=DEFAULT_ID,
				created_time=DEFAULT_CREATED_TIME,
				modified_time=DEFAULT_MODIFIED_TIME,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_PNG_PAYLOAD_NAME],
				)
		
		self.assertEqual(DEFAULT_HTML_PAYLOAD_NAME, node.main_payload_name)
		self.assertEqual([DEFAULT_PNG_PAYLOAD_NAME], node.additional_payload_names)
	
	def test_constructor_parameters_new_c1(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			ContentNode(
					notebook_storage=None,
					notebook=None,
					content_type=DEFAULT_CONTENT_TYPE,
					parent=None,
					loaded_from_storage=False,
					title=DEFAULT_TITLE,
					main_payload=None,  # Must not be None if not loaded from storage
					additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
					node_id=None,
					main_payload_name=None,
					additional_payload_names=None,
					)
	
	def test_constructor_parameters_new_c2(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			ContentNode(
					notebook_storage=None,
					notebook=None,
					content_type=DEFAULT_CONTENT_TYPE,
					parent=None,
					loaded_from_storage=False,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
					additional_payloads=None,  # Must not be None if not loaded from storage
					node_id=None,
					main_payload_name=None,
					additional_payload_names=None,
					)
	
	def test_constructor_parameters_from_storage_c1(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			ContentNode(
					notebook_storage=None,
					notebook=None,
					content_type=DEFAULT_CONTENT_TYPE,
					parent=None,
					loaded_from_storage=True,
					title=DEFAULT_TITLE,
					main_payload=None,
					additional_payloads=None,
					node_id=DEFAULT_ID,
					main_payload_name=None,  # Must not be None if loaded from storage
					additional_payload_names=[DEFAULT_PNG_PAYLOAD_NAME],
					)
	
	def test_constructor_parameters_from_storage_c2(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			ContentNode(
					notebook_storage=None,
					notebook=None,
					content_type=DEFAULT_CONTENT_TYPE,
					parent=None,
					loaded_from_storage=True,
					title=DEFAULT_TITLE,
					main_payload=None,
					additional_payloads=None,
					node_id=DEFAULT_ID,
					main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
					additional_payload_names=None,  # Must not be None if loaded from storage
					)
	
	def test_notebook_storage_attributes_main_payload_name(self):
		node = ContentNode(
				notebook_storage=None,
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
				)
		
		self.assertEqual(DEFAULT_HTML_PAYLOAD_NAME, node._notebook_storage_attributes[MAIN_PAYLOAD_NAME_ATTRIBUTE])
		
	def test_add_additional_payload_new(self):
		node = ContentNode(
				notebook_storage=None,
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[(DEFAULT_JPG_PAYLOAD_NAME, DEFAULT_JPG_PAYLOAD)],
				)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		node.add_additional_payload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)
		
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual([DEFAULT_JPG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_NAME], node.additional_payload_names)
		self.assertEqual(DEFAULT_PNG_PAYLOAD, node.get_payload(DEFAULT_PNG_PAYLOAD_NAME))		
	
	def test_add_additional_payload_from_storage_1(self):
		node = ContentNode(
				notebook_storage=None,
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[],
				)
		
		with self.assertRaises(PayloadAlreadyExistsError):
			node.add_additional_payload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD)
		
		self.assertEqual(False, node.is_dirty)
	
	def test_add_additional_payload_from_storage_2(self):
		node = ContentNode(
				notebook_storage=None,
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_PNG_PAYLOAD_NAME],
				)
		
		with self.assertRaises(PayloadAlreadyExistsError):
			node.add_additional_payload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)
		
		self.assertEqual(False, node.is_dirty)
	
	def test_get_payload_from_storage(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		node = ContentNode(
				notebook_storage=notebook_storage,
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[],
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
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[],
				)
		
		with self.assertRaises(PayloadDoesNotExistError):
			node.get_payload('unknown_name')
	
	def test_remove_additional_payload_new(self):
		node = ContentNode(
				notebook_storage=None,
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[],
				)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		node.add_additional_payload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual([], node.additional_payload_names)
		with self.assertRaises(PayloadDoesNotExistError):
			node.get_payload(DEFAULT_PNG_PAYLOAD_NAME)
	
	def test_remove_additional_payload_from_storage(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		node = self._create_node(
				notebook_storage=notebook_storage,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_PNG_PAYLOAD_NAME],
				)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		def side_effect_get_node_payload(node_id, payload_name):
			if node_id == node.node_id and payload_name == DEFAULT_PNG_PAYLOAD_NAME:
				return io.BytesIO(DEFAULT_PNG_PAYLOAD)
			else:
				raise storage.PayloadDoesNotExistError
		notebook_storage.get_node_payload.side_effect = side_effect_get_node_payload
		
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual([], node.additional_payload_names)
		with self.assertRaises(PayloadDoesNotExistError):
			node.get_payload(DEFAULT_PNG_PAYLOAD_NAME)
	
	def test_remove_additional_payload_nonexistent(self):
		node = ContentNode(
				notebook_storage=None,
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[],
				)
		
		with self.assertRaises(PayloadDoesNotExistError):
			node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		
		self.assertEqual(False, node.is_dirty)
	
	def test_set_main_payload_new(self):
		node = ContentNode(
				notebook_storage=None,
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[],
				)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		node.set_main_payload('new payload 1')
		
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual('new payload 1', node.get_payload(DEFAULT_HTML_PAYLOAD_NAME))		
		
		node.set_main_payload('new payload 2')
		
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual('new payload 2', node.get_payload(DEFAULT_HTML_PAYLOAD_NAME))		
	
	def test_set_main_payload_from_storage(self):
		node = self._create_node(
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[],
				)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		node.set_main_payload('new payload 1')
		
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual('new payload 1', node.get_payload(DEFAULT_HTML_PAYLOAD_NAME))		
		
		node.set_main_payload('new payload 2')
		
		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual('new payload 2', node.get_payload(DEFAULT_HTML_PAYLOAD_NAME))		
	
	def test_copy_new(self):
		"""Tests copying a single node without its children."""
		
		# Create the original and target nodes. The original has a child node.
		original = ContentNode(
				notebook_storage=None,
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
				)
		original.new_folder_child_node(title=DEFAULT_TITLE)
		target = Mock(spec=NotebookNode)
		target.parent = None
		target.is_trash = False
		target.is_in_trash = False
		copy = Mock(spec=NotebookNode)
		def side_effect(*_args, **_kwargs):
			return copy
		self._get_proper_copy_method(target).side_effect = side_effect
		
		# Verify the original.
		self.assertEqual(True, original.can_copy(target, with_subtree=False))
		
		# Copy the node.
		result = original.copy(target, with_subtree=False)
		
		# Verify the result and the parent.
		self.assertEqual(copy, result)
		self._assert_proper_copy_call_on_mock(target_mock=target, original=original, behind=None)
	
	def test_copy_from_storage(self):
		"""Tests copying a single node without its children."""
		
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the original and target nodes. The original has a child node.
		original = ContentNode(
				notebook_storage=notebook_storage,
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_PNG_PAYLOAD_NAME],
				)
		original.new_folder_child_node(title=DEFAULT_TITLE)
		target = Mock(spec=NotebookNode)
		target.parent = None
		target.is_trash = False
		target.is_in_trash = False
		copy = Mock(spec=NotebookNode)
		def side_effect(*_args, **_kwargs):
			return copy
		self._get_proper_copy_method(target).side_effect = side_effect
		
		def side_effect_get_node_payload(node_id, payload_name):
			if node_id == original.node_id and payload_name == DEFAULT_HTML_PAYLOAD_NAME:
				return io.BytesIO(DEFAULT_HTML_PAYLOAD)
			elif node_id == original.node_id and payload_name == DEFAULT_PNG_PAYLOAD_NAME:
				return io.BytesIO(DEFAULT_PNG_PAYLOAD)
			else:
				raise storage.PayloadDoesNotExistError
		notebook_storage.get_node_payload.side_effect = side_effect_get_node_payload
		
		# Verify the original.
		self.assertEqual(True, original.can_copy(target, with_subtree=False))
		
		# Copy the node.
		result = original.copy(target, with_subtree=False)
		
		# Verify the result and the parent.
		self.assertEqual(copy, result)
		self._assert_proper_copy_call_on_mock(target_mock=target, original=original, behind=None)
	
	def test_save_new(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = Mock(spec=NotebookNode)
		parent.node_id = new_node_id()
		parent.is_dirty = False
		node = ContentNode(
				notebook_storage=notebook_storage,
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=parent,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
				)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=DEFAULT_CONTENT_TYPE,
				attributes=node._notebook_storage_attributes,
				payloads=[
						(DEFAULT_HTML_PAYLOAD_NAME, FileMatcher(io.BytesIO(DEFAULT_HTML_PAYLOAD))),
						(DEFAULT_PNG_PAYLOAD_NAME, FileMatcher(io.BytesIO(DEFAULT_PNG_PAYLOAD)))
						]
				)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node.called)
	
	def test_save_new_root(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		node = ContentNode(
				notebook_storage=notebook_storage,
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
				)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=DEFAULT_CONTENT_TYPE,
				attributes=node._notebook_storage_attributes,
				payloads=[
						(DEFAULT_HTML_PAYLOAD_NAME, FileMatcher(io.BytesIO(DEFAULT_HTML_PAYLOAD))),
						(DEFAULT_PNG_PAYLOAD_NAME, FileMatcher(io.BytesIO(DEFAULT_PNG_PAYLOAD)))
						]
				)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node.called)
	
	def test_save_add_additional_payload_from_storage(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node.
		node = ContentNode(
				notebook_storage=notebook_storage,
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_JPG_PAYLOAD_NAME]
				)
		
		# Make changes.
		node.add_additional_payload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.add_node_payload.assert_called_once_with(DEFAULT_ID, DEFAULT_PNG_PAYLOAD_NAME, FileMatcher(io.BytesIO(DEFAULT_PNG_PAYLOAD)))
		self.assertEqual(False, notebook_storage.remove_node_payload.called)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node_payload.called)
		self.assertEqual(False, notebook_storage.remove_node_payload.called)
	
	def test_save_remove_additional_payload_new(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node.
		node = ContentNode(
				notebook_storage=notebook_storage,
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
				additional_payloads=[]
				)
		
		# Make changes.
		node.add_additional_payload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.remove_node_payload.called)
		self.assertEqual(False, notebook_storage.add_node_payload.called)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node_payload.called)
		self.assertEqual(False, notebook_storage.remove_node_payload.called)
	
	def test_save_remove_additional_payload_from_storage(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node.
		node = ContentNode(
				notebook_storage=notebook_storage,
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_PNG_PAYLOAD_NAME]
				)
		
		# Make changes.
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.remove_node_payload.assert_called_once_with(DEFAULT_ID, DEFAULT_PNG_PAYLOAD_NAME)
		self.assertEqual(False, notebook_storage.add_node_payload.called)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node_payload.called)
		self.assertEqual(False, notebook_storage.remove_node_payload.called)
	
	def test_save_set_main_payload_from_storage(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node.
		node = ContentNode(
				notebook_storage=notebook_storage,
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[]
				)
		
		# Make changes.
		node.set_main_payload('new payload 1 (that should not be saved)')
		node.set_main_payload('new payload 2')
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.remove_node_payload.assert_called_once_with(DEFAULT_ID, DEFAULT_HTML_PAYLOAD_NAME)
		notebook_storage.add_node_payload.assert_called_once_with(DEFAULT_ID, DEFAULT_HTML_PAYLOAD_NAME, FileMatcher(io.BytesIO('new payload 2')))
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node_payload.called)
		self.assertEqual(False, notebook_storage.remove_node_payload.called)
	
	def test_save_replace_additional_payload(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node.
		node = ContentNode(
				notebook_storage=notebook_storage,
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_PNG_PAYLOAD_NAME]
				)
		
		# Make changes.
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		node.add_additional_payload(DEFAULT_PNG_PAYLOAD_NAME, 'new payload 1')
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		node.add_additional_payload(DEFAULT_PNG_PAYLOAD_NAME, 'new payload 2')
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.remove_node_payload.assert_called_once_with(DEFAULT_ID, DEFAULT_PNG_PAYLOAD_NAME)
		notebook_storage.add_node_payload.assert_called_once_with(DEFAULT_ID, DEFAULT_PNG_PAYLOAD_NAME, FileMatcher(io.BytesIO('new payload 2')))
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node_payload.called)
		self.assertEqual(False, notebook_storage.remove_node_payload.called)
	
	def test_save_multiple_changes(self):
		"""Tests saving multiple changes at once."""
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and parents.
		old_parent = TestNotebookNode()
		new_parent = TestNotebookNode()
		node = ContentNode(
				notebook_storage=notebook_storage,
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=old_parent,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload_name=DEFAULT_HTML_PAYLOAD_NAME,
				additional_payload_names=[DEFAULT_PNG_PAYLOAD_NAME],
				)
		old_parent._add_child_node(node)

		# Make several changes.
		node.title = 'new title'
		node.move(new_parent)
		node.set_main_payload('new html payload data')
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		node.add_additional_payload(DEFAULT_PNG_PAYLOAD_NAME, 'new png payload')
		node.add_additional_payload(DEFAULT_JPG_PAYLOAD_NAME, 'new jpg payload')
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.add_node.called)
		self.assertEqual([
				call.set_node_attributes(DEFAULT_ID, node._notebook_storage_attributes),
				call.remove_node_payload(DEFAULT_ID, DEFAULT_HTML_PAYLOAD_NAME),
				call.remove_node_payload(DEFAULT_ID, DEFAULT_PNG_PAYLOAD_NAME),
				call.add_node_payload(DEFAULT_ID, DEFAULT_HTML_PAYLOAD_NAME, FileMatcher(io.BytesIO('new html payload data'))),
				call.add_node_payload(DEFAULT_ID, DEFAULT_PNG_PAYLOAD_NAME, FileMatcher(io.BytesIO('new png payload'))),
				call.add_node_payload(DEFAULT_ID, DEFAULT_JPG_PAYLOAD_NAME, FileMatcher(io.BytesIO('new jpg payload'))),
				], notebook_storage.method_calls)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node.called)
		self.assertEqual(False, notebook_storage.set_node_attributes.called)
		self.assertEqual(False, notebook_storage.add_node_payload.called)
		self.assertEqual(False, notebook_storage.remove_node_payload.called)

class FolderNodeTest(unittest.TestCase, ContentFolderNodeTestBase):
	def _create_node(
			self,
			notebook_storage=None,
			notebook=None,
			parent=None,
			loaded_from_storage=False,
			title=DEFAULT_TITLE,
			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			client_preferences=DEFAULT_CLIENT_PREFERENCES,
			node_id=DEFAULT,
			created_time=DEFAULT,
			modified_time=DEFAULT,
			):
		
		if loaded_from_storage:
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
		
		node = FolderNode(
				notebook_storage=notebook_storage,
				notebook=notebook,
				parent=parent,
				loaded_from_storage=loaded_from_storage,
				title=title,
				order=order,
				icon_normal=icon_normal,
				icon_open=icon_open,
				title_color_foreground=title_color_foreground,
				title_color_background=title_color_background,
				client_preferences=client_preferences,
				node_id=node_id,
				created_time=created_time,
				modified_time=modified_time,
				)
		if parent is not None:
			parent._add_child_node(node)
		return node
	
	def _assert_proper_copy_call_on_mock(self, target_mock, original, behind):
		target_mock.new_folder_child_node.assert_called_once_with(
				title=original.title,
				behind=behind
				)
	
	def _get_proper_copy_method(self, target_mock):
		return target_mock.new_folder_child_node
	
	def test_copy_new(self):
		"""Tests copying a single node without its children."""
		
		# Create the original and target nodes. The original has a child node.
		original = FolderNode(
				notebook_storage=None,
				notebook=None,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				)
		original.new_folder_child_node(title=DEFAULT_TITLE)
		target = Mock(spec=NotebookNode)
		target.parent = None
		target.is_trash = False
		target.is_in_trash = False
		copy = Mock(spec=NotebookNode)
		def side_effect(*_args, **_kwargs):
			return copy
		self._get_proper_copy_method(target).side_effect = side_effect
		
		# Verify the original.
		self.assertEqual(True, original.can_copy(target, with_subtree=False))
		
		# Copy the node.
		result = original.copy(target, with_subtree=False)
		
		# Verify the result and the parent.
		self.assertEqual(copy, result)
		self._assert_proper_copy_call_on_mock(target_mock=target, original=original, behind=None)
	
	def test_copy_from_storage(self):
		"""Tests copying a single node without its children."""
		
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the original and target nodes. The original has a child node.
		original = FolderNode(
				notebook_storage=notebook_storage,
				notebook=None,
				node_id=DEFAULT_ID,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				)
		original.new_folder_child_node(title=DEFAULT_TITLE)
		target = Mock(spec=NotebookNode)
		target.parent = None
		target.is_trash = False
		target.is_in_trash = False
		copy = Mock(spec=NotebookNode)
		def side_effect(*_args, **_kwargs):
			return copy
		self._get_proper_copy_method(target).side_effect = side_effect
		
		# Verify the original.
		self.assertEqual(True, original.can_copy(target, with_subtree=False))
		
		# Copy the node.
		result = original.copy(target, with_subtree=False)
		
		# Verify the result and the parent.
		self.assertEqual(copy, result)
		self._assert_proper_copy_call_on_mock(target_mock=target, original=original, behind=None)
	
	def test_save_new(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = Mock(spec=NotebookNode)
		parent.node_id = new_node_id()
		parent.is_dirty = False
		node = FolderNode(
				notebook_storage=notebook_storage,
				notebook=None,
				parent=parent,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=CONTENT_TYPE_FOLDER,
				attributes=node._notebook_storage_attributes,
				payloads=[]
				)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node.called)
	
	def test_save_new_root(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		node = FolderNode(
				notebook_storage=notebook_storage,
				notebook=None,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=CONTENT_TYPE_FOLDER,
				attributes=node._notebook_storage_attributes,
				payloads=[]
				)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node.called)
	
	def test_save_multiple_changes(self):
		"""Tests saving multiple changes at once."""
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and parents.
		old_parent = TestNotebookNode()
		new_parent = TestNotebookNode()
		node = FolderNode(
				notebook_storage=notebook_storage,
				notebook=None,
				node_id=DEFAULT_ID,
				parent=old_parent,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				)
		old_parent._add_child_node(node)

		# Make several changes.
		node.title = 'new title'
		node.move(new_parent)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.add_node.called)
		self.assertEqual([
				call.set_node_attributes(DEFAULT_ID, node._notebook_storage_attributes),
				], notebook_storage.method_calls)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node.called)
		self.assertEqual(False, notebook_storage.set_node_attributes.called)


class TrashNodeTest(unittest.TestCase, ContentFolderTrashNodeTestBase):
	def _create_node(
			self,
			notebook_storage=None,
			notebook=None,
			parent=None,
			loaded_from_storage=False,
			title=DEFAULT_TITLE,
			order=DEFAULT_ORDER,
			icon_normal=DEFAULT_ICON_NORMAL,
			icon_open=DEFAULT_ICON_OPEN,
			title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND,
			title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND,
			client_preferences=DEFAULT_CLIENT_PREFERENCES,
			node_id=DEFAULT,
			created_time=DEFAULT,
			modified_time=DEFAULT,
			):
		
		if loaded_from_storage:
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
		
		node = TrashNode(
				notebook_storage=notebook_storage,
				notebook=notebook,
				parent=parent,
				loaded_from_storage=loaded_from_storage,
				title=title,
				order=order,
				icon_normal=icon_normal,
				icon_open=icon_open,
				title_color_foreground=title_color_foreground,
				title_color_background=title_color_background,
				client_preferences=client_preferences,
				node_id=node_id,
				created_time=created_time,
				modified_time=modified_time,
				)
		if parent is not None:
			parent._add_child_node(node)
		return node

	def _assert_proper_copy_call_on_mock(self, target_mock, original, behind):
		target_mock.new_folder_child_node.assert_called_once_with(
				title=original.title,
				behind=behind
				)
	
	def _get_proper_copy_method(self, target_mock):
		return target_mock.new_folder_child_node
	
	def test_is_trash(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		self.assertEqual(True, node.is_trash)
		
	def test_is_in_trash(self):
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = False
		
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_in_trash)
	
	def test_delete(self):
		# Create the node, the parent and the child.
		parent = TestNotebookNode()
		node = TrashNode(
				notebook_storage=None,
				notebook=None,
				node_id=DEFAULT_ID,
				parent=parent,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				)
		parent._add_child_node(node)
		child = Mock(spec=NotebookNode)
		child.parent = node
		node._add_child_node(child)
		
		self.assertEqual(False, node.can_delete())
				
		with self.assertRaises(IllegalOperationError):
			node.delete()
		
		self.assertEqual(False, child.delete.called)
## TODO: Nodig?		self.assertEqual([child], node.children)
		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
	
	def test_new_content_child_node(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		self.assertEqual(False, node.can_add_new_content_child_node())
		
		with self.assertRaises(IllegalOperationError):
			# Add content node.
			node.new_content_child_node(
					content_type=CONTENT_TYPE_HTML,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD),
					additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD)],
					)
		
		# Verify the parent.
		self.assertEqual([], node.children)
	
	def test_new_folder_child_node(self):
		node = self._create_node(parent=None, loaded_from_storage=True)
		
		self.assertEqual(False, node.can_add_new_folder_child_node())
		
		with self.assertRaises(IllegalOperationError):
			# Add folder node.
			node.new_folder_child_node(title=DEFAULT_TITLE)
		
		# Verify the parent.
		self.assertEqual([], node.children)
	
	def test_copy_new(self):
		"""Tests copying a single node without its children."""
		
		# Create the original and target nodes. The original has a child node.
		original = TrashNode(
				notebook_storage=None,
				notebook=None,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				)
		child = Mock(spec=NotebookNode)
		child.parent = original
		original._add_child_node(child)
		target = Mock(spec=NotebookNode)
		target.parent = None
		target.is_trash = False
		target.is_in_trash = False
		copy = Mock(spec=NotebookNode)
		def side_effect(*_args, **_kwargs):
			return copy
		self._get_proper_copy_method(target).side_effect = side_effect
		
		# Verify the original.
		self.assertEqual(True, original.can_copy(target, with_subtree=False))
		
		# Copy the node.
		result = original.copy(target, with_subtree=False)
		
		# Verify the result and the parent.
		self.assertEqual(copy, result)
		self._assert_proper_copy_call_on_mock(target_mock=target, original=original, behind=None)
	
	def test_copy_from_storage(self):
		"""Tests copying a single node without its children."""
		
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the original and target nodes. The original has a child node.
		original = TrashNode(
				notebook_storage=notebook_storage,
				notebook=None,
				node_id=DEFAULT_ID,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				)
		child = Mock(spec=NotebookNode)
		child.parent = original
		original._add_child_node(child)
		target = Mock(spec=NotebookNode)
		target.parent = None
		target.is_trash = False
		target.is_in_trash = False
		copy = Mock(spec=NotebookNode)
		def side_effect(*_args, **_kwargs):
			return copy
		self._get_proper_copy_method(target).side_effect = side_effect
		
		# Verify the original.
		self.assertEqual(True, original.can_copy(target, with_subtree=False))
		
		# Copy the node.
		result = original.copy(target, with_subtree=False)
		
		# Verify the result and the parent.
		self.assertEqual(copy, result)
		self._assert_proper_copy_call_on_mock(target_mock=target, original=original, behind=None)
	
	def test_copy_to_self(self):
		"""Tests copying a single node to itself."""
		
		# Create the original and target nodes. The original has two child nodes.
		original = self._create_node(parent=None, loaded_from_storage=False)
		target = original
		
		# Verify the original.
		self.assertEqual(False, original.can_copy(target, with_subtree=False))
		
		with self.assertRaises(IllegalOperationError):
			# Copy the node.
			original.copy(target, with_subtree=False)
		
		self.assertEqual([], target.children)
	
	def test_copy_to_child(self):
		"""Tests copying a single node to one of its children."""
		
		# Create the original and target nodes. The original has two child nodes.
		original = self._create_node(parent=None, loaded_from_storage=False)
		child1 = Mock(spec=NotebookNode)
		child1.parent = original
		child1.children = []
		original.children.append(child1)
		child11 = Mock(spec=NotebookNode)
		child11.parent = child1
		child11.children = []
		child1.children.append(child11)
		target = child11
		target.is_trash = False
		target.is_in_trash = False
		
		# Verify the original.
		self.assertEqual(False, original.can_copy(target, with_subtree=False))
		
		with self.assertRaises(IllegalOperationError):
			# Copy the node.
			original.copy(target, with_subtree=False)
		
		self.assertEqual([], target.children)
	
	def test_move(self):
		"""Tests moving a node."""
		
		# Create the node and parents.
		old_parent = Mock(spec=NotebookNode)
		node = self._create_node(parent=old_parent, loaded_from_storage=True)
		old_parent.children = [node]
		new_parent = Mock(spec=NotebookNode)
		new_parent._notebook = None
		new_parent.parent = None
		new_parent.children = []
		
		# Verify the node.
		self.assertEqual(False, node.can_move(new_parent))
		
		with self.assertRaises(IllegalOperationError):
			# Move the node.
			node.move(new_parent)
		
		# Verify the node and the parents.
		self.assertEqual(old_parent, node.parent)
		self.assertEqual(False, node.is_dirty)
		self.assertEqual([node], old_parent.children)
		self.assertEqual([], new_parent.children)
	
	
	def test_save_new(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = Mock(spec=NotebookNode)
		parent.node_id = new_node_id()
		parent.is_dirty = False
		node = TrashNode(
				notebook_storage=notebook_storage,
				notebook=None,
				parent=parent,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=CONTENT_TYPE_TRASH,
				attributes=node._notebook_storage_attributes,
				payloads=[]
				)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node.called)
	
	def test_save_new_root(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		node = TrashNode(
				notebook_storage=notebook_storage,
				notebook=None,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=CONTENT_TYPE_TRASH,
				attributes=node._notebook_storage_attributes,
				payloads=[]
				)
		
		# Verify the node.
		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node.called)
	


# Utilities

class AnyUuidMatcher(object):
	def __eq__(self, other):
		if other is None:
			return False
		matcher = re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', other)
		return matcher is not None
	
	def __repr__(self, *_args, **_kwargs):
		return '{cls}[]'.format(cls=self.__class__.__name__, **self.__dict__)

class AllButOneUuidMatcher(AnyUuidMatcher):
	def __init__(self, uuid):
		self.uuid = uuid
	
	def __eq__(self, other):
		return super(AllButOneUuidMatcher, self).__eq__(other) and other != self.uuid

class AttributeMatcher(object):
	def __init__(self, attribute, expected_value):
		self.attribute = attribute
		self.expected_value = expected_value
	
	def __eq__(self, other):
		if self.attribute not in other:
			return False
		result = other[self.attribute] == self.expected_value
		return result
	
	def __ne__(self, other):
		return not self.__eq__(other);

class FileMatcher(object):
	def __init__(self, expected):
		self.expected = expected.read()
	
	def __eq__(self, other):
		actual = other.read()
		return self.expected == actual
	
	def __ne__(self, other):
		return not self.__eq__(other);

class MissingAttributeMatcher(object):
	def __init__(self, attribute):
		self.attribute = attribute
	
	def __eq__(self, other):
		return self.attribute not in other
	
	def __ne__(self, other):
		return not self.__eq__(other);

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

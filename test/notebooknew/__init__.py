# -*- coding: utf-8 -*-
import base64
import copy
from datetime import datetime
from hamcrest import *
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

from test.notebooknew.testutils import *

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

# The following StoredNodes and NotebookNodes have the following structure:
# root
#   child1
#     child11
#     child12
#       child121
#   child2
#     child21
ROOT_SN = StoredNode('root_id', CONTENT_TYPE_FOLDER, attributes={TITLE_ATTRIBUTE: 'root'}, payloads=[])
CHILD1_SN = StoredNode('child1_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child1'}, payloads=[])
CHILD11_SN = StoredNode('child11_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child11'}, payloads=[])
CHILD12_SN = StoredNode('child12_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child1_id', TITLE_ATTRIBUTE: 'child12'}, payloads=[])
CHILD121_SN = StoredNode('child121_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child12_id', TITLE_ATTRIBUTE: 'child121'}, payloads=[])
CHILD2_SN = StoredNode('child2_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'child2'}, payloads=[])
CHILD21_SN = StoredNode('child21_id', CONTENT_TYPE_FOLDER, attributes={PARENT_ID_ATTRIBUTE: 'child2_id', TITLE_ATTRIBUTE: 'child21'}, payloads=[])
TRASH_SN = StoredNode('trash_id', CONTENT_TYPE_TRASH, attributes={PARENT_ID_ATTRIBUTE: 'root_id', TITLE_ATTRIBUTE: 'trash'}, payloads=[])


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
		
		# Initialize Notebook.
		notebook = Notebook()
		
		# Verify the Notebook.
# 		self.assertEqual(False, notebook.is_dirty)
	
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
		
		# Initialize Notebook.
		notebook = Notebook()
		
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
		
# 		self.assertEqual(False, notebook.is_dirty)
		notebook.save()
		
		self.assertEqual(2, len(list(notebook_storage.get_all_nodes())))
	
	def test_close_without_changes(self):
		handler = Mock()
		
		notebook = Notebook()
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
		handler = Mock()
		
		notebook = Notebook()
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
					node_id=None,  # Must be not None if loaded from storage
					)
	
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
		node = self._create_node(title=DEFAULT_TITLE, loaded_from_storage=False)
		self.assertEqual(DEFAULT_TITLE, node.title)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title.
		node.title = 'new title'
		
		self.assertEqual('new title', node.title)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_title_init_set_from_storage(self):
		"""Tests setting the title of a node loaded from storage."""
		node = self._create_node(title=DEFAULT_TITLE, loaded_from_storage=True)
		self.assertEqual(DEFAULT_TITLE, node.title)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title.
		node.title = 'new title'
		
		self.assertEqual('new title', node.title)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_title_create_copy(self):
		node = self._create_node(title=DEFAULT_TITLE, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.title, equal_to(node.title))
	
	def test_created_time_init_new(self):
		"""Tests the created time of a new node."""
		node = self._create_node(loaded_from_storage=False)
		self.assertEqual(utc, node.created_time.tzinfo)
		self.assertEqual(True, abs(utc.localize(datetime.utcnow()) - node.created_time).total_seconds() < 5)
		original_created_time = node.created_time

		# Try changing the node's created time.
		with self.assertRaises(Exception):
			node.created_time = datetime.now(tz=utc)
		
		self.assertEqual(original_created_time, node.created_time)
# 		self.assertEqual(True, node.is_dirty)
	
	def test_created_time_init_from_storage(self):
		"""Tests the created time of a node loaded from storage."""
		node = self._create_node(created_time=DEFAULT_CREATED_TIME, loaded_from_storage=True)
		self.assertEqual(utc, node.created_time.tzinfo)
		self.assertEqual(DEFAULT_CREATED_TIME, node.created_time)
		original_created_time = node.created_time

		# Try changing the node's created time.
		with self.assertRaises(Exception):
			node.created_time = datetime.now(tz=utc)

# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual(original_created_time, node.created_time)
	
	def test_created_time_init_unset(self):
		"""Tests loading a node from storage without a created time."""
		node = self._create_node(created_time=None, loaded_from_storage=True)
		self.assertEqual(None, node.created_time)
	
	def test_created_time_create_copy(self):
		node = self._create_node(loaded_from_storage=False)
		sleep(1 * MS)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.created_time.tzinfo, is_(same_instance(utc)))
		assert_that(abs(utc.localize(datetime.utcnow()) - copy.created_time).total_seconds(), is_(less_than(1)))
		assert_that(copy.created_time, is_not(equal_to(node.created_time)))
	
	def test_modified_time_init_new(self):
		"""Tests saving the modified time of a new node."""
		node = self._create_node(loaded_from_storage=False)
		self.assertEqual(utc, node.modified_time.tzinfo)
		self.assertEqual(node.created_time, node.modified_time)

		# Change the node's modified time.
		new_modified_time = datetime.now(tz=utc)
		node.modified_time = new_modified_time
		
		self.assertEqual(new_modified_time, node.modified_time)
# 		self.assertEqual(True, node.is_dirty)
	
	def test_modified_time_init_from_storage(self):
		"""Tests saving the modified time of a node loaded from storage."""
		node = self._create_node(modified_time=DEFAULT_MODIFIED_TIME, loaded_from_storage=True)
		self.assertEqual(utc, node.modified_time.tzinfo)
		self.assertEqual(DEFAULT_MODIFIED_TIME, node.modified_time)

		# Change the node's modified time.
		new_modified_time = datetime.now(tz=utc)
		node.modified_time = new_modified_time
		
		self.assertEqual(new_modified_time, node.modified_time)
# 		self.assertEqual(True, node.is_dirty)
	
	def test_modified_time_create_copy(self):
		node = self._create_node(loaded_from_storage=False)
		sleep(1 * MS)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.created_time.tzinfo, is_(same_instance(utc)))
		assert_that(copy.modified_time, equal_to(copy.created_time))
	
	def test_icon_normal_init_set_new(self):
		"""Tests setting the normal icon of a new node."""
		node = self._create_node(icon_normal=DEFAULT_ICON_NORMAL, loaded_from_storage=False)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's normal icon.
		node.icon_normal = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_normal)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_icon_normal_init_set_from_storage(self):
		"""Tests setting the normal icon of a node loaded from storage."""
		node = self._create_node(icon_normal=DEFAULT_ICON_NORMAL, loaded_from_storage=True)
		self.assertEqual(DEFAULT_ICON_NORMAL, node.icon_normal)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's normal icon.
		node.icon_normal = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_normal)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_icon_normal_create_copy(self):
		node = self._create_node(icon_normal=DEFAULT_ICON_NORMAL, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.icon_normal, equal_to(node.icon_normal))
	
	def test_icon_open_init_set_new(self):
		"""Tests setting the open icon of a new node."""
		node = self._create_node(icon_open=DEFAULT_ICON_OPEN, loaded_from_storage=False)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's open icon.
		node.icon_open = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_open)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_icon_open_init_set_from_storage(self):
		"""Tests setting the open icon of a node loaded from storage."""
		node = self._create_node(icon_open=DEFAULT_ICON_OPEN, loaded_from_storage=True)
		self.assertEqual(DEFAULT_ICON_OPEN, node.icon_open)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's open icon.
		node.icon_open = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.icon_open)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_icon_open_create_copy(self):
		node = self._create_node(icon_open=DEFAULT_ICON_OPEN, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.icon_open, equal_to(node.icon_open))
	
	def test_title_color_foreground_init_set_new(self):
		"""Tests setting the title foreground color of a new node."""
		node = self._create_node(title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND, loaded_from_storage=False)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title foreground color.
		node.title_color_foreground = '#c0c0c0'
		
		self.assertEqual('#c0c0c0', node.title_color_foreground)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_title_color_foreground_init_set_from_storage(self):
		"""Tests setting the title foreground of a node loaded from storage."""
		node = self._create_node(title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND, loaded_from_storage=True)
		self.assertEqual(DEFAULT_TITLE_COLOR_FOREGROUND, node.title_color_foreground)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title foreground color.
		node.title_color_foreground = '#c0c0c0'
		
		self.assertEqual('#c0c0c0', node.title_color_foreground)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_title_color_foreground_create_copy(self):
		node = self._create_node(title_color_foreground=DEFAULT_TITLE_COLOR_FOREGROUND, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.title_color_foreground, equal_to(node.title_color_foreground))
	
	def test_title_color_background_init_set_new(self):
		"""Tests setting the title background color of a new node."""
		node = self._create_node(title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND, loaded_from_storage=False)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title background color.
		node.title_color_background = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.title_color_background)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_title_color_background_init_set_from_storage(self):
		"""Tests setting the title background color of a node loaded from storage."""
		node = self._create_node(title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND, loaded_from_storage=True)
		self.assertEqual(DEFAULT_TITLE_COLOR_BACKGROUND, node.title_color_background)
		old_modified_time = node.modified_time
		sleep(1 * MS)

		# Change the node's title background color.
		node.title_color_background = 'icon_new.png'
		
		self.assertEqual('icon_new.png', node.title_color_background)
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_title_color_background_create_copy(self):
		node = self._create_node(title_color_background=DEFAULT_TITLE_COLOR_BACKGROUND, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.title_color_background, equal_to(node.title_color_background))
	
	def test_client_preferences_init_set_new(self):
		"""Tests setting the client preferences of a new node."""
		node = self._create_node(client_preferences=DEFAULT_CLIENT_PREFERENCES, loaded_from_storage=False)
		self.assertEqual(DEFAULT_CLIENT_PREFERENCES, node.client_preferences._data)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		# Change the node's client preferences.
		node.client_preferences.get('test', 'key', define=True)
		node.client_preferences.set('test', 'key', 'new value')
		
		self.assertEqual('new value', node.client_preferences.get('test', 'key'))
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_client_preferences_set_from_storage(self):
		"""Tests setting the client preferences of a node loaded from storage."""
		node = self._create_node(client_preferences=DEFAULT_CLIENT_PREFERENCES, loaded_from_storage=True)
		self.assertEqual(DEFAULT_CLIENT_PREFERENCES, node.client_preferences._data)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		# Change the node's client preferences.
		node.client_preferences.get('test', 'key', define=True)
		node.client_preferences.set('test', 'key', 'new value')

		self.assertEqual('new value', node.client_preferences.get('test', 'key'))
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
	
	def test_client_preferences_create_copy(self):
		node = self._create_node(client_preferences=DEFAULT_CLIENT_PREFERENCES, loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.client_preferences, equal_to(node.client_preferences))
		assert_that(copy.client_preferences, is_not(same_instance(node.client_preferences)))
	
	@unittest.skip("TODO: MIGRATE?")
	def test_save_new_with_dirty_parent(self):
		"""Tests saving a new node with a dirty parent."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = TestNotebookNode()
		parent.set_is_dirty(True)
		node = self._create_node(parent=parent, loaded_from_storage=False)
		
		with self.assertRaises(IllegalOperationError):
			# Save the node.
			node.save()
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.add_node.called)
		
		# Verify the node.
# 		self.assertEqual(True, node.is_dirty)
	
	def test_create_copy(self):
		node = self._create_node(notebook=Notebook(), loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy._notebook, is_(none()))
		assert_that(copy.node_id, is_not(equal_to(node.node_id)))
		assert_that(copy.parent, is_(none()))
		assert_that(copy.is_dirty, equal_to(True))
	
	def test_create_copy_with_subtree(self):
		node = self._create_node(parent=None, loaded_from_storage=False)
		child1_copy = TestNotebookNode()
		child1 = TestNotebookNode()
		child1.set_create_copy_result(child1_copy)
		child2_copy = TestNotebookNode()
		child2 = TestNotebookNode()
		child2.set_create_copy_result(child2_copy)
		node._add_unbound_node_as_child(child1)
		node._add_unbound_node_as_child(child2)
		
		copy = node.create_copy(with_subtree=True)
		
		assert_that(copy.children), contains(child1_copy, child2_copy)

	
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
	
	def test_title_set_if_deleted(self):
		parent = TestNotebookNode()
		node = self._create_node(parent=parent, title=DEFAULT_TITLE, loaded_from_storage=False)
		node.delete()
		
		with self.assertRaises(IllegalOperationError):
			node.title = 'new title'
		
		self.assertNotEquals('new title', node.title)
	
	def test_content_type_create_copy(self):
		node = self._create_node(loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.content_type, equal_to(node.content_type))
	
	def test_add_new_node_as_child(self):
		notebook = Notebook()
		node = self._create_node(notebook=notebook, loaded_from_storage=False)
		child = TestNotebookNode(notebook=None, parent=None)
		
		assert_that(node.can_add_new_node_as_child(), is_(True))
		
		node.add_new_node_as_child(child)
		
		assert_that(node.children, contains(child))
		assert_that(child._notebook, is_(same_instance(node._notebook)))
		assert_that(child.parent, is_(same_instance(node)))
	
	def test_add_new_node_as_child_child_notebook_not_none(self):
		notebook = Notebook()
		node = self._create_node(notebook=notebook, loaded_from_storage=False)
		child = TestNotebookNode(notebook=notebook, parent=None)
		
		with self.assertRaises(Exception):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(same_instance(notebook)))
		assert_that(child.parent, is_(none()))
	
	def test_add_new_node_as_child_child_parent_not_none(self):
		notebook = Notebook()
		node = self._create_node(notebook=notebook, loaded_from_storage=False)
		other_parent = TestNotebookNode()
		child = TestNotebookNode(parent=other_parent, add_to_parent=True)
		
		with self.assertRaises(Exception):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(same_instance(other_parent)))
	
	def test_add_new_node_as_child_child_deleted(self):
		notebook = Notebook()
		node = self._create_node(notebook=notebook, loaded_from_storage=False)
		child = TestNotebookNode()
		child.delete()
		
		with self.assertRaises(Exception):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(none()))
	
	def test_add_new_node_as_child_node_deleted(self):
		notebook = Notebook()
		parent = TestNotebookNode()
		node = self._create_node(notebook=notebook, parent=parent, loaded_from_storage=False)
		node.delete()
		child = TestNotebookNode()
		
		assert_that(node.can_add_new_node_as_child(), is_(False))
		
		with self.assertRaises(IllegalOperationError):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(none()))
	
	def test_add_new_node_as_child_node_in_trash_1(self):
		notebook = Notebook()
		parent = Mock(spec=NotebookNode)
		parent.is_trash = True
		parent.is_in_trash = False
		node = self._create_node(notebook=notebook, parent=parent, loaded_from_storage=False)
		child = TestNotebookNode(notebook=None, parent=None)
		
		assert_that(node.can_add_new_node_as_child(), is_(False))
		
		with self.assertRaises(IllegalOperationError):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(none()))
	
	def test_add_new_node_as_child_node_in_trash_2(self):
		notebook = Notebook()
		parent = Mock(spec=NotebookNode)
		parent.is_trash = False
		parent.is_in_trash = True
		node = self._create_node(notebook=notebook, parent=parent, loaded_from_storage=False)
		child = TestNotebookNode(notebook=None, parent=None)
		
		assert_that(node.can_add_new_node_as_child(), is_(False))
		
		with self.assertRaises(IllegalOperationError):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(none()))
	
	def test_delete_without_children(self):
		parent = TestNotebookNode()
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
		self.assertEqual(True, node.can_delete())
		
		node.delete()
		
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.is_deleted)
		self.assertEqual(False, node in parent.children)
		self.assertEqual(False, node in parent.get_children())
	
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

# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
		self.assertEqual(True, node in parent.children)
	
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
# 		self.assertEqual(True, node.is_dirty)
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
# 		self.assertEqual(False, node.is_dirty)
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
# 		self.assertEqual(False, node.is_dirty)
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
# 		self.assertEqual(False, node.is_dirty)
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
# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual([node], old_parent.children)
		self.assertEqual([], new_parent.children)
	
	@unittest.skip("TODO: MIGRATE?")
	def test_save_loaded_and_deleted_with_dirty_parent(self):
		"""Tests saving a loaded and deleted node with a dirty parent."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = TestNotebookNode()
		parent.set_is_dirty(True)
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		# Delete the node.
		node.delete()
		
		with self.assertRaises(IllegalOperationError):
			# Save the node.
			node.save()
		
		# Verify the storage.
		self.assertEqual(False, notebook_storage.add_node.called)
		
		# Verify the node.
# 		self.assertEqual(True, node.is_dirty)
	
	@unittest.skip("TODO: MIGRATE?")
	def test_save_loaded_and_deleted_with_deleted_parent(self):
		"""Tests saving a loaded and deleted node with a deleted parent."""
		
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = TestNotebookNode()
		parent.set_is_deleted(True)
		parent.set_is_dirty(True)
		node = self._create_node(parent=parent, loaded_from_storage=True)
		
		# Delete the node.
		node.delete()
		
		# Save the node.
		node.save()
	

class ContentNodeTest(unittest.TestCase, ContentFolderNodeTestBase):
	def _create_node(
			self,
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
			main_payload=DEFAULT,
			additional_payloads=DEFAULT,
			node_id=DEFAULT,
			created_time=DEFAULT,
			modified_time=DEFAULT,
			):
		
		if main_payload is DEFAULT:
			main_payload = TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA)
		if additional_payloads is DEFAULT:
			additional_payloads = [TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA)]
		
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
		
		node = ContentNode(
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
				)
		if parent is not None:
			parent._add_child_node(node)
		return node
	
	def test_create_c(self):
		parent = TestNotebookNode()
		
		node = ContentNode(
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
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA)],
				)
		
		self.assertEqual(DEFAULT_HTML_PAYLOAD_NAME, node.main_payload_name)
		self.assertEqual([DEFAULT_PNG_PAYLOAD_NAME], node.additional_payload_names)
		self.assertEqual(DEFAULT_HTML_PAYLOAD_DATA, node.payloads[DEFAULT_HTML_PAYLOAD_NAME].open(mode='r').read())
		self.assertEqual(DEFAULT_PNG_PAYLOAD_DATA, node.payloads[DEFAULT_PNG_PAYLOAD_NAME].open(mode='r').read())
		
	def test_constructor_parameters_c1(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			ContentNode(
					notebook=None,
					content_type=DEFAULT_CONTENT_TYPE,
					parent=None,
					loaded_from_storage=False,
					title=DEFAULT_TITLE,
					main_payload=None,  # Must be not None
					additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA)],
					node_id=None,
					)
	
	def test_constructor_parameters_c2(self):
		with self.assertRaises(IllegalArgumentCombinationError):
			ContentNode(
					notebook=None,
					content_type=DEFAULT_CONTENT_TYPE,
					parent=None,
					loaded_from_storage=False,
					title=DEFAULT_TITLE,
					main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
					additional_payloads=None,  # Must be not None
					node_id=None,
					)
	
	def test_add_additional_payload(self):
		node = ContentNode(
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[TestPayload(DEFAULT_JPG_PAYLOAD_NAME, DEFAULT_JPG_PAYLOAD_DATA)],
				)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		node.add_additional_payload(TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA))
		
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual([DEFAULT_JPG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_NAME], node.additional_payload_names)
		self.assertEqual(DEFAULT_PNG_PAYLOAD_DATA, node.payloads[DEFAULT_PNG_PAYLOAD_NAME].open('r').read())		
	
	@unittest.skip('TODO MIGRATE')
	def test_get_payload_from_storage(self):
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		node = ContentNode(
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
				return io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA)
			else:
				raise storage.PayloadDoesNotExistError
		notebook_storage.get_node_payload.side_effect = side_effect_get_node_payload
		
		self.assertEqual(DEFAULT_HTML_PAYLOAD_DATA, node.get_payload(DEFAULT_HTML_PAYLOAD_NAME))
		
	@unittest.skip('TODO MIGRATE')
	def test_get_payload_nonexistent(self):
		node = ContentNode(
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
	
	def test_remove_additional_payload(self):
		node = ContentNode(
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[],
				)
		old_modified_time = node.modified_time
		sleep(1 * MS)
		
		node.add_additional_payload(TestPayload(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA))
		node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		
# 		self.assertEqual(True, node.is_dirty)
		self.assertEqual(True, node.modified_time > old_modified_time)
		self.assertEqual([], node.additional_payload_names)
		with self.assertRaises(PayloadDoesNotExistError):
			node.get_payload(DEFAULT_PNG_PAYLOAD_NAME)
	
	def test_remove_additional_payload_nonexistent(self):
		node = ContentNode(
				notebook=None,
				node_id=DEFAULT_ID,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=True,
				title=DEFAULT_TITLE,
				main_payload=TestPayload(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[],
				)
		
		with self.assertRaises(PayloadDoesNotExistError):
			node.remove_additional_payload(DEFAULT_PNG_PAYLOAD_NAME)
		
# 		self.assertEqual(False, node.is_dirty)
	
	@unittest.skip('TODO: MIGRATE')
	def test_save_new(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		parent = Mock(spec=NotebookNode)
		parent.node_id = new_node_id()
		parent.is_dirty = False
		node = ContentNode(
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=parent,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA)],
				)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=DEFAULT_CONTENT_TYPE,
				attributes=node._notebook_storage_attributes,
				payloads=[
						(DEFAULT_HTML_PAYLOAD_NAME, FileMatcher(io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))),
						(DEFAULT_PNG_PAYLOAD_NAME, FileMatcher(io.BytesIO(DEFAULT_PNG_PAYLOAD_DATA)))
						]
				)
		
		# Verify the node.
# 		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node.called)
	
	@unittest.skip('TODO: MIGRATE')
	def test_save_new_root(self):
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and the parent.
		node = ContentNode(
				notebook=None,
				content_type=DEFAULT_CONTENT_TYPE,
				parent=None,
				loaded_from_storage=False,
				title=DEFAULT_TITLE,
				main_payload=(DEFAULT_HTML_PAYLOAD_NAME, DEFAULT_HTML_PAYLOAD_DATA),
				additional_payloads=[(DEFAULT_PNG_PAYLOAD_NAME, DEFAULT_PNG_PAYLOAD_DATA)],
				)
		
		# Save the node.
		node.save()
		
		# Verify the storage.
		notebook_storage.add_node.assert_called_once_with(
				node_id=node.node_id,
				content_type=DEFAULT_CONTENT_TYPE,
				attributes=node._notebook_storage_attributes,
				payloads=[
						(DEFAULT_HTML_PAYLOAD_NAME, FileMatcher(io.BytesIO(DEFAULT_HTML_PAYLOAD_DATA))),
						(DEFAULT_PNG_PAYLOAD_NAME, FileMatcher(io.BytesIO(DEFAULT_PNG_PAYLOAD_DATA)))
						]
				)
		
		# Verify the node.
# 		self.assertEqual(False, node.is_dirty)
		
		# Verify that saving the node again does nothing.
		notebook_storage.reset_mock()
		node._unsaved_changes.add(NotebookNode.DUMMY_CHANGE)
		node.save()
		self.assertEqual(False, notebook_storage.add_node.called)
	
	@unittest.skip('TODO: MIGRATE')
	def test_save_multiple_changes(self):
		"""Tests saving multiple changes at once."""
		# Create a mocked NotebookStorage.
		notebook_storage = Mock(spec=storage.NotebookStorage)
		
		# Create the node and parents.
		old_parent = TestNotebookNode()
		new_parent = TestNotebookNode()
		node = ContentNode(
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
# 		self.assertEqual(False, node.is_dirty)
		
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


class TrashNodeTest(unittest.TestCase, ContentFolderTrashNodeTestBase):
	def _create_node(
			self,
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
# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual(False, node.is_deleted)
	
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
# 		self.assertEqual(False, node.is_dirty)
		self.assertEqual([node], old_parent.children)
		self.assertEqual([], new_parent.children)
	
	# NEW COPYING ---
	
	def test_class_create_copy(self):
		node = self._create_node(loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy, instance_of(FolderNode))
	
	def test_content_type_create_copy(self):
		node = self._create_node(loaded_from_storage=False)
		
		copy = node.create_copy(with_subtree=False)
		
		assert_that(copy.content_type, equal_to(CONTENT_TYPE_FOLDER))
		
	def test_add_new_node_as_child(self):
		notebook = Notebook()
		node = self._create_node(notebook=notebook, loaded_from_storage=False)
		child = TestNotebookNode(notebook=None, parent=None)
		
		assert_that(node.can_add_new_node_as_child(), is_(False))
		
		with self.assertRaises(IllegalOperationError):
			node.add_new_node_as_child(child)
		
		assert_that(node.children, is_not(contains(child)))
		assert_that(child._notebook, is_(none()))
		assert_that(child.parent, is_(none()))
	

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
